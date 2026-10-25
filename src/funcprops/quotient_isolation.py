"""Source-defined quotient zeros and meromorphic poles on rational rectangles.

The source grammar is rational arithmetic over the entire grammar. Raw inverse
bases remain exclusions after exact factor cancellation. Independent replay
checks local counts and a full rectangle partition; it never calls the search.
"""

from collections import deque
from dataclasses import dataclass, replace

import sympy as sp

from ._checkpoints import checkpoint_sink
from .analytic_contours import (
    AnalyticContourCertificate,
    _header,
    certify_analytic_contour,
    check_analytic_contour,
)
from .complex_coverage import CoverageRectangle, _partition
from .complex_interval import entire_source, valid_box
from .complex_isolation import (
    ComplexIsolationTask,
    _accurate,
    _children,
    _dovetail,
    _individual,
    _split_choice,
)
from .complex_multiplicity import _propose_multiple
from .complex_newton import _valid_region
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy
from .implicit_orders import ImplicitMultiplicityProof, ImplicitRootValueProof
from .shared_zeros import (
    SharedZeroImplication,
    SharedZeroOrderProof,
    _propose_implication,
    same_base,
    shared_base,
    valid_zero_implication,
)
from .source_syntax import differentiate

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    RecursionError,
    sp.PolynomialError,
)
_RATIOS = {
    sp.tan: (sp.sin, sp.cos),
    sp.cot: (sp.cos, sp.sin),
    sp.sec: (None, sp.cos),
    sp.csc: (None, sp.sin),
    sp.tanh: (sp.sinh, sp.cosh),
    sp.coth: (sp.cosh, sp.sinh),
    sp.sech: (None, sp.cosh),
    sp.csch: (None, sp.sinh),
}


def _fraction(node, z):
    """A structural fraction and *all* original nonzero premises, without cancel."""
    if entire_source(node, z):
        return node, sp.S.One, ()
    if node.func in _RATIOS and entire_source(node.args[0], z):
        nf, df = _RATIOS[node.func]
        n = sp.S.One if nf is None else nf(node.args[0])
        d = df(node.args[0])
        return n, d, (d,)
    if node.is_Add or node.is_Mul:
        n, d, guards = (sp.S.Zero if node.is_Add else sp.S.One), sp.S.One, ()
        for arg in node.args:
            part = _fraction(arg, z)
            if part is None:
                return None
            a, b, gs = part
            n, d = (n * b + a * d, d * b) if node.is_Add else (n * a, d * b)
            guards += gs
        return n, d, tuple(dict.fromkeys(guards))
    if node.is_Pow and isinstance(node.exp, sp.Integer):
        part = _fraction(node.base, z)
        if part is None:
            return None
        n, d, gs = part
        k = node.exp
        if k < 0:
            return d ** (-k), n ** (-k), tuple(dict.fromkeys((*gs, n)))
        return n**k, d**k, gs
    return None


def quotient_source_supported(expression, variable):
    """Test the supported entire-quotient grammar while retaining raw source guards."""

    try:
        f, z = map(sp.sympify, (expression, variable))
        return (
            isinstance(z, sp.Symbol)
            and z.assumptions0 == {"commutative": True}
            and not f.free_symbols - {z}
            and not f.has(sp.Float)
            and (part := _fraction(f, z)) is not None
            and part[1] != 0
            and all(g != 0 for g in part[2])
            and not entire_source(f, z)
        )
    except _ERRORS:
        return False


@dataclass(frozen=True)
class QuotientSourceProof:
    """Bind an entire numerator/denominator representation to original source guards."""

    expression: sp.Expr
    variable: sp.Symbol
    numerator: sp.Expr
    denominator: sp.Expr
    common: sp.Expr
    guards: tuple
    source_syntax: str
    schema_version: int = 1

    @property
    def scope(self):
        return "exact-entire-quotient-with-original-source-exclusions"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            f, z = self.expression, self.variable
            if (
                type(self) is not QuotientSourceProof
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or not quotient_source_supported(f, z)
                or self.source_syntax != sp.srepr(f)
                or type(self.guards) is not tuple
            ):
                return False
            raw_n, raw_d, gs = _fraction(f, z)
            return (
                self.guards == gs
                and all(
                    entire_source(e, z)
                    for e in (self.numerator, self.denominator, self.common)
                )
                and all(
                    not e.has(sp.Float) and not e.free_symbols - {z}
                    for e in (self.numerator, self.denominator, self.common)
                )
                and self.denominator != 0
                and self.common != 0
                and raw_d != 0
                and sp.expand(raw_n - self.common * self.numerator) == 0
                and sp.expand(raw_d - self.common * self.denominator) == 0
            )
        except _ERRORS:
            return False


def _source(f, z, cancel=True):
    n, d, guards = _fraction(f, z)
    common = sp.S.One
    if cancel and sp.count_ops(n) + sp.count_ops(d) <= 512 and d != 0:
        try:
            a, b = sp.fraction(sp.cancel(n / d))
            fa, fb = sp.factor(a), sp.factor(b)
            if entire_source(fa, z) and entire_source(fb, z):
                a, b = fa, fb
            c = sp.cancel(d / b)
            p = QuotientSourceProof(f, z, a, b, c, guards, sp.srepr(f))
            if p.verify():
                return p
        except _ERRORS:
            pass
    return QuotientSourceProof(f, z, n, d, common, guards, sp.srepr(f))


@dataclass(frozen=True)
class DenominatorExclusionProof:
    """Prove that a quotient denominator and its source guards stay nonzero."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    contour: AnalyticContourCertificate
    schema_version: int = 1

    @property
    def scope(self):
        return "entire-denominator-nonzero-on-closed-rectangle"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            c = self.contour
            return (
                type(self) is DenominatorExclusionProof
                and type(self.schema_version) is int
                and self.schema_version == 1
                and type(self.rectangle) is CoverageRectangle
                and self.rectangle.valid()
                and type(c) is AnalyticContourCertificate
                and c.expression == self.expression
                and c.variable == self.variable
                and c.rectangle.contains_rectangle(self.rectangle)
                and c.zero_count == 0
                and check_analytic_contour(c).certified is True
            )
        except _ERRORS:
            return False


@dataclass(frozen=True)
class ExactLocalZeroProof:
    """Exact vanishing jets plus an exhaustive local count locate all its zeros.

    If the count is m and the first m jets vanish at c, the analytic order is
    at least m. The finite count then proves exact order m and no other zero.
    """

    region: object
    center: sp.Expr
    jets: tuple
    schema_version: int = 1

    @property
    def expression(self):
        return self.region.expression

    @property
    def variable(self):
        return self.region.variable

    @property
    def scope(self):
        return "exact-local-zero-from-jets-and-exhaustive-count"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            r, c = self.region, self.center
            x, y = sp.re(c), sp.im(c)
            a, b, u, v = r.rectangle.bounds()
            m = r.zero_count
            if (
                type(self) is not ExactLocalZeroProof
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or type(m) is not int
                or m < 1
                or not valid_box((x, y, x, y))
                or not a < x < u
                or not b < y < v
                or type(self.jets) is not tuple
                or len(self.jets) != m
                or not _valid_region(r, r.expression, r.variable, {})
            ):
                return False
            expected = tuple(
                differentiate(r.expression, r.variable, k).subs(r.variable, c)
                for k in range(m)
            )
            return self.jets == expected and all(e == 0 for e in expected)
        except _ERRORS:
            return False


@dataclass(frozen=True)
class QuotientCellProof:
    """Account for source zeros, extension zeros and poles on one checked cell."""

    numerator: object
    denominator: object
    exclusions: tuple = ()
    numerator_location: ExactLocalZeroProof | None = None
    denominator_location: ExactLocalZeroProof | None = None
    excluded_guard: sp.Expr | None = None
    guard_cofactor: sp.Expr | None = None
    schema_version: int = 1
    guard_zero: (
        SharedZeroImplication
        | ImplicitRootValueProof
        | ImplicitMultiplicityProof
        | None
    ) = None

    @property
    def rectangle(self):
        return self.numerator.rectangle


def _cell_data(source, cell):
    """Return actual zero count, pole count, extension zeros, and distinct counts."""
    n, d = cell.numerator.zero_count, cell.denominator.zero_count
    ni = _individual(cell.numerator) or cell.numerator_location is not None
    di = _individual(cell.denominator) or cell.denominator_location is not None
    if n == 0:
        return 0, d, 0, 0, (0 if d == 0 else 1 if di else None)
    if d > 0:
        if (
            cell.numerator_location is not None
            and cell.denominator_location is not None
            and cell.numerator_location.center == cell.denominator_location.center
        ) or same_base(shared_base(cell.numerator), shared_base(cell.denominator)):
            p, e = max(d - n, 0), max(n - d, 0)
            return 0, p, e, 0, int(p > 0)
        return None
    if cell.excluded_guard is not None or cell.guard_zero is not None:
        return 0, 0, n, 0, 0
    if len(cell.exclusions) == len(source.guards):
        return n, 0, n, (1 if ni else None), 0
    return None


@dataclass(frozen=True)
class QuotientRegionProof:
    """Bind a local quotient divisor conclusion to count and shared-order proofs."""

    source: QuotientSourceProof
    cell: QuotientCellProof
    kind: str = "zero"
    schema_version: int = 1
    guard_contours: tuple = ()

    @property
    def expression(self):
        return self.source.expression

    @property
    def variable(self):
        return self.source.variable

    @property
    def rectangle(self):
        return self.cell.rectangle

    @property
    def multiplicity_count(self):
        data = _cell_data(self.source, self.cell)
        return None if data is None else data[0 if self.kind == "zero" else 1]

    @property
    def zero_count(self):
        return self.multiplicity_count if self.kind == "zero" else 0

    @property
    def known_distinct(self):
        data = _cell_data(self.source, self.cell)
        return None if data is None else data[3 if self.kind == "zero" else 4]

    @property
    def exclusions(self):
        return self.cell.exclusions

    @property
    def distinct_root_count(self):
        return self.known_distinct if self.kind == "zero" else 0

    @property
    def distinct_pole_count(self):
        return self.known_distinct if self.kind == "pole" else 0

    @property
    def scope(self):
        return "quotient-" + self.kind + "-region"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return (
                type(self) is QuotientRegionProof
                and type(self.schema_version) is int
                and self.schema_version == 1
                and self.kind in ("zero", "pole")
                and type(self.source) is QuotientSourceProof
                and self.source.verify()
                and _valid_cell(self.source, self.cell)
                and self._source_domain_valid()
                and self.multiplicity_count is not None
                and self.multiplicity_count > 0
            )
        except _ERRORS:
            return False

    def _source_domain_valid(self):
        # A formal cancellation identity is conditional on the original guards.
        # A source with an identically zero guard has no meromorphic germ. Pole
        # counts therefore need nontriviality of *every* guard, even though the
        # guards are allowed to vanish at the pole. A verified zero-free contour
        # around a containing box proves each entire guard is not identically zero.
        if type(self.guard_contours) is not tuple:
            return False
        if not self.guard_contours and self.kind == "zero":
            # Positive source-zero regions already prove all guards nonzero
            # on their closed box through the cell's exclusion witnesses.
            return len(self.cell.exclusions) == len(self.source.guards)
        if len(self.guard_contours) != len(self.source.guards):
            return False
        return all(
            type(c) is AnalyticContourCertificate
            and c.expression == g
            and c.variable == self.variable
            and type(c.rectangle) is CoverageRectangle
            and c.rectangle.contains_rectangle(self.rectangle)
            and c.complete
            and check_analytic_contour(c).certified is True
            for g, c in zip(self.source.guards, self.guard_contours, strict=True)
        )


def _valid_cell(source, cell):
    if (
        type(cell) is not QuotientCellProof
        or type(cell.schema_version) is not int
        or cell.schema_version != 1
        or type(cell.exclusions) is not tuple
    ):
        return False
    n, d, z = cell.numerator, cell.denominator, source.variable
    if (
        not _valid_region(n, source.numerator, z, {})
        or not _valid_region(d, source.denominator, z, {})
        or n.rectangle != d.rectangle
    ):
        return False
    for loc, r in ((cell.numerator_location, n), (cell.denominator_location, d)):
        if loc is not None and (
            type(loc) is not ExactLocalZeroProof or loc.region != r or not loc.verify()
        ):
            return False
    if len(cell.exclusions) not in (0, len(source.guards)):
        return False
    if any(
        type(w) is not DenominatorExclusionProof
        or w.expression != g
        or w.variable != z
        or w.rectangle != cell.rectangle
        or not w.verify()
        for w, g in zip(cell.exclusions, source.guards, strict=False)
    ):
        return False
    if cell.excluded_guard is not None:
        g = cell.excluded_guard
        if g not in source.guards or d.zero_count != 0:
            return False
        if cell.guard_cofactor is not None:
            if (
                not entire_source(cell.guard_cofactor, z)
                or cell.guard_cofactor.free_symbols - {z}
                or cell.guard_cofactor.has(sp.Float)
                or sp.expand(g - source.numerator * cell.guard_cofactor) != 0
            ):
                return False
        elif (
            cell.numerator_location is None
            or g.subs(z, cell.numerator_location.center) != 0
        ):
            return False
    elif cell.guard_cofactor is not None:
        return False
    if cell.guard_zero is not None:
        w = cell.guard_zero
        if (
            not valid_zero_implication(w, {})
            or w.expression not in source.guards
            or w.variable != z
            or d.zero_count != 0
            or not same_base(w.base_region, shared_base(n))
        ):
            return False
    return True


@dataclass(frozen=True)
class QuotientIsolationProof:
    """Assemble a source-preserving zero/pole ledger over a rectangle."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    source: QuotientSourceProof
    outer: tuple = ()
    cells: tuple = ()
    unresolved: tuple = ()
    max_box_width: sp.Rational | None = None
    max_box_diameter: sp.Rational | None = None
    exhaustion: str | None = None
    schema_version: int = 1
    refinements: tuple = ()

    @property
    def scope(self):
        return "source-defined-quotient-zeros-and-meromorphic-poles"

    @property
    def coverage_complete(self):
        return (
            bool(self.outer)
            and not self.unresolved
            and all(_cell_data(self.source, c) is not None for c in self.cells)
        )

    @property
    def isolation_complete(self):
        return self.coverage_complete and all(
            None not in _cell_data(self.source, c)[3:] for c in self.cells
        )

    @property
    def accuracy_complete(self):
        return self.isolation_complete and all(
            _accurate(c, self.max_box_width, self.max_box_diameter)
            for c in self.cells
            if any(_cell_data(self.source, c)[:2])
        )

    @property
    def complete(self):
        return (
            self.coverage_complete
            and self.isolation_complete
            and self.accuracy_complete
        )

    @property
    def multiplicity_count(self):
        return (
            sum(_cell_data(self.source, c)[0] for c in self.cells)
            if self.coverage_complete
            else None
        )

    @property
    def total_count(self):
        return self.multiplicity_count

    @property
    def root_count(self):
        return (
            sum(_cell_data(self.source, c)[3] for c in self.cells)
            if self.isolation_complete
            else None
        )

    @property
    def distinct_root_count(self):
        return self.root_count

    @property
    def pole_multiplicity_count(self):
        return (
            sum(_cell_data(self.source, c)[1] for c in self.cells)
            if self.coverage_complete
            else None
        )

    @property
    def distinct_pole_count(self):
        return (
            sum(_cell_data(self.source, c)[4] for c in self.cells)
            if self.isolation_complete
            else None
        )

    @property
    def extension_zero_count(self):
        return (
            sum(_cell_data(self.source, c)[2] for c in self.cells)
            if self.coverage_complete
            else None
        )

    @property
    def excluded_zero_multiplicity(self):
        return (
            self.extension_zero_count - self.multiplicity_count
            if self.coverage_complete
            else None
        )

    @property
    def winding_count(self):
        # This counts the meromorphic extension; excluded source zeros are separate.
        return (
            self.outer[0].zero_count - self.outer[1].zero_count if self.outer else None
        )

    @property
    def holomorphic_on_rectangle(self):
        return bool(self.outer) and all(c.zero_count == 0 for c in self.outer[1:])

    @property
    def root_regions(self):
        return tuple(
            QuotientRegionProof(self.source, c)
            for c in self.cells
            if (v := _cell_data(self.source, c)) is not None
            and v[0]
            and v[3] is not None
        )

    @property
    def pole_regions(self):
        return tuple(
            QuotientRegionProof(self.source, c, "pole", guard_contours=self.outer[2:])
            for c in self.cells
            if (v := _cell_data(self.source, c)) is not None
            and v[1]
            and v[4] is not None
        )

    @property
    def denominator_exclusions(self):
        return tuple(
            DenominatorExclusionProof(g, self.variable, self.rectangle, c)
            for g, c in zip(self.source.guards, self.outer[2:], strict=False)
            if c.zero_count == 0
        )

    @property
    def clusters(self):
        regions = []
        for c in self.cells:
            v = _cell_data(self.source, c)
            if v is not None:
                if v[3] is None:
                    regions.append(QuotientRegionProof(self.source, c))
                if v[4] is None:
                    regions.append(
                        QuotientRegionProof(
                            self.source, c, "pole", guard_contours=self.outer[2:]
                        )
                    )
        return tuple(regions)

    @property
    def isolating_boxes(self):
        return tuple(c.rectangle for c in self.root_regions)

    @property
    def individual_multiplicities(self):
        return (
            tuple(c.multiplicity_count for c in self.root_regions)
            if self.isolation_complete
            else None
        )

    @property
    def obligations(self):
        return tuple(
            s
            for test, s in (
                (not self.outer, "unresolved-outer-source-boundary"),
                (bool(self.unresolved), "unresolved-regions"),
                (
                    any(_cell_data(self.source, c) is None for c in self.cells),
                    "unresolved-source-collisions",
                ),
                (bool(self.clusters), "unseparated-root-or-pole-clusters"),
                (
                    self.isolation_complete and not self.accuracy_complete,
                    "requested-box-accuracy",
                ),
            )
            if test
        )

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_quotient_isolation(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def check_quotient_isolation(p):
    """Check the stored quotient isolation premises and report their replay outcome."""

    rejected = CheckResult(
        CheckOutcome.REJECTED, False, False, "false-quotient_isolation-premise"
    )
    try:
        if (
            type(p) is not QuotientIsolationProof
            or type(p.schema_version) is not int
            or p.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "unsupported-quotient-schema"
            )
        if (
            not _header(p)
            or type(p.rectangle) is not CoverageRectangle
            or type(p.source) is not QuotientSourceProof
            or p.source.expression != p.expression
            or p.source.variable != p.variable
            or not p.source.verify()
            or any(
                type(t) is not tuple
                for t in (p.outer, p.cells, p.unresolved, p.refinements)
            )
            or any(
                v is not None and (not isinstance(v, sp.Rational) or v <= 0)
                for v in (p.max_box_width, p.max_box_diameter)
            )
            or p.exhaustion
            not in (
                None,
                "cell-budget",
                "depth-budget",
                "wall-budget",
                "boundary-obligation",
            )
            or any(type(r) is not CoverageRectangle for r in p.unresolved)
        ):
            return rejected
        from .quotient_refinement import QuotientNewtonRefinement

        if any(
            type(r) is not QuotientNewtonRefinement
            or r.source != p.source
            or not p.rectangle.contains_rectangle(r.rectangle)
            or not r.verify()
            for r in p.refinements
        ):
            return rejected
        if not p.outer:
            if p.cells or p.refinements or p.unresolved != (p.rectangle,):
                return rejected
        else:
            fs = (p.source.numerator, p.source.denominator, *p.source.guards)
            if len(p.outer) != len(fs):
                return rejected
            for c, f in zip(p.outer, fs, strict=True):
                if (
                    type(c) is not AnalyticContourCertificate
                    or c.expression != f
                    or c.variable != p.variable
                    or c.rectangle != p.rectangle
                    or not c.complete
                    or check_analytic_contour(c).certified is not True
                ):
                    return rejected
        if any(not _valid_cell(p.source, c) for c in p.cells) or not _partition(
            p.rectangle, tuple(c.rectangle for c in p.cells) + p.unresolved
        ):
            return rejected
        if p.outer and not p.unresolved:
            if (
                sum(c.numerator.zero_count for c in p.cells) != p.outer[0].zero_count
                or sum(c.denominator.zero_count for c in p.cells)
                != p.outer[1].zero_count
            ):
                return rejected
        if p.complete and p.exhaustion is not None:
            return rejected
        return CheckResult(
            CheckOutcome.COMPLETE
            if p.complete
            else CheckOutcome.EXHAUSTED
            if p.exhaustion
            else CheckOutcome.LOCAL_VALID,
            True,
            p.complete,
            p.exhaustion or "; ".join(p.obligations) or None,
        )
    except _ERRORS:
        return rejected


@dataclass(frozen=True)
class QuotientContourCertificate:
    """Divisor counts of the extension; original-source zeros stay explicit."""

    proof: QuotientIsolationProof
    schema_version: int = 1

    @property
    def expression(self):
        return self.proof.expression

    @property
    def variable(self):
        return self.proof.variable

    @property
    def lower_left(self):
        return self.proof.rectangle.lower_left

    @property
    def upper_right(self):
        return self.proof.rectangle.upper_right

    @property
    def zeros(self):
        return self.proof.extension_zero_count

    @property
    def poles(self):
        return self.proof.pole_multiplicity_count

    @property
    def winding(self):
        return self.proof.winding_count

    @property
    def source_zero_count(self):
        return self.proof.total_count

    @property
    def complete(self):
        return self.proof.coverage_complete

    @property
    def scope(self):
        return "meromorphic-extension-divisor-count-on-source-defined-boundary"

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        try:
            valid = (
                type(self) is QuotientContourCertificate
                and type(self.schema_version) is int
                and self.schema_version == 1
                and type(self.proof) is QuotientIsolationProof
                and self.proof.verify()
                and self.proof.coverage_complete
                and self.zeros - self.poles == self.winding
            )
            return CheckResult(
                CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
                bool(valid),
                bool(valid),
                None if valid else "false-quotient-divisor-count",
            )
        except _ERRORS:
            return CheckResult(
                CheckOutcome.REJECTED, False, False, "false-quotient-divisor-count"
            )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def _needs_work(p, c):
    data = _cell_data(p.source, c)
    return (
        data is None
        or None in data[3:]
        or (any(data[:2]) and not _accurate(c, p.max_box_width, p.max_box_diameter))
    )


@dataclass(frozen=True)
class QuotientIsolationState:
    """Retain a quotient proof and every pending subdivision task."""

    proof: QuotientIsolationProof
    pending: tuple = ()
    tested: int = 0
    generation: int = 0
    schema_version: int = 1

    @property
    def state(self):
        return self

    @property
    def expression(self):
        return self.proof.expression

    @property
    def variable(self):
        return self.proof.variable

    @property
    def complete(self):
        return self.proof.complete

    @property
    def scope(self):
        return "resumable-quotient-root-and-pole-isolation"

    @property
    def coverage_complete(self):
        return self.proof.coverage_complete

    @property
    def isolation_complete(self):
        return self.proof.isolation_complete

    @property
    def accuracy_complete(self):
        return self.proof.accuracy_complete

    @property
    def root_count(self):
        return self.proof.root_count

    @property
    def total_count(self):
        return self.proof.total_count

    @property
    def multiplicity_count(self):
        return self.proof.multiplicity_count

    @property
    def distinct_root_count(self):
        return self.proof.distinct_root_count

    @property
    def pole_multiplicity_count(self):
        return self.proof.pole_multiplicity_count

    @property
    def distinct_pole_count(self):
        return self.proof.distinct_pole_count

    @property
    def isolating_boxes(self):
        return self.proof.isolating_boxes

    @property
    def clusters(self):
        return self.proof.clusters

    @property
    def unresolved(self):
        return self.proof.unresolved

    @property
    def refinements(self):
        return self.proof.refinements

    @property
    def exhaustion(self):
        return self.proof.exhaustion

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        rejected = CheckResult(
            CheckOutcome.REJECTED, False, False, "false-quotient-checkpoint"
        )
        try:
            if (
                type(self) is not QuotientIsolationState
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or type(self.proof) is not QuotientIsolationProof
                or type(self.pending) is not tuple
                or any(
                    type(n) is not int or n < 0 for n in (self.tested, self.generation)
                )
            ):
                return rejected
            boxes = []
            for t in self.pending:
                if (
                    type(t) is not ComplexIsolationTask
                    or type(t.rectangle) is not CoverageRectangle
                    or type(t.path) is not tuple
                    or type(t.attempt) is not int
                    or t.attempt < 0
                ):
                    return rejected
                r = self.proof.rectangle
                for step in t.path:
                    if type(step) is not tuple or len(step) != 3:
                        return rejected
                    axis, ratio, side = step
                    if (
                        type(axis) is not int
                        or axis not in (0, 1)
                        or type(side) is not int
                        or side not in (0, 1)
                        or not isinstance(ratio, sp.Rational)
                        or not 0 < ratio < 1
                    ):
                        return rejected
                    r = _children(r, axis, ratio)[side]
                if r != t.rectangle or r in boxes:
                    return rejected
                boxes.append(r)
            expected = self.proof.unresolved + tuple(
                c.rectangle for c in self.proof.cells if _needs_work(self.proof, c)
            )
            if set(boxes) != set(expected):
                return rejected
            return self.proof.check()
        except _ERRORS:
            return rejected

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def _seed(
    expr,
    var,
    lower_left,
    upper_right,
    max_box_width=None,
    max_box_diameter=None,
    *,
    cancel=False,
):
    f, z, lo, hi = map(sp.sympify, (expr, var, lower_left, upper_right))
    if not quotient_source_supported(f, z):
        raise ValueError("unsupported entire-quotient source")
    targets = tuple(
        None if v is None else sp.sympify(v) for v in (max_box_width, max_box_diameter)
    )
    if any(
        v is not None and (not isinstance(v, sp.Rational) or v <= 0) for v in targets
    ):
        raise ValueError("box targets must be positive exact rationals")
    r = CoverageRectangle(lo, hi)
    if not r.valid():
        raise ValueError("require a nonempty rational rectangle")
    p = QuotientIsolationProof(
        f,
        z,
        r,
        sp.srepr(f),
        tuple(sorted(z.assumptions0.items())),
        _source(f, z, cancel),
        unresolved=(r,),
        max_box_width=targets[0],
        max_box_diameter=targets[1],
    )
    return QuotientIsolationState(p, (ComplexIsolationTask(r),))


def _wall_state(state):
    if state.complete:
        return state
    return replace(state, proof=replace(state.proof, exhaustion="wall-budget"))


def _rectangle_path(task, child):
    a, b, c, d = task.rectangle.bounds()
    e, f, g, h = child.bounds()
    path = list(task.path)
    if e > a:
        path.append((0, (e - a) / (c - a), 1))
        a = e
    if g < c:
        path.append((0, (g - a) / (c - a), 0))
    if f > b:
        path.append((1, (f - b) / (d - b), 1))
        b = f
    if h < d:
        path.append((1, (h - b) / (d - b), 0))
    return tuple(path)


def _run(
    state, policy, max_boundary_depth, use_multiple, use_newton=True, cofinal=False
):
    """Advance a checked joint divisor frontier within one invocation budget.

    Each accepted cell accounts for numerator, denominator and source guards.
    Checkpoints are emitted only after the ledger and pending queue agree."""

    p = replace(state.proof, exhaustion=None)
    cells, unresolved = list(p.cells), list(p.unresolved)
    tasks, blocked = deque(state.pending), []
    used, outer = 0, p.outer
    count_failure = "cell-budget"
    refinements = list(p.refinements)
    limit, quota = policy.max_cells, policy.max_cells
    local_policy, boundary_limit = policy, max_boundary_depth

    def snapshot(exhaustion=None):
        proof = replace(
            p,
            outer=outer,
            cells=tuple(cells),
            unresolved=tuple(unresolved),
            exhaustion=exhaustion,
            refinements=tuple(refinements),
        )
        if proof.complete:
            proof = replace(proof, exhaustion=None)
        wanted = set(proof.unresolved) | {
            c.rectangle for c in cells if _needs_work(proof, c)
        }
        pending = tuple(t for t in (*tasks, *blocked) if t.rectangle in wanted)
        return QuotientIsolationState(
            proof, pending, state.tested + used, state.generation + 1
        )

    def checkpoint():
        if (sink := checkpoint_sink()) is not None:
            sink(snapshot())

    def count(f, r):
        nonlocal used, count_failure
        if used >= limit:
            count_failure = "cell-budget"
            return None
        c = certify_analytic_contour(
            f,
            p.variable,
            r.lower_left,
            r.upper_right,
            policy=replace(
                local_policy,
                seconds=None,
                max_cells=min(quota, limit - used),
                max_depth=boundary_limit,
            ),
        )
        used += c.tested
        if not c.complete:
            count_failure = (
                "cell-budget"
                if "cell-budget" in c.obligations
                else "depth-budget"
                if any("depth-budget" in reason for reason in c.obligations)
                else "boundary-obligation"
            )
        return c if c.complete else None

    if not outer:
        if used >= policy.max_cells:
            return snapshot("cell-budget")
        p = replace(p, source=_source(p.expression, p.variable, cancel=True))
        used += 1
        cs, cache = [], {}
        for f in (p.source.numerator, p.source.denominator, *p.source.guards):
            if f not in cache:
                cache[f] = count(f, p.rectangle)
            if cache[f] is None:
                return snapshot(count_failure)
            cs.append(cache[f])
        outer = tuple(cs)
        unresolved.clear()
        cells.append(QuotientCellProof(cs[0], cs[1]))
        checkpoint()

    def locate(r):
        nonlocal used
        m = r.zero_count
        if (
            m < 1
            or (m > 1 and not use_multiple)
            or m > policy.max_taylor_order + 1
            or sp.count_ops(r.expression) > 512
        ):
            return None
        a, b, u, v = r.rectangle.bounds()
        for center in dict.fromkeys((sp.S.Zero, (a + u) / 2 + sp.I * (b + v) / 2)):
            if used >= limit:
                break
            used += 1
            loc = ExactLocalZeroProof(
                r,
                center,
                tuple(
                    differentiate(r.expression, p.variable, k).subs(p.variable, center)
                    for k in range(m)
                ),
            )
            if loc.verify():
                return loc
        return None

    def enrich(cell):
        nonlocal used
        n, d = cell.numerator, cell.denominator
        if use_multiple:
            for is_n, r in ((True, n), (False, d)):
                if r.zero_count > 1 and not _individual(r) and used < limit:
                    q, spent = _propose_multiple(
                        r,
                        replace(
                            local_policy,
                            seconds=None,
                            max_cells=limit - used,
                            max_depth=boundary_limit,
                        ),
                    )
                    used += spent
                    if q is not None:
                        if is_n:
                            n = q
                        else:
                            d = q
        # A stronger count record proves the same local theorem. Keep existing
        # exact locations bound to that record when a resumed query upgrades it.
        cell = replace(
            cell,
            numerator=n,
            denominator=d,
            numerator_location=(
                replace(cell.numerator_location, region=n)
                if cell.numerator_location is not None
                else None
            ),
            denominator_location=(
                replace(cell.denominator_location, region=d)
                if cell.denominator_location is not None
                else None
            ),
        )
        nl = cell.numerator_location or (locate(n) if n.zero_count else None)
        dl = cell.denominator_location or (
            locate(d) if d.zero_count and n.zero_count else None
        )
        cell = replace(cell, numerator_location=nl, denominator_location=dl)
        if n.zero_count and (
            (d.zero_count and _cell_data(p.source, cell) is None)
            or (d.zero_count == 0 and not cell.guard_zero and not cell.excluded_guard)
        ):
            bases = []
            for r in (n, d):
                b = shared_base(r)
                if b is not None and not any(same_base(b, a) for a in bases):
                    bases.append(b)
            hints = tuple(
                dict.fromkeys(
                    (
                        *p.source.guards,
                        *(
                            node.args[0]
                            for f in (n.expression, d.expression)
                            for node in sp.preorder_traversal(f)
                            if node.func
                            in (
                                sp.sin,
                                sp.cos,
                                sp.sinh,
                                sp.cosh,
                                sp.exp,
                                sp.erf,
                                sp.erfc,
                            )
                            and node.args[0].has(p.variable)
                        ),
                    )
                )
            )
            # Try existing count-one bases before any new contour proposals.
            for hint in (None, *hints):
                if hint is not None:
                    if used >= limit:
                        break
                    if any(b.expression == hint for b in bases):
                        continue
                    b = next(
                        (
                            c
                            for c in outer
                            if c.expression == hint and c.rectangle == cell.rectangle
                        ),
                        None,
                    )
                    if b is None:
                        b = count(hint, cell.rectangle)
                    if b is None or b.zero_count != 1:
                        continue
                    bases.append(b)
                for base in bases:
                    records = []
                    for r in (n, d):
                        if not r.zero_count:
                            records.append(r)
                            continue
                        if used >= limit or (r.zero_count > 1 and not use_multiple):
                            break
                        used += 1
                        w = _propose_implication(
                            r.expression,
                            base,
                            r.zero_count,
                            max_order=policy.max_taylor_order + 1,
                        )
                        if w is None:
                            break
                        q = SharedZeroOrderProof(r, w)
                        if not q.verify():
                            break
                        records.append(q)
                    if len(records) != 2:
                        continue
                    nn, dd = records
                    if dd.zero_count:
                        n, d = nn, dd
                        cell = replace(
                            cell,
                            numerator=n,
                            denominator=d,
                            numerator_location=replace(nl, region=n) if nl else None,
                            denominator_location=replace(dl, region=d) if dl else None,
                        )
                        return cell
                    for g in p.source.guards:
                        if used >= limit:
                            break
                        used += 1
                        w = _propose_implication(g, base, 1)
                        if w is not None:
                            return replace(
                                cell,
                                numerator=nn,
                                numerator_location=replace(nl, region=nn)
                                if nl
                                else None,
                                guard_zero=w,
                                exclusions=(),
                            )
                if (
                    hint is None
                    and d.zero_count == 0
                    and all(c.zero_count == 0 for c in outer[2:])
                ):
                    break
        if n.zero_count and d.zero_count == 0:
            ex = []
            for g, global_c in zip(p.source.guards, outer[2:], strict=True):
                c = (
                    global_c
                    if global_c.zero_count == 0
                    else next(
                        (
                            q
                            for q in (n, d)
                            if q.expression == g
                            and q.zero_count == 0
                            and type(q) is AnalyticContourCertificate
                        ),
                        None,
                    )
                )
                if c is None:
                    c = count(g, cell.rectangle)
                if c is not None and c.zero_count == 0:
                    ex.append(
                        DenominatorExclusionProof(g, p.variable, cell.rectangle, c)
                    )
                    continue
                if nl is not None and g.subs(p.variable, nl.center) == 0:
                    return replace(cell, exclusions=(), excluded_guard=g)
                if (
                    used < limit
                    and sp.count_ops(g) + sp.count_ops(p.source.numerator) <= 512
                ):
                    used += 1
                    try:
                        h = sp.cancel(g / p.source.numerator)
                        if (
                            entire_source(h, p.variable)
                            and sp.expand(g - p.source.numerator * h) == 0
                        ):
                            return replace(
                                cell, exclusions=(), excluded_guard=g, guard_cofactor=h
                            )
                    except _ERRORS:
                        pass
                return replace(cell, exclusions=())
            cell = replace(cell, exclusions=tuple(ex))
        return cell

    while tasks and used < policy.max_cells:
        t = tasks.popleft()
        candidate, effort = _dovetail(t.attempt) if cofinal else (t.attempt, 0)
        quota = 64 * (effort + 1) ** 2 if cofinal else policy.max_cells
        if cofinal and policy.max_cells - used < 8 * quota + 1:
            tasks.appendleft(t)
            break
        used += 1
        limit = policy.max_cells
        local_policy = (
            replace(policy, max_refinements=min(policy.max_refinements, effort))
            if cofinal
            else policy
        )
        boundary_limit = (
            min(max_boundary_depth, 14 + effort) if cofinal else max_boundary_depth
        )
        cell = next((c for c in cells if c.rectangle == t.rectangle), None)
        if cell is None:
            n, d = (
                count(p.source.numerator, t.rectangle),
                count(p.source.denominator, t.rectangle),
            )
            if n is None or d is None:
                tasks.append(replace(t, attempt=t.attempt + 1))
                checkpoint()
                continue
            unresolved.remove(t.rectangle)
            cell = QuotientCellProof(n, d)
            cells.append(cell)
        limit = min(policy.max_cells, used + quota) if cofinal else policy.max_cells
        enriched = enrich(cell)
        limit = policy.max_cells
        cells[cells.index(cell)] = enriched
        cell = enriched
        if not _needs_work(p, cell):
            checkpoint()
            continue
        if t.depth >= policy.max_depth:
            blocked.append(t)
            checkpoint()
            continue
        if use_newton and t.attempt % 4 == 0 and t.depth + 4 <= policy.max_depth:
            from .quotient_refinement import _propose_quotient_refinement

            def refine_count(
                f, r, cap, local_policy=local_policy, boundary_limit=boundary_limit
            ):
                if cap < 1:
                    return None, 0
                c = certify_analytic_contour(
                    f,
                    p.variable,
                    r.lower_left,
                    r.upper_right,
                    policy=replace(
                        local_policy,
                        max_cells=cap,
                        max_depth=boundary_limit,
                        seconds=None,
                    ),
                )
                return (c if c.complete else None), c.tested

            refinement, spent = _propose_quotient_refinement(
                p.source,
                cell,
                outer[2:],
                replace(
                    local_policy,
                    max_cells=min(quota, policy.max_cells - used),
                    seconds=None,
                ),
                refine_count,
                p.max_box_width,
                p.max_box_diameter,
            )
            used += spent
            if refinement is not None:
                refinements.append(refinement)
                cells.remove(cell)
                cells.extend(refinement.cells)
                tasks.extend(
                    ComplexIsolationTask(c.rectangle, _rectangle_path(t, c.rectangle))
                    for c in refinement.cells
                    if _needs_work(p, c)
                )
                checkpoint()
                continue
        axis, ratio = _split_choice(t.rectangle, candidate)
        boxes = _children(t.rectangle, axis, ratio)
        from .quotient_refinement import _source_evidence, _transfer

        proposed, cache = [], {}
        for r in boxes:
            records = []
            for component in (cell.numerator, cell.denominator):
                base = shared_base(component)
                if component.zero_count == 0:
                    from .shared_zeros import ComplexZeroSubsetProof

                    q = ComplexZeroSubsetProof(component, r)
                else:
                    f = component.expression if base is None else base.expression
                    key = (f, r)
                    if key not in cache:
                        cache[key] = count(f, r)
                    b = cache[key]
                    q = (
                        b
                        if base is None or b is None
                        else _transfer(component, base, b)
                    )
                if q is None:
                    break
                records.append(q)
            if len(records) != 2:
                break
            proposed.append(_source_evidence(p.source, cell, *records))
        if (
            len(proposed) == 2
            and sum(c.numerator.zero_count for c in proposed)
            == cell.numerator.zero_count
            and sum(c.denominator.zero_count for c in proposed)
            == cell.denominator.zero_count
        ):
            cells.remove(cell)
            cells.extend(proposed)
            tasks.extend(
                ComplexIsolationTask(r, (*t.path, (axis, ratio, side)))
                for side, r in enumerate(boxes)
            )
        else:
            tasks.append(replace(t, attempt=t.attempt + 1))
        checkpoint()
    result = snapshot("cell-budget" if tasks else "depth-budget" if blocked else None)
    return result


def certify_quotient_isolation(
    expr,
    var,
    lower_left,
    upper_right,
    *,
    max_box_width=None,
    max_box_diameter=None,
    policy=None,
    max_boundary_depth=14,
    use_multiple=True,
    use_newton=True,
):
    """Certify quotient zeros and poles, retaining every raw inverse-base hole."""
    policy = EnclosurePolicy() if policy is None else policy
    if (
        type(use_multiple) is not bool
        or type(use_newton) is not bool
        or type(max_boundary_depth) is not int
        or max_boundary_depth < 0
    ):
        raise ValueError("invalid quotient isolation mode or boundary depth")
    seed = _seed(expr, var, lower_left, upper_right, max_box_width, max_box_diameter)
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_quotient_isolation",
            expr,
            (var, lower_left, upper_right),
            {
                "max_box_width": max_box_width,
                "max_box_diameter": max_box_diameter,
                "policy": replace(policy, seconds=None),
                "max_boundary_depth": max_boundary_depth,
                "use_multiple": use_multiple,
                "use_newton": use_newton,
            },
            policy.seconds,
        )
    return _run(
        seed,
        policy,
        max_boundary_depth,
        use_multiple,
        use_newton,
    )


def resume_quotient_isolation(
    state, *, policy=None, max_boundary_depth=14, use_multiple=True, use_newton=True
):
    """Validate a joint zero/pole checkpoint and continue its pending frontier."""

    state = getattr(state, "state", state)
    if type(state) is not QuotientIsolationState:
        raise ValueError("invalid quotient isolation checkpoint")
    policy = EnclosurePolicy() if policy is None else policy
    if (
        type(use_multiple) is not bool
        or type(use_newton) is not bool
        or type(max_boundary_depth) is not int
        or max_boundary_depth < 0
    ):
        raise ValueError("invalid quotient isolation mode or boundary depth")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "resume_quotient_isolation",
            state,
            (),
            {
                "policy": replace(policy, seconds=None),
                "max_boundary_depth": max_boundary_depth,
                "use_multiple": use_multiple,
                "use_newton": use_newton,
            },
            policy.seconds,
        )
    if not state.verify():
        raise ValueError("invalid quotient isolation checkpoint")
    return _run(state, policy, max_boundary_depth, use_multiple, use_newton)
