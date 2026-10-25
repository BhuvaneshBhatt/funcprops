"""Selected exact complex multiplicities; unknown clusters stay unknown.

An exact Taylor order plus the enclosing contour total proves one located
multiple zero. A power of a simple counted factor times a nonvanishing unit
proves one zero of the corresponding multiplicity without guessing its center.
"""

from dataclasses import dataclass, replace

import sympy as sp

from .analytic_contours import (
    ComplexBoxWitness,
    _clear,
    _header,
    certify_analytic_contour,
)
from .complex_coverage import CoverageRectangle
from .complex_interval import (
    complex_box_evaluate,
    complex_box_taylor,
    entire_source,
    valid_box,
    valid_taylor_coefficients,
)
from .complex_newton import _ERRORS, _midpoint, _point, _valid_region
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy
from .source_syntax import differentiate

_ERRORS = (*_ERRORS, sp.PolynomialError)


def _point_inside(center, rectangle, strict=True):
    a, b, c, d = rectangle.bounds()
    x, y = sp.re(center), sp.im(center)
    return a < x < c and b < y < d if strict else a <= x <= c and b <= y <= d


def _unit_structure(f, z):
    if isinstance(f, sp.Rational) or f in (sp.I, sp.pi, sp.E):
        return f != 0
    if f.func is sp.exp:
        return entire_source(f.args[0], z)
    if f.is_Mul:
        return all(_unit_structure(a, z) for a in f.args)
    if f.is_Pow and isinstance(f.exp, sp.Integer) and f.exp >= 0:
        return entire_source(f.base, z) and (f.exp == 0 or _unit_structure(f.base, z))
    return False


@dataclass(frozen=True)
class ComplexTaylorWitness:
    """Enclose exact Taylor coefficients at a specified complex point."""

    expression: sp.Expr
    variable: sp.Symbol
    center: sp.Expr
    order: int
    coefficients: tuple
    precision: int
    max_series_terms: int = 4096
    schema_version: int = 1

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return (
                type(self) is ComplexTaylorWitness
                and type(self.schema_version) is int
                and self.schema_version == 1
                and isinstance(self.center, sp.Expr)
                and not self.center.has(sp.Float)
                and not self.center.free_symbols
                and valid_box(_point(self.center))
                and valid_taylor_coefficients(self.coefficients, self.order)
                and self.coefficients
                == complex_box_taylor(
                    self.expression,
                    self.variable,
                    _point(self.center),
                    self.order,
                    precision=self.precision,
                    max_series_terms=self.max_series_terms,
                )
            )
        except _ERRORS:
            return False

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "entire-complex-normalized-Taylor-enclosure"


@dataclass(frozen=True)
class ComplexUnitWitness:
    """Prove a complex analytic factor nonzero throughout a rectangle."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    enclosure: ComplexBoxWitness | None = None
    schema_version: int = 1

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self) is not ComplexUnitWitness
                or not _header(self)
                or type(self.rectangle) is not CoverageRectangle
                or not entire_source(self.expression, self.variable)
            ):
                return False
            if self.enclosure is None:
                return _unit_structure(self.expression, self.variable)
            w = self.enclosure
            return (
                type(w) is ComplexBoxWitness
                and w.expression == self.expression
                and w.variable == self.variable
                and w.box == self.rectangle.bounds()
                and w.verify()
                and _clear(w.bounds)
            )
        except _ERRORS:
            return False

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "entire-nonvanishing-unit-on-closed-rectangle"


class _CountRecord:
    @property
    def complete(self):
        return True

    @property
    def multiplicity_count(self):
        return self.zero_count

    @property
    def root_count(self):
        return self.known_distinct

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        try:
            valid = _valid_region(self, self.expression, self.variable, {})
        except _ERRORS:
            valid = False
        return CheckResult(
            CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
            valid,
            valid,
            None if valid else "false-complex-multiplicity-premise",
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class ComplexExactMultiplicity(_CountRecord):
    """Prove an exact root location and multiplicity from Taylor data."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    parent: object
    center: sp.Expr
    multiplicity: int
    jets: tuple
    taylor: ComplexTaylorWitness
    schema_version: int = 1

    @property
    def zero_count(self):
        return self.multiplicity

    @property
    def known_distinct(self):
        return 1

    @property
    def scope(self):
        return "exact-complex-order-and-exhaustive-local-count"


@dataclass(frozen=True)
class ComplexLocatedRegion(_CountRecord):
    """Transfer a counted region using an exact certified root location."""

    parent: object
    rectangle: CoverageRectangle
    schema_version: int = 1

    @property
    def expression(self):
        return self.parent.expression

    @property
    def variable(self):
        return self.parent.variable

    @property
    def center(self):
        return self.parent.center

    @property
    def zero_count(self):
        if _point_inside(self.center, self.rectangle):
            return self.parent.zero_count
        return None if _point_inside(self.center, self.rectangle, False) else 0

    @property
    def known_distinct(self):
        return 1 if self.zero_count else 0

    @property
    def scope(self):
        return "located-complex-root-subset-count"


@dataclass(frozen=True)
class ComplexPowerFactorProof(_CountRecord):
    """Relate complex zero orders to a power and an analytic unit."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    parent: object
    base: sp.Expr
    multiplicity: int
    unit: sp.Expr
    unit_witness: ComplexUnitWitness
    base_parent: object
    schema_version: int = 1

    @property
    def zero_count(self):
        return self.multiplicity

    @property
    def known_distinct(self):
        return 1

    @property
    def scope(self):
        return "simple-entire-factor-times-unit-multiplicity"

    @property
    def root_region(self):
        return ComplexPowerRootRegion(self, self.base_parent)


@dataclass(frozen=True)
class ComplexPowerRootRegion(_CountRecord):
    """Isolate one multiple zero through its checked power-factor base."""

    factorization: ComplexPowerFactorProof
    base_region: object
    schema_version: int = 1

    @property
    def expression(self):
        return self.factorization.expression

    @property
    def variable(self):
        return self.factorization.variable

    @property
    def rectangle(self):
        return self.base_region.rectangle

    @property
    def zero_count(self):
        return self.factorization.multiplicity * self.base_region.zero_count

    @property
    def known_distinct(self):
        return self.base_region.zero_count

    @property
    def scope(self):
        return "power-factor-transferred-region-count"


def _valid_multiple(c, memo):
    """Check exact complex root order from vanishing jets and nonzero leading data."""

    key = id(c)
    if key in memo:
        return memo[key]
    memo[key] = False
    try:
        if type(c.schema_version) is not int or c.schema_version != 1:
            return False
        if type(c) is ComplexExactMultiplicity:
            f, z, m = c.expression, c.variable, c.multiplicity
            if (
                not _header(c)
                or type(c.rectangle) is not CoverageRectangle
                or not entire_source(f, z)
                or type(m) is not int
                or m < 2
                or not isinstance(c.center, sp.Expr)
                or c.center.has(sp.Float)
                or c.center.free_symbols
                or not valid_box(_point(c.center))
                or not _point_inside(c.center, c.rectangle)
                or not isinstance(c.jets, tuple)
                or len(c.jets) != m
            ):
                return False
            if (
                not _valid_region(c.parent, f, z, memo)
                or c.parent.zero_count != m
                or c.parent.rectangle != c.rectangle
            ):
                return False
            expected = tuple(differentiate(f, z, k).subs(z, c.center) for k in range(m))
            if c.jets != expected or any(v != 0 for v in expected):
                return False
            t = c.taylor
            valid = (
                type(t) is ComplexTaylorWitness
                and t.expression == f
                and t.variable == z
                and t.center == c.center
                and type(t.order) is int
                and t.order == m
                and t.verify()
                and _clear(t.coefficients[m])
            )
        elif type(c) is ComplexLocatedRegion:
            if (
                type(c.parent) not in (ComplexExactMultiplicity, ComplexLocatedRegion)
                or type(c.rectangle) is not CoverageRectangle
                or not c.rectangle.valid()
            ):
                return False
            valid = (
                _valid_region(c.parent, c.expression, c.variable, memo)
                and c.parent.known_distinct == 1
                and c.parent.rectangle.contains_rectangle(c.rectangle)
                and c.zero_count is not None
            )
        elif type(c) is ComplexPowerFactorProof:
            f, z, m = c.expression, c.variable, c.multiplicity
            if (
                not _header(c)
                or type(c.rectangle) is not CoverageRectangle
                or not entire_source(f, z)
                or type(m) is not int
                or m < 2
                or not entire_source(c.base, z)
                or not entire_source(c.unit, z)
                or c.base.free_symbols - {z}
                or c.unit.free_symbols - {z}
                or c.base.has(sp.Float)
                or c.unit.has(sp.Float)
            ):
                return False
            w = c.unit_witness
            valid = (
                _valid_region(c.parent, f, z, memo)
                and c.parent.zero_count == m
                and c.parent.rectangle == c.rectangle
                and _valid_region(c.base_parent, c.base, z, memo)
                and c.base_parent.zero_count == 1
                and c.base_parent.rectangle == c.rectangle
                and type(w) is ComplexUnitWitness
                and w.expression == c.unit
                and w.variable == z
                and w.rectangle == c.rectangle
                and w.verify()
                and sp.expand(f - c.unit * c.base**m) == 0
            )
        elif type(c) is ComplexPowerRootRegion:
            p = c.factorization
            if type(p) is not ComplexPowerFactorProof:
                return False
            valid = (
                _valid_multiple(p, memo)
                and _valid_region(c.base_region, p.base, p.variable, memo)
                and c.base_region.zero_count in (0, 1)
                and p.rectangle.contains_rectangle(c.rectangle)
            )
        else:
            valid = False
        memo[key] = bool(valid)
        return bool(valid)
    except _ERRORS:
        return False


def _unit_witness(f, z, rectangle, policy):
    used = 0
    if _unit_structure(f, z):
        c = ComplexUnitWitness(
            f, z, rectangle, sp.srepr(f), tuple(sorted(z.assumptions0.items()))
        )
        return (c if c.verify() else None), used
    for precision in policy.precisions:
        if used >= policy.max_cells:
            break
        used += 1
        bounds = complex_box_evaluate(
            f,
            z,
            rectangle.bounds(),
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        if bounds is None or not _clear(bounds):
            continue
        w = ComplexBoxWitness(
            f, z, rectangle.bounds(), bounds, precision, policy.max_series_terms
        )
        c = ComplexUnitWitness(
            f, z, rectangle, sp.srepr(f), tuple(sorted(z.assumptions0.items())), w
        )
        if c.verify():
            return c, used
    return None, used


def _propose_multiple_impl(parent, policy, center=None):
    """Search bounded exact-location and power-factor candidates, accepting only checked orders."""

    used = 0
    f, z, m = parent.expression, parent.variable, parent.zero_count
    if type(m) is not int or m < 2 or sp.count_ops(f) > 512:
        return None, used
    if center is None and policy.max_cells:
        used += 1
        factored = sp.Mul.make_args(sp.factor(f))
        for factor in factored:
            base, power = factor.as_base_exp()
            if not isinstance(power, sp.Integer) or power != m:
                continue
            unit = sp.Mul(*(v for v in factored if v != factor))
            if not entire_source(base, z) or not entire_source(unit, z):
                continue
            unit_proof, spent = _unit_witness(
                unit,
                z,
                parent.rectangle,
                replace(policy, max_cells=policy.max_cells - used),
            )
            used += spent
            if unit_proof is None or used >= policy.max_cells:
                continue
            p = certify_analytic_contour(
                base,
                z,
                parent.rectangle.lower_left,
                parent.rectangle.upper_right,
                policy=replace(policy, max_cells=policy.max_cells - used, seconds=None),
            )
            used += p.tested
            if not p.complete or p.zero_count != 1:
                continue
            proof = ComplexPowerFactorProof(
                f,
                z,
                parent.rectangle,
                sp.srepr(f),
                tuple(sorted(z.assumptions0.items())),
                parent,
                base,
                m,
                unit,
                unit_proof,
                p,
            )
            if proof.verify():
                return proof.root_region, used
    if m > policy.max_taylor_order + 1:
        return None, used
    centers = (
        (sp.S.Zero, _midpoint(parent.rectangle.bounds()))
        if center is None
        else (sp.sympify(center),)
    )
    for point in dict.fromkeys(centers):
        if used >= policy.max_cells:
            break
        used += 1
        if (
            not isinstance(point, sp.Expr)
            or point.has(sp.Float)
            or point.free_symbols
            or not valid_box(_point(point))
            or not _point_inside(point, parent.rectangle)
        ):
            continue
        jets = tuple(differentiate(f, z, k).subs(z, point) for k in range(m))
        if any(v != 0 for v in jets):
            continue
        for precision in policy.precisions:
            if used >= policy.max_cells:
                break
            used += 1
            coefficients = complex_box_taylor(
                f,
                z,
                _point(point),
                m,
                precision=precision,
                max_series_terms=policy.max_series_terms,
            )
            if coefficients is None or not _clear(coefficients[m]):
                continue
            witness = ComplexTaylorWitness(
                f, z, point, m, coefficients, precision, policy.max_series_terms
            )
            c = ComplexExactMultiplicity(
                f,
                z,
                parent.rectangle,
                sp.srepr(f),
                tuple(sorted(z.assumptions0.items())),
                parent,
                point,
                m,
                jets,
                witness,
            )
            if c.verify():
                return c, used
    return None, used


def _propose_multiple(parent, policy, center=None):
    try:
        return _propose_multiple_impl(parent, policy, center)
    except _ERRORS:
        # A failed heuristic must not disable contour completeness. Conservatively
        # charge its entire finite allowance before returning to the fallback.
        return None, policy.max_cells


def certify_complex_multiple_root(parent, *, center=None, policy=None):
    """Prove one selected multiple zero, or return None with no guessed order."""
    parent = getattr(parent, "certificate", parent)
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_complex_multiple_root",
            parent,
            (),
            {"center": center, "policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    try:
        if not _valid_region(parent, parent.expression, parent.variable, {}):
            return None
        return _propose_multiple(parent, policy, center)[0]
    except _ERRORS:
        return None
