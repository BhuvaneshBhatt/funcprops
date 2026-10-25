"""Checked scalar complex Krawczyk contraction and root-count transfer.

The parent already has a certified count of one. A contraction image strictly
inside a rational child retains its root and proves four complement strips
root-free, including their new shared boundaries. Replay never proposes boxes.
"""

from dataclasses import dataclass, replace

import sympy as sp

from .analytic_contours import (
    AnalyticContourCertificate,
    ComplexBoxWitness,
    _header,
    check_analytic_contour,
)
from .complex_coverage import CoverageRectangle, _partition
from .complex_interval import complex_box_jet, entire_source, valid_box
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    RecursionError,
)


def _point(value):
    x, y = sp.re(value), sp.im(value)
    return x, y, x, y


def _plus(a, b):
    return a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]


def _minus(a, b):
    return a[0] - b[2], a[1] - b[3], a[2] - b[0], a[3] - b[1]


def _times(a, b):
    def real_mul(x, y):
        products = tuple(p * q for p in x for q in y)
        return min(products), max(products)

    xu = real_mul((a[0], a[2]), (b[0], b[2]))
    yv = real_mul((a[1], a[3]), (b[1], b[3]))
    xv = real_mul((a[0], a[2]), (b[1], b[3]))
    yu = real_mul((a[1], a[3]), (b[0], b[2]))
    return xu[0] - yv[1], xv[0] + yu[0], xu[1] - yv[0], xv[1] + yu[1]


def _inside(inner, outer):
    return (
        outer[0] < inner[0]
        and outer[1] < inner[1]
        and inner[2] < outer[2]
        and inner[3] < outer[3]
    )


def _midpoint(box):
    return (box[0] + box[2]) / 2 + sp.I * (box[1] + box[3]) / 2


def _inverse(box):
    x, y = sp.re(_midpoint(box)), sp.im(_midpoint(box))
    square = x * x + y * y
    return None if square == 0 else x / square - sp.I * y / square


def _image(rectangle, center, value, derivative, inverse):
    residual = _minus(_point(sp.S.One), _times(_point(inverse), derivative))
    image = _plus(
        _minus(_point(center), _times(_point(inverse), value)),
        _times(residual, _minus(rectangle.bounds(), _point(center))),
    )
    contraction = max(abs(residual[0]), abs(residual[2])) + max(
        abs(residual[1]), abs(residual[3])
    )
    return residual, image, contraction


def _layout(rectangle, child):
    a, b, c, d = rectangle.bounds()
    e, f, g, h = child.bounds()
    return (
        child,
        CoverageRectangle(a + b * sp.I, e + d * sp.I),
        CoverageRectangle(g + b * sp.I, c + d * sp.I),
        CoverageRectangle(e + b * sp.I, g + f * sp.I),
        CoverageRectangle(e + h * sp.I, g + d * sp.I),
    )


@dataclass(frozen=True)
class ComplexDerivativeWitness:
    """Enclose the complex derivative on a rational rectangle."""

    expression: sp.Expr
    variable: sp.Symbol
    box: tuple
    bounds: tuple
    precision: int
    max_series_terms: int = 4096
    order: int = 1
    schema_version: int = 1

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self) is not ComplexDerivativeWitness
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or type(self.order) is not int
                or self.order != 1
                or not valid_box(self.bounds)
            ):
                return False
            actual = complex_box_jet(
                self.expression,
                self.variable,
                self.box,
                precision=self.precision,
                max_series_terms=self.max_series_terms,
            )
            return actual is not None and actual[1] == self.bounds
        except _ERRORS:
            return False

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "entire-complex-first-derivative-enclosure"


@dataclass(frozen=True)
class ComplexNewtonRefinement:
    """Bind a Krawczyk contraction to its parent, child and four complements."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    parent: object
    center: sp.Expr
    value: ComplexBoxWitness
    derivative: ComplexDerivativeWitness
    center_derivative: ComplexDerivativeWitness
    inverse: sp.Expr
    residual: tuple
    image: tuple
    contraction: sp.Rational
    child_rectangle: CoverageRectangle
    tested: int = 2
    schema_version: int = 1

    @property
    def complete(self):
        return True

    @property
    def zero_count(self):
        return 1

    @property
    def root_count(self):
        return 1

    @property
    def multiplicity_count(self):
        return 1

    @property
    def scope(self):
        return "complex-krawczyk-count-one-refinement"

    @property
    def regions(self):
        return tuple(ComplexNewtonRegion(self, index) for index in range(5))

    @property
    def root_region(self):
        return self.regions[0]

    @property
    def zero_regions(self):
        return self.regions[1:]

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_complex_refinement(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def certified(self):
        return self.verify()


@dataclass(frozen=True)
class ComplexNewtonRegion:
    """Transfer a parent's count to a checked Newton child or complement."""

    refinement: ComplexNewtonRefinement
    index: int
    schema_version: int = 1

    @property
    def expression(self):
        return self.refinement.expression

    @property
    def variable(self):
        return self.refinement.variable

    @property
    def rectangle(self):
        return _layout(self.refinement.rectangle, self.refinement.child_rectangle)[
            self.index
        ]

    @property
    def zero_count(self):
        return int(self.index == 0)

    @property
    def root_count(self):
        return self.zero_count

    @property
    def multiplicity_count(self):
        return self.zero_count

    @property
    def complete(self):
        return True

    @property
    def scope(self):
        return "complex-krawczyk-transferred-region-count"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        valid = (
            type(self) is ComplexNewtonRegion
            and type(self.refinement) is ComplexNewtonRefinement
            and _valid_region(self, self.expression, self.variable, {})
        )
        return CheckResult(
            CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
            valid,
            valid,
            None if valid else "false-newton-region",
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return self.check().certified is True
        except _ERRORS:
            return False

    @property
    def certified(self):
        return self.verify()


def _valid_region(region, f, z, memo):
    """Check count transfer to one contraction child or one of its complement strips."""

    from .shared_zeros import (
        ComplexZeroSubsetProof,
        SharedZeroOrderProof,
        SharedZeroRegion,
        _valid_shared_region,
    )

    if type(region) in (ComplexZeroSubsetProof, SharedZeroOrderProof, SharedZeroRegion):
        try:
            return (
                region.expression == f
                and region.variable == z
                and _valid_shared_region(region, memo)
            )
        except _ERRORS:
            return False
    from .complex_multiplicity import (
        ComplexExactMultiplicity,
        ComplexLocatedRegion,
        ComplexPowerFactorProof,
        ComplexPowerRootRegion,
        _valid_multiple,
    )

    if type(region) in (
        ComplexExactMultiplicity,
        ComplexLocatedRegion,
        ComplexPowerFactorProof,
        ComplexPowerRootRegion,
    ):
        try:
            return (
                region.expression == f
                and region.variable == z
                and _valid_multiple(region, memo)
            )
        except _ERRORS:
            return False
    # Memoization caches arithmetic validity, never a different source binding.
    try:
        if region.expression != f or region.variable != z:
            return False
    except _ERRORS:
        return False
    key = id(region)
    if key in memo:
        return memo[key]
    memo[key] = False  # Also rejects cyclic parent graphs.
    try:
        if type(region) not in (AnalyticContourCertificate, ComplexNewtonRegion) or (
            type(region) is ComplexNewtonRegion
            and type(region.refinement) is not ComplexNewtonRefinement
        ):
            return False
        if region.expression != f or region.variable != z:
            return False
        if type(region) is AnalyticContourCertificate:
            valid = (
                type(region.rectangle) is CoverageRectangle
                and region.complete
                and type(region.zero_count) is int
                and all(type(w) is ComplexBoxWitness for w in region.images)
                and check_analytic_contour(region).certified is True
            )
        elif type(region) is ComplexNewtonRegion:
            valid = (
                type(region.schema_version) is int
                and region.schema_version == 1
                and type(region.index) is int
                and 0 <= region.index < 5
                and _valid_refinement(region.refinement, memo)
            )
        else:
            valid = False
        memo[key] = valid
        return valid
    except _ERRORS:
        return False


def _valid_refinement(c, memo):
    """Reconstruct the Krawczyk image, strict contraction and exact complement geometry."""

    key = id(c)
    if key in memo:
        return memo[key]
    memo[key] = False
    try:
        if (
            type(c) is not ComplexNewtonRefinement
            or not _header(c)
            or type(c.rectangle) is not CoverageRectangle
            or not entire_source(c.expression, c.variable)
            or type(c.child_rectangle) is not CoverageRectangle
            or not c.child_rectangle.valid()
            or not _inside(c.child_rectangle.bounds(), c.rectangle.bounds())
            or type(c.tested) is not int
            or c.tested < 2
        ):
            return False
        f, z = c.expression, c.variable
        if (
            not _valid_region(c.parent, f, z, memo)
            or c.parent.zero_count != 1
            or c.parent.rectangle != c.rectangle
            or c.center != _midpoint(c.rectangle.bounds())
            or not valid_box(_point(c.center))
        ):
            return False
        for witness, kind, box in (
            (c.value, ComplexBoxWitness, _point(c.center)),
            (c.derivative, ComplexDerivativeWitness, c.rectangle.bounds()),
            (c.center_derivative, ComplexDerivativeWitness, _point(c.center)),
        ):
            if (
                type(witness) is not kind
                or witness.expression != f
                or witness.variable != z
                or witness.box != box
                or not witness.verify()
            ):
                return False
        if (
            c.inverse is None
            or c.inverse != _inverse(c.center_derivative.bounds)
            or not valid_box(_point(c.inverse))
            or c.inverse == 0
        ):
            return False
        residual, image, contraction = _image(
            c.rectangle, c.center, c.value.bounds, c.derivative.bounds, c.inverse
        )
        if (
            c.residual != residual
            or c.image != image
            or c.contraction != contraction
            or not isinstance(c.contraction, sp.Rational)
            or not 0 <= contraction < 1
            or not _inside(image, c.child_rectangle.bounds())
        ):
            return False
        a, b, cx, d = c.rectangle.bounds()
        e, f0, g, h = c.child_rectangle.bounds()
        if g - e > sp.Rational(3, 4) * (cx - a) or h - f0 > sp.Rational(3, 4) * (d - b):
            return False
        if not _partition(c.rectangle, _layout(c.rectangle, c.child_rectangle)):
            return False
        memo[key] = True
        return True
    except _ERRORS:
        return False


def check_complex_refinement(c):
    """Replay strict Krawczyk contraction and count transfer without search."""
    if (
        type(c) is not ComplexNewtonRefinement
        or type(c.schema_version) is not int
        or c.schema_version != 1
    ):
        return CheckResult(
            CheckOutcome.UNSUPPORTED,
            None,
            False,
            "unsupported-complex-refinement-schema",
        )
    valid = _valid_refinement(c, {})
    return CheckResult(
        CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
        valid,
        valid,
        None if valid else "false-complex-refinement-premise",
    )


def _propose_refinement(parent, policy, max_box_width=None, max_box_diameter=None):
    """Propose a rational Krawczyk child and retain four counted complement strips."""

    used = 0
    if (
        type(parent) not in (AnalyticContourCertificate, ComplexNewtonRegion)
        or parent.zero_count != 1
    ):
        return None, used
    rectangle = parent.rectangle
    center = _midpoint(rectangle.bounds())
    for precision in policy.precisions:
        if used + 2 > policy.max_cells:
            break
        # The two outward jet evaluations are query-wide charged work, even
        # when no contraction can be accepted at this precision.
        whole = complex_box_jet(
            parent.expression,
            parent.variable,
            rectangle.bounds(),
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        at_center = complex_box_jet(
            parent.expression,
            parent.variable,
            _point(center),
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        used += 2
        if whole is None or at_center is None:
            continue
        inverse = _inverse(at_center[1])
        if inverse is None:
            continue
        residual, image, contraction = _image(
            rectangle, center, at_center[0], whole[1], inverse
        )
        if contraction >= 1 or not _inside(image, rectangle.bounds()):
            continue
        a, b, c, d = rectangle.bounds()
        e, f, g, h = image
        floor = sp.Rational(1, 10**precision)
        caps = [v / 16 for v in (max_box_width, max_box_diameter) if v is not None]
        px = min((e - a) / 4, (c - g) / 4, (c - a) / 32, max((g - e) / 8, floor), *caps)
        py = min((f - b) / 4, (d - h) / 4, (d - b) / 32, max((h - f) / 8, floor), *caps)
        child = CoverageRectangle(e - px + sp.I * (f - py), g + px + sp.I * (h + py))
        cert = ComplexNewtonRefinement(
            parent.expression,
            parent.variable,
            rectangle,
            sp.srepr(parent.expression),
            tuple(sorted(parent.variable.assumptions0.items())),
            parent,
            center,
            ComplexBoxWitness(
                parent.expression,
                parent.variable,
                _point(center),
                at_center[0],
                precision,
                policy.max_series_terms,
            ),
            ComplexDerivativeWitness(
                parent.expression,
                parent.variable,
                rectangle.bounds(),
                whole[1],
                precision,
                policy.max_series_terms,
            ),
            ComplexDerivativeWitness(
                parent.expression,
                parent.variable,
                _point(center),
                at_center[1],
                precision,
                policy.max_series_terms,
            ),
            inverse,
            residual,
            image,
            contraction,
            child,
            tested=used,
        )
        if cert.verify():
            return cert, used
    return None, used


def certify_complex_refinement(parent, *, policy=None):
    """Contract a known count-one rectangle, or return None without new claims.

    Accepts a native count certificate or a public CertifiedComplexRootRectangle.
    A failed Newton proposal leaves the existing parent proof untouched.
    """
    parent = getattr(parent, "certificate", parent)
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_complex_refinement",
            parent,
            (),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    if type(parent) not in (
        AnalyticContourCertificate,
        ComplexNewtonRegion,
    ) or not _valid_region(parent, parent.expression, parent.variable, {}):
        return None
    return _propose_refinement(parent, policy)[0]
