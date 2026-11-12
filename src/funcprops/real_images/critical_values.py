"""Shared source-bound critical values for range and optimization consumers."""

from dataclasses import dataclass

import sympy as sp

from ..analytic_roots import (
    CriticalValue,
    ImplicitRealRoot,
    _explicit_location,
    check_root_evidence,
    root_region,
)
from ..coverage_contract import CoverageLeaf, CoverageProof, EnclosureWitness
from ..source_syntax import same_data


@dataclass(frozen=True)
class CriticalValueEnclosure:
    """Outward bounds at an implicit root, with independently replayable premises."""

    value: CriticalValue
    root_cover: CoverageLeaf | CoverageProof
    enclosure: EnclosureWitness

    @property
    def expression(self):
        """Expression to which the stored evidence applies."""
        return self.value.function.expr

    @property
    def variable(self):
        """Coordinate used by the source and its evidence."""
        return self.value.function.variables[0]

    @property
    def lower(self):
        """Lower endpoint of the outward value bound."""
        return self.enclosure.lower

    @property
    def upper(self):
        """Upper endpoint of the outward value bound."""
        return self.enclosure.upper

    def verify(self):
        """Check root uniqueness, bracket inclusion and the bound formula."""
        from ..analysis import verify_value_enclosure

        if (
            type(self) is not CriticalValueEnclosure
            or type(self.value) is not CriticalValue
            or type(self.enclosure) is not EnclosureWitness
        ):
            return False
        p = self.root_cover
        r = self.value.root
        return (
            r.verify()
            and check_root_evidence(p, r.function)
            and root_region(p).is_subset(r.interval) is True
            and verify_value_enclosure(
                self.enclosure,
                self.value.function.expr,
                self.value.function.variables[0],
                root_region(p).closure,
            )
        )


@dataclass(frozen=True)
class ImageSite:
    """An endpoint, owned point or implicit critical value on a source cell."""

    point: object
    value: object
    attained: bool
    kind: str
    enclosure: object = None


def value_bounds(value, precision=30):
    """Build outward evidence for an explicit or implicit finite real value."""
    from ..analysis import value_enclosure

    if type(value) is CriticalValue:
        return value.enclosure(precision)
    return value_enclosure(
        sp.sympify(value),
        sp.Symbol("_image_value", real=True),
        sp.FiniteSet(0),
        precision=precision,
    )


def check_value_bounds(value, evidence):
    """Bind a value witness to its exact expression, including implicit roots."""
    from ..analysis import verify_value_enclosure

    if type(value) is CriticalValue:
        return (
            type(evidence) is CriticalValueEnclosure
            and same_data(evidence.value, value)
            and evidence.verify()
        )
    return type(evidence) is EnclosureWitness and verify_value_enclosure(
        evidence,
        sp.sympify(value),
        sp.Symbol("_image_value", real=True),
        sp.FiniteSet(0),
    )


def site_value(function, variable, point):
    """Evaluate an explicit point or retain an exact implicit value."""
    if type(point) is ImplicitRealRoot:
        return CriticalValue(sp.Lambda(variable, function), point)
    return sp.simplify(function.subs(variable, point))


def root_locations(cover, function, variable):
    """Extract explicit or checked implicit locations from an exhaustive cover."""
    if (
        type(cover) is not CoverageProof
        or not cover.complete
        or not same_data((cover.expression, cover.variable), (function, variable))
        or not cover.verify()
    ):
        return None
    result = []
    for leaf in cover.leaves:
        if leaf.root_count == 0:
            continue
        exact = _explicit_location(leaf)
        if exact is not None:
            result.append(exact)
            continue
        if leaf.roots and len(leaf.roots) == leaf.root_count:
            result.extend(point for point, _ in leaf.roots)
        elif (
            leaf.root_count == 1
            and isinstance(leaf.region, sp.FiniteSet)
            and len(leaf.region) == 1
        ):
            result.append(next(iter(leaf.region)))
        elif leaf.root_count == 1 and isinstance(leaf.region, sp.Interval):
            try:
                root = ImplicitRealRoot.from_cover(leaf)
                region = root.enclosure(2)
                result.append(
                    next(iter(region)) if isinstance(region, sp.FiniteSet) else root
                )
            except ValueError:
                return None
        else:
            return None
    return tuple(result) if len(result) == cover.root_count else None


def critical_value_regions(f, x, D, cover):
    """Return endpoint, critical and unresolved value regions for a finite cell.

    The supplied derivative cover must match the cell interior exactly. The
    returned regions contain every possible extremum; they do not select an
    optimum or claim that an endpoint limit is attained.
    """
    from ..analysis import derivative_on_domain as derivative_formula_on_cell
    from ..coverage_checker import check_coverage
    from ..coverage_contract import CoverageProof
    from ..source_syntax import normalize_arithmetic

    if isinstance(D, sp.FiniteSet):
        if cover is not None:
            raise ValueError("point-cover-not-needed")
        return tuple(
            (sp.FiniteSet(p), "point") for p in sorted(D, key=sp.default_sort_key)
        )
    if not isinstance(D, sp.Interval) or not all(
        p.is_finite is True for p in (D.start, D.end)
    ):
        raise ValueError("finite-components-required")
    derivative = derivative_formula_on_cell(normalize_arithmetic(f), x, D.closure, 1)
    if derivative is None:
        raise ValueError("C1-closure-required")
    if derivative == 0:
        if cover is not None:
            raise ValueError("constant-cover-not-needed")
        return ((sp.FiniteSet((D.start + D.end) / 2), "constant"),)
    endpoints = ((sp.FiniteSet(D.start), "limit"), (sp.FiniteSet(D.end), "limit"))
    if cover is None:
        return (*endpoints, (D.closure, "unresolved"))
    interior = sp.Interval.open(D.start, D.end)
    if (
        type(cover) is not CoverageProof
        or cover.expression != derivative
        or cover.variable != x
        or cover.context.requested != interior
        or cover.context.effective != interior
        or cover.context.substitutions
        or cover.context.parameter_guard is not sp.S.true
        or cover.context.branch_context is not None
        or check_coverage(cover).certified is not True
    ):
        raise ValueError("critical-cover-mismatch")
    return (
        endpoints
        + tuple(
            (r.closure if isinstance(r, sp.Interval) else r, "critical")
            for leaf in cover.leaves
            if leaf.root_count != 0
            for r in (
                tuple(sp.FiniteSet(point) for point, _ in leaf.roots)
                if leaf.roots and len(leaf.roots) == leaf.root_count
                else _parts(leaf.region)
            )
        )
        + tuple(
            (r.closure if isinstance(r, sp.Interval) else r, "unresolved")
            for r in _parts(cover.unresolved)
        )
    )


def _parts(region):
    if region is sp.S.EmptySet:
        return ()
    if isinstance(region, sp.Union):
        return tuple(p for r in region.args for p in _parts(r))
    return (region,)
