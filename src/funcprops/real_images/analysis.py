"""Source-bound exact and partial images assembled from critical-value covers."""

from dataclasses import dataclass, replace
from functools import cmp_to_key

import sympy as sp

from ..analysis import (
    derivative_on_domain,
    value_enclosure,
    verify_real_identity,
    verify_value_enclosure,
)
from ..analytic_roots import CriticalValue, ImplicitRealRoot, critical_values_equal
from ..coverage_checker import check_coverage
from ..coverage_contract import CoverageProof
from ..domain_tracking import DomainRecord, track_domain
from ..enclosure_policy import EnclosurePolicy
from ..source_syntax import same_data
from .critical_values import (
    ImageSite,
    check_value_bounds,
    root_locations,
    site_value,
    value_bounds,
)
from .interior import (
    InteriorCriticalCover,
    InteriorRootCover,
    endpoint_value,
    interior_critical_cover,
    interior_derivative,
    range_cells,
    rational_interior_cover,
)

_ERRORS = (TypeError, ValueError, AttributeError, ArithmeticError, NotImplementedError)


def _parts(region):
    return (
        ()
        if region is sp.S.EmptySet
        else region.args
        if isinstance(region, sp.Union)
        else (region,)
    )


def _compare_sites(a, b):
    if critical_values_equal(a.value, b.value) is True or (
        type(a.value) is not CriticalValue
        and type(b.value) is not CriticalValue
        and verify_real_identity(a.value, b.value)
    ):
        return 0
    if a.value is -sp.oo or b.value is sp.oo:
        return -1
    if a.value is sp.oo or b.value is -sp.oo:
        return 1
    if type(a.value) is not CriticalValue and type(b.value) is not CriticalValue:
        difference = a.value - b.value
        if difference.is_negative is True:
            return -1
        if difference.is_positive is True:
            return 1
    if a.enclosure is None or b.enclosure is None:
        raise ValueError("unresolved value order")
    if a.enclosure.upper < b.enclosure.lower:
        return -1
    if b.enclosure.upper < a.enclosure.lower:
        return 1
    raise ValueError("unresolved value order")


@dataclass(frozen=True)
class CriticalValueCover:
    """Endpoint, critical and unresolved value sites on one continuous real cell.

    Search state is retained only for resumption. The root proof and the supplied
    value witnesses establish the mathematical claims independently of discovery.
    """

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    critical_cover: object = None
    sites: tuple = ()
    samples: tuple = ()
    search_state: object = None

    def verify(self):
        """Replay source regularity, exhaustive critical geometry and value binding."""
        try:
            return self._verify()
        except _ERRORS:
            return False

    def _verify(self):
        if (
            type(self) is not CriticalValueCover
            or type(self.sites) is not tuple
            or type(self.samples) is not tuple
        ):
            return False
        f, x, D = self.expression, self.variable, self.domain
        if (
            not isinstance(f, sp.Expr)
            or not isinstance(x, sp.Symbol)
            or f.free_symbols - {x}
            or f.has(sp.Float)
        ):
            return False
        if isinstance(D, sp.FiniteSet):
            source = track_domain(f, x, D)
            if not source.complete or source.effective != D:
                return False
            if self.critical_cover is not None or self.search_state is not None:
                return False
            points = tuple(sorted(D, key=sp.default_sort_key))
            expected = tuple(
                ImageSite(p, site_value(f, x, p), True, "point") for p in points
            )
            if len(expected) != len(self.sites):
                return False
            return (
                all(
                    _site_matches(a, b)
                    for a, b in zip(self.sites, expected, strict=True)
                )
                and not self.samples
            )
        if not isinstance(D, sp.Interval) or any(
            p.is_finite is not True for p in (D.start, D.end)
        ):
            return False
        interior = sp.Interval.open(D.start, D.end)
        derivative = derivative_on_domain(f, x, D.closure)
        if derivative is None:
            derivative = interior_derivative(f, x, interior)
        if derivative is None or len(self.sites) < 2:
            return False
        expected = (
            ImageSite(
                D.start,
                endpoint_value(f, x, D, True),
                not bool(D.left_open),
                "endpoint",
            ),
            ImageSite(
                D.end,
                endpoint_value(f, x, D, False),
                not bool(D.right_open),
                "endpoint",
            ),
        )
        if any(s.value is None for s in expected) or not all(
            _site_matches(a, b) for a, b in zip(self.sites[:2], expected, strict=True)
        ):
            return False
        rest = self.sites[2:]
        if verify_real_identity(derivative, 0):
            if (
                self.critical_cover is not None
                or self.search_state is not None
                or len(rest) != 1
            ):
                return False
            p = (D.start + D.end) / 2
            if not _site_matches(
                rest[0], ImageSite(p, site_value(f, x, p), True, "constant")
            ):
                return False
        else:
            proof = self.critical_cover
            interior = sp.Interval.open(D.start, D.end)
            if type(proof) in (InteriorCriticalCover, InteriorRootCover):
                valid_cover = (
                    same_data(
                        (proof.source, proof.expression, proof.variable, proof.domain),
                        (f, derivative, x, interior),
                    )
                    and proof.verify()
                )
            else:
                valid_cover = (
                    type(proof) is CoverageProof
                    and same_data(
                        (
                            proof.expression,
                            proof.variable,
                            proof.context.requested,
                            proof.context.effective,
                        ),
                        (derivative, x, interior, interior),
                    )
                    and check_coverage(proof).certified is True
                )
            if not valid_cover:
                return False
            if self.search_state is not None:
                from ..adaptive_roots import CoverageState

                if (
                    type(proof) is not CoverageProof
                    or type(self.search_state) is not CoverageState
                    or self.search_state.check().certified is not True
                    or not same_data(self.search_state.proof, proof)
                ):
                    return False
            if not proof.complete or (len(rest) == 1 and rest[0].kind == "unresolved"):
                if (
                    len(rest) != 1
                    or rest[0].kind != "unresolved"
                    or rest[0].point != D.closure
                    or rest[0].value is not None
                    or rest[0].attained is not False
                ):
                    return False
                if rest[0].enclosure is not None and not verify_value_enclosure(
                    rest[0].enclosure, f, x, D.closure
                ):
                    return False
            else:
                if len(rest) != proof.root_count:
                    return False
                supports = []
                for site in rest:
                    p = site.point
                    if type(p) is ImplicitRealRoot:
                        valid = (
                            p.verify()
                            and same_data(
                                p.function,
                                sp.Lambda(
                                    x,
                                    proof.equation
                                    if type(proof) is InteriorRootCover
                                    else derivative,
                                ),
                            )
                            and p.interval.is_subset(interior) is True
                        )
                        support = p.interval
                    else:
                        valid = (
                            isinstance(p, sp.Expr)
                            and not p.free_symbols
                            and not p.has(sp.Float)
                            and interior.contains(p) is sp.true
                            and verify_real_identity(derivative.subs(x, p), 0)
                        )
                        support = sp.FiniteSet(p)
                    if (
                        not valid
                        or site.kind != "critical"
                        or site.attained is not True
                        or not same_data(site.value, site_value(f, x, p))
                    ):
                        return False
                    if any(
                        sp.Intersection(support, old) is not sp.S.EmptySet
                        for old in supports
                    ):
                        return False
                    supports.append(support)
                    if site.enclosure is not None and not check_value_bounds(
                        site.value, site.enclosure
                    ):
                        return False
        for sample in self.samples:
            if (
                type(sample) is not ImageSite
                or D.contains(sample.point) is not sp.true
                or not _site_matches(
                    sample,
                    ImageSite(
                        sample.point, site_value(f, x, sample.point), True, "sample"
                    ),
                )
            ):
                return False
        return True


def _site_matches(actual, expected):
    return (
        type(actual) is ImageSite
        and same_data(
            (actual.point, actual.value, actual.attained, actual.kind),
            (expected.point, expected.value, expected.attained, expected.kind),
        )
        and (
            actual.enclosure is None
            or check_value_bounds(actual.value, actual.enclosure)
        )
    )


def _cell_condition(cell, value):
    """Express a continuous image without ordering its possible extremal sites."""
    if any(site.kind == "unresolved" for site in cell.sites):
        return None
    if isinstance(cell.domain, sp.FiniteSet):
        return sp.Or(*(sp.Eq(value, s.value) for s in cell.sites))
    lower = sp.Or(
        *(value >= s.value if s.attained else value > s.value for s in cell.sites)
    )
    upper = sp.Or(
        *(value <= s.value if s.attained else value < s.value for s in cell.sites)
    )
    return sp.And(lower, upper)


def _cell_images(cell):
    """Derive exact images or justified inner/outer intervals from stored sites."""
    if isinstance(cell.domain, sp.FiniteSet):
        image = sp.FiniteSet(*(s.value for s in cell.sites))
        return image, image, image, sp.S.EmptySet
    unresolved = any(s.kind == "unresolved" for s in cell.sites)
    if not unresolved:
        try:
            ordered = sorted(cell.sites, key=cmp_to_key(_compare_sites))
            lo, hi = ordered[0], ordered[-1]
            ownedlo = any(s.attained and _compare_sites(s, lo) == 0 for s in cell.sites)
            ownedhi = any(s.attained and _compare_sites(s, hi) == 0 for s in cell.sites)
            image = sp.Interval(lo.value, hi.value, not ownedlo, not ownedhi)
            return image, image, image, sp.S.EmptySet
        except ValueError:
            value = sp.Symbol("_range_output", real=True)
            image = sp.ConditionSet(value, _cell_condition(cell, value), sp.S.Reals)
            return image, image, image, sp.S.EmptySet
    bounds = [s.enclosure for s in cell.sites]
    outer = (
        sp.Interval(min(b.lower for b in bounds), max(b.upper for b in bounds))
        if bounds and all(b is not None for b in bounds)
        else sp.S.Reals
    )
    owned = [
        s.enclosure
        for s in (*cell.sites, *cell.samples)
        if s.attained and s.enclosure is not None
    ]
    inner = sp.S.EmptySet
    if owned:
        lo = min(b.upper for b in owned)
        hi = max(b.lower for b in owned)
        if lo <= hi:
            inner = sp.Interval(lo, hi)
    return None, inner, outer, cell.domain


@dataclass(frozen=True)
class RangeAnalysis:
    """An exact image or source-bound partial inner/outer range information.

    certified=False is the default. Exactness, critical-root coverage and replay
    are distinct: a partial image can have valid enclosure evidence. Requested
    per-cell work is controlled by EnclosurePolicy; unsupported cells remain unresolved.
    """

    expression: sp.Expr
    variable: sp.Symbol
    requested: object
    domain_record: object
    cells: tuple = ()
    image: object = None
    inner: sp.Set = sp.S.EmptySet
    outer: sp.Set = sp.S.Reals
    unresolved: sp.Set = sp.S.Reals
    reason: object = None
    certified: bool = False
    transfer: object = None

    @property
    def complete(self):
        """Completion status for this record's stated scope; replay validity is separate."""
        return self.image is not None and self.unresolved is sp.S.EmptySet

    @property
    def critical_coverage_complete(self):
        """Whether every interval's derivative-zero geometry is exhaustive."""
        if self.transfer is not None:
            from .transfers import PeriodicImage, TailImage

            if type(self.transfer) is PeriodicImage:
                return self.transfer.analysis.critical_coverage_complete
            if type(self.transfer) is TailImage:
                return self.transfer.core.critical_coverage_complete
            return False
        return all(
            c.critical_cover is None or c.critical_cover.complete for c in self.cells
        ) and bool(self.cells or self.domain_record.effective is sp.S.EmptySet)

    @property
    def value_coverage_complete(self):
        """Whether extremal values have exact images or outward value bounds."""
        if self.transfer is not None:
            return self.complete
        return all(
            all(
                s.enclosure is not None
                or (isinstance(s.value, sp.Expr) and s.value.is_extended_real is True)
                for s in c.sites
            )
            for c in self.cells
        ) and bool(self.cells or self.domain_record.effective is sp.S.EmptySet)

    @property
    def range_kind(self):
        """Whether the result represents an exact image or an enclosure."""
        return "exact_image" if self.complete else "range_enclosure"

    @property
    def scope(self):
        """Scope identifier: ``real-image-on-effective-source-domain``."""
        return "real-image-on-effective-source-domain"

    def as_condition(self, value):
        """Return exact output membership, or None when image coverage is partial.

        A complete condition need not have a canonical interval presentation or
        a decided ordering of every implicit critical value.
        """
        value = sp.sympify(value)
        if not isinstance(value, sp.Symbol) or value.is_real is False:
            raise ValueError("value must be a real output Symbol")
        if not self.complete:
            return None
        from ..real_analysis.common import set_to_condition

        return set_to_condition(self.image, value)

    def verify(self):
        """Replay the supplied domain, value covers and summary without root search."""
        try:
            if (
                type(self) is not RangeAnalysis
                or type(self.certified) is not bool
                or type(self.domain_record) is not DomainRecord
                or not same_data(
                    (
                        self.domain_record.expression,
                        self.domain_record.variable,
                        self.domain_record.requested,
                    ),
                    (self.expression, self.variable, self.requested),
                )
                or not self.domain_record.verify()
            ):
                return False
            if self.transfer is not None:
                from .transfers import verify_transfer

                return verify_transfer(self)
            if not self.cells and self.reason is not None:
                return same_data(
                    (self.image, self.inner, self.outer, self.unresolved),
                    (None, sp.S.EmptySet, sp.S.Reals, self.domain_record.effective),
                )
            expected = range_cells(
                self.expression, self.variable, self.domain_record.effective
            )
            if (
                type(self.cells) is not tuple
                or expected is None
                or not same_data(
                    tuple((c.expression, c.domain) for c in self.cells), expected
                )
                or not all(
                    type(c) is CriticalValueCover and c.verify() for c in self.cells
                )
            ):
                return False
            return same_data(
                (self.image, self.inner, self.outer, self.unresolved),
                _assemble(self.cells),
            )
        except _ERRORS:
            return False


def _assemble(cells):
    images = [_cell_images(c) for c in cells]
    image = (
        sp.Union(*(a[0] for a in images))
        if all(a[0] is not None for a in images)
        else None
    )
    return (
        image,
        sp.Union(*(a[1] for a in images)),
        sp.Union(*(a[2] for a in images)),
        sp.Union(*(a[3] for a in images)),
    )


def _build_cell(f, x, D, policy, previous=None):
    from ..adaptive_roots import adaptive_root_coverage, resume_root_coverage

    if isinstance(D, sp.FiniteSet):
        sites = tuple(
            ImageSite(p, site_value(f, x, p), True, "point")
            for p in sorted(D, key=sp.default_sort_key)
        )
        return CriticalValueCover(f, x, D, sites=sites)
    if not isinstance(D, sp.Interval) or any(
        p.is_finite is not True for p in (D.start, D.end)
    ):
        return None
    interior = sp.Interval.open(D.start, D.end)
    derivative = derivative_on_domain(f, x, D.closure)
    native = derivative is not None
    if derivative is None:
        derivative = interior_derivative(f, x, interior)
    if (
        derivative is None
        or endpoint_value(f, x, D, True) is None
        or endpoint_value(f, x, D, False) is None
    ):
        return None
    sites = [
        ImageSite(
            D.start, endpoint_value(f, x, D, True), not bool(D.left_open), "endpoint"
        ),
        ImageSite(
            D.end, endpoint_value(f, x, D, False), not bool(D.right_open), "endpoint"
        ),
    ]
    cover, state = None, None
    if verify_real_identity(derivative, 0):
        p = (D.start + D.end) / 2
        sites.append(ImageSite(p, site_value(f, x, p), True, "constant"))
    else:
        interior = sp.Interval.open(D.start, D.end)
        if not native:
            cover = interior_critical_cover(f, derivative, x, interior)
            if not cover.complete:
                native_cover = rational_interior_cover(
                    f, derivative, x, interior, policy
                )
                if native_cover is not None:
                    cover = native_cover
            points = cover.roots
        else:
            if previous is not None and previous.search_state is not None:
                result = resume_root_coverage(previous.search_state, policy=policy)
            else:
                result = adaptive_root_coverage(derivative, x, interior, policy=policy)
            cover, state = result.proof, result.state
            points = root_locations(cover, derivative, x)
        if points is None:
            sites.append(
                ImageSite(
                    D.closure,
                    None,
                    False,
                    "unresolved",
                    value_enclosure(f, x, D.closure, precision=policy.precision)
                    if policy.max_cells
                    else None,
                )
            )
        else:
            sites.extend(
                ImageSite(p, site_value(f, x, p), True, "critical") for p in points
            )
    enriched = []
    for site in sites:
        if site.value is not None and policy.max_cells:
            site = replace(site, enclosure=value_bounds(site.value, policy.precision))
        enriched.append(site)
    midpoint = (D.start + D.end) / 2
    sample = ImageSite(midpoint, site_value(f, x, midpoint), True, "sample")
    if policy.max_cells:
        sample = replace(sample, enclosure=value_bounds(sample.value, policy.precision))
    return CriticalValueCover(f, x, D, cover, tuple(enriched), (sample,), state)


def analyze_range(
    expression,
    variable,
    domain=sp.S.Reals,
    *,
    policy=None,
    certified=False,
    tail_facts=(),
    _previous=None,
    _transfers=True,
):
    """Assemble exact implicit ranges or partial image bounds on real source cells.

    Interval cells use checked C1 closure extensions or exact real interior
    regularity with one-sided limits. Complete critical geometry can return an
    exact ConditionSet when value order is unresolved. Root evidence is reused
    by refine_range; supported periods and tail bounds extend unbounded queries.
    tail_facts accepts source-bound TailValueBound records from other providers.
    """
    if type(certified) is not bool:
        raise TypeError("certified must be a boolean")
    policy = EnclosurePolicy() if policy is None else policy
    if type(policy) is not EnclosurePolicy:
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from ..work_budget import bounded_query

        return bounded_query(
            "analyze_range",
            expression,
            (variable, domain),
            {
                "policy": replace(policy, seconds=None),
                "certified": certified,
                "tail_facts": tail_facts,
            },
            policy.seconds,
        )
    from .tails import FiniteTailBound, TailValueBound

    if type(tail_facts) is not tuple or any(
        type(t) not in (TailValueBound, FiniteTailBound) or not t.verify()
        for t in tail_facts
    ):
        raise ValueError("tail_facts must contain checked TailValueBound records")
    f, x = sp.sympify(expression), sp.sympify(variable)
    if any(t.expression != f or t.variable != x for t in tail_facts):
        raise ValueError("tail facts must match the source expression and coordinate")
    if not isinstance(x, sp.Symbol) or x.is_real is False:
        raise ValueError("variable must be a real coordinate Symbol")
    record = track_domain(f, x, domain)
    seed = RangeAnalysis(
        f,
        x,
        record.requested,
        record,
        unresolved=record.effective if record.complete else sp.S.Reals,
    )
    if not record.complete or f.free_symbols - {x} or f.has(sp.Float):
        return replace(seed, reason=record.reason or "fixed-exact-source-required")
    if _transfers:
        from .transfers import propose_transfer

        transfer = propose_transfer(
            seed,
            policy,
            _previous.transfer if _previous is not None else None,
            tail_facts,
        )
        if transfer is not None:
            return replace(transfer, certified=certified and transfer.verify())
    from ..real_analysis.domain import (
        _has_complex_intermediates,
        _real_formula_on_domain,
    )

    if (
        _has_complex_intermediates(f, x)
        and _real_formula_on_domain(f, x, record.effective) is None
    ):
        return replace(seed, reason="unresolved-real-source-formula")
    cells = range_cells(f, x, record.effective)
    if cells is None:
        return replace(seed, reason="unsupported-domain-geometry")
    built = []
    for i, (g, D) in enumerate(cells):
        previous = (
            _previous.cells[i]
            if _previous is not None and i < len(_previous.cells)
            else None
        )
        cell = _build_cell(g, x, D, policy, previous)
        if cell is None:
            return replace(seed, reason="unsupported-closure-regularity")
        built.append(cell)
    result = replace(seed, cells=tuple(built), reason=None)
    image, inner, outer, unresolved = _assemble(result.cells)
    result = replace(
        result,
        image=image,
        inner=inner,
        outer=outer,
        unresolved=unresolved,
        reason=None if image is not None else "unresolved-critical-values-or-order",
    )
    return replace(result, certified=certified and result.verify())


def refine_range(result, *, policy=None, certified=False):
    """Resume valid critical-root covers and refine their value enclosures."""
    from .tails import BoundedTailImage

    if type(result) is not RangeAnalysis or not result.verify():
        raise ValueError("result must have valid source-bound range evidence")
    return analyze_range(
        result.expression,
        result.variable,
        result.requested,
        policy=policy,
        certified=certified,
        _previous=result,
        tail_facts=result.transfer.tails
        if type(result.transfer) is BoundedTailImage
        else (),
    )
