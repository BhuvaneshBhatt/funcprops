"""Entire rectangle counts by certified boundary homotopy and exact winding.

Replay uses only the outward primitive and rational geometry, never the contour
search. Positive counts include multiplicity; they do not locate real roots.
"""

from dataclasses import dataclass, replace

import sympy as sp

from .complex_coverage import CoverageRectangle, _partition
from .complex_interval import complex_box_evaluate, entire_source, valid_box
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy

_ERRORS = (AttributeError, TypeError, ValueError, ArithmeticError, NotImplementedError)


def _inside(point, box):
    a, b, c, d = box
    return a <= sp.re(point) <= c and b <= sp.im(point) <= d


def _clear(box):
    a, b, c, d = box
    return a > 0 or c < 0 or b > 0 or d < 0


def _point(rectangle, t):
    a, b, c, d = rectangle.bounds()
    corners = (a + b * sp.I, c + b * sp.I, c + d * sp.I, a + d * sp.I, a + b * sp.I)
    side = min(int(sp.floor(t)), 3)
    return corners[side] + (t - side) * (corners[side + 1] - corners[side])


def _segment_box(rectangle, start, end):
    p, q = _point(rectangle, start), _point(rectangle, end)
    return (
        min(sp.re(p), sp.re(q)),
        min(sp.im(p), sp.im(q)),
        max(sp.re(p), sp.re(q)),
        max(sp.im(p), sp.im(q)),
    )


def _winding(vertices):
    count = 0
    for p, q in zip(vertices, vertices[1:] + vertices[:1], strict=True):
        x, y, u, v = sp.re(p), sp.im(p), sp.re(q), sp.im(q)
        cross = x * v - u * y
        if y <= 0 < v and cross > 0:
            count += 1
        elif v <= 0 < y and cross < 0:
            count -= 1
    return count


@dataclass(frozen=True)
class ComplexBoxWitness:
    """Enclose an entire function's image on a complex boundary segment."""

    expression: sp.Expr
    variable: sp.Symbol
    box: tuple
    bounds: tuple
    precision: int
    max_series_terms: int = 4096
    schema_version: int = 1

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self) is not ComplexBoxWitness
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or not valid_box(self.bounds)
            ):
                return False
            actual = complex_box_evaluate(
                self.expression,
                self.variable,
                self.box,
                precision=self.precision,
                max_series_terms=self.max_series_terms,
            )
            return (
                actual is not None
                and _inside(actual[0] + sp.I * actual[1], self.bounds)
                and _inside(actual[2] + sp.I * actual[3], self.bounds)
            )
        except _ERRORS:
            return False

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()


@dataclass(frozen=True)
class AnalyticContourCertificate:
    """Bind an entire-function winding count to a rectangle and image witnesses."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    knots: tuple = (sp.S.Zero, sp.S.One, sp.Integer(2), sp.Integer(3), sp.Integer(4))
    images: tuple = (None, None, None, None)
    vertices: tuple = ()
    zero_count: int | None = None
    obligations: tuple = ()
    tested: int = 0
    schema_version: int = 1

    @property
    def complete(self):
        return self.zero_count is not None and not self.obligations

    @property
    def multiplicity_count(self):
        return self.zero_count

    @property
    def root_count(self):
        return 0 if self.zero_count == 0 else None

    @property
    def distinct_root_count(self):
        return self.root_count

    @property
    def individual_multiplicities(self):
        return () if self.zero_count == 0 else None

    @property
    def real_root_count(self):
        return 0 if self.zero_count == 0 else None

    @property
    def scope(self):
        return "entire-rectangle-count-with-multiplicity"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_analytic_contour(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def certified(self):
        return self.verify()


def _header(c):
    z, f = c.variable, c.expression
    return (
        type(c.schema_version) is int
        and c.schema_version == 1
        and isinstance(z, sp.Symbol)
        and z.assumptions0 == {"commutative": True}
        and c.coordinate_assumptions == tuple(sorted(z.assumptions0.items()))
        and c.source_syntax == sp.srepr(f)
        and not f.free_symbols - {z}
        and not f.has(sp.Float)
        and type(c.rectangle) is CoverageRectangle
        and c.rectangle.valid()
    )


def check_analytic_contour(c):
    """Check the stored analytic contour premises and report their replay outcome."""

    reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-contour-premise")
    try:
        if type(c) is not AnalyticContourCertificate:
            return reject
        if type(c.schema_version) is not int or c.schema_version != 1:
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "unsupported-contour-schema"
            )
        if (
            not _header(c)
            or not isinstance(c.knots, tuple)
            or not isinstance(c.images, tuple)
            or not isinstance(c.vertices, tuple)
            or not isinstance(c.obligations, tuple)
        ):
            return reject
        if not entire_source(c.expression, c.variable):
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED,
                    None,
                    False,
                    "unsupported-entire-source-grammar",
                )
                if not c.complete and c.zero_count is None
                else reject
            )
        if (
            type(c.tested) is not int
            or c.tested < 0
            or len(c.knots) != len(c.images) + 1
            or len(c.knots) < 5
            or c.knots[0] != 0
            or c.knots[-1] != 4
            or not {sp.Integer(i) for i in range(5)}.issubset(c.knots)
        ):
            return reject
        for i, (a, b) in enumerate(zip(c.knots, c.knots[1:], strict=False)):
            if (
                not isinstance(a, sp.Rational)
                or not isinstance(b, sp.Rational)
                or not 0 <= a < b <= 4
                or sp.ceiling(b) - sp.floor(a) != 1
            ):
                return reject
            w = c.images[i]
            if w is not None and (
                type(w) is not ComplexBoxWitness
                or w.expression != c.expression
                or w.variable != c.variable
                or w.box != _segment_box(c.rectangle, a, b)
                or not w.verify()
                or not _clear(w.bounds)
            ):
                return reject
        if c.zero_count is None:
            if not c.obligations or c.vertices:
                return reject
            return CheckResult(
                CheckOutcome.EXHAUSTED
                if any("budget" in a for a in c.obligations)
                else CheckOutcome.LOCAL_VALID,
                True,
                False,
                "; ".join(c.obligations),
            )
        if (
            type(c.zero_count) is not int
            or c.zero_count < 0
            or c.obligations
            or any(w is None for w in c.images)
            or len(c.vertices) != len(c.images)
        ):
            return reject
        for i, w in enumerate(c.images):
            for point in (c.vertices[i], c.vertices[(i + 1) % len(c.vertices)]):
                if (
                    not isinstance(sp.re(point), sp.Rational)
                    or not isinstance(sp.im(point), sp.Rational)
                    or not _inside(point, w.bounds)
                ):
                    return reject
        if _winding(c.vertices) != c.zero_count:
            return reject
        return CheckResult(CheckOutcome.COMPLETE, True, True)
    except _ERRORS:
        return reject


def _seed(expr, var, lower_left, upper_right, reason):
    f, z, lo, hi = map(sp.sympify, (expr, var, lower_left, upper_right))
    return AnalyticContourCertificate(
        f,
        z,
        CoverageRectangle(lo, hi),
        sp.srepr(f),
        tuple(sorted(z.assumptions0.items())) if isinstance(z, sp.Symbol) else (),
        obligations=(reason,),
    )


def certify_analytic_contour(expr, var, lower_left, upper_right, *, policy=None):
    """Certify an entire function's zero count inside a rational rectangle."""
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_analytic_contour",
            expr,
            (var, lower_left, upper_right),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    c = _seed(expr, var, lower_left, upper_right, "unresolved-boundary")
    if not _header(c) or not entire_source(c.expression, c.variable):
        return replace(c, obligations=("unsupported-entire-source-or-geometry",))
    tasks = [(sp.Integer(i), sp.Integer(i + 1), 0) for i in range(4)]
    done, tested = [], 0
    while tasks:
        a, b, depth = tasks.pop(0)
        found = None
        box = _segment_box(c.rectangle, a, b)
        for precision in policy.precisions:
            if tested >= policy.max_cells:
                break
            tested += 1
            bounds = complex_box_evaluate(
                c.expression,
                c.variable,
                box,
                precision=precision,
                max_series_terms=policy.max_series_terms,
            )
            if bounds is not None and _clear(bounds):
                found = ComplexBoxWitness(
                    c.expression,
                    c.variable,
                    box,
                    bounds,
                    precision,
                    policy.max_series_terms,
                )
                break
        if found is not None or depth >= policy.max_depth or tested >= policy.max_cells:
            done.append((a, b, found))
        else:
            mid = (a + b) / 2
            tasks.extend(((a, mid, depth + 1), (mid, b, depth + 1)))
    done.sort(key=lambda a: a[0])
    c = replace(
        c,
        knots=(*tuple(a[0] for a in done), sp.Integer(4)),
        images=tuple(a[2] for a in done),
        tested=tested,
    )
    if any(w is None for w in c.images):
        return replace(
            c,
            obligations=(
                "cell-budget"
                if tested >= policy.max_cells
                else "depth-budget-or-boundary-zero",
            ),
        )
    # Choose a common rational polygon vertex inside the intersection of both
    # adjacent image boxes. The true image of their shared endpoint lies there.
    vertices = []
    for i, w in enumerate(c.images):
        prev = c.images[i - 1]
        a, b = max(w.bounds[0], prev.bounds[0]), max(w.bounds[1], prev.bounds[1])
        d, e = min(w.bounds[2], prev.bounds[2]), min(w.bounds[3], prev.bounds[3])
        if a > d or b > e:
            return replace(c, obligations=("unresolved-shared-image",))
        vertices.append((a + d) / 2 + sp.I * (b + e) / 2)
    vertices = tuple(vertices)
    candidate = replace(
        c, vertices=vertices, zero_count=_winding(vertices), obligations=()
    )
    return (
        candidate
        if candidate.verify()
        else replace(c, obligations=("unresolved-winding",))
    )


@dataclass(frozen=True)
class AnalyticComplexCoverage:
    """Assemble certified contour counts over an exact complex rectangle cover."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    regions: tuple = ()
    unresolved: tuple = ()
    complete: bool = False
    multiplicity_count: int | None = None
    tested: int = 0
    schema_version: int = 1
    exhaustion: str | None = None

    @property
    def distinct_root_count(self):
        return self.root_count

    @property
    def real_root_count(self):
        return 0 if self.multiplicity_count == 0 else None

    @property
    def individual_multiplicities(self):
        return () if self.multiplicity_count == 0 else None

    @property
    def source_syntax(self):
        return sp.srepr(self.expression)

    @property
    def coordinate_assumptions(self):
        return tuple(sorted(self.variable.assumptions0.items()))

    @property
    def root_count(self):
        return 0 if self.multiplicity_count == 0 else None

    @property
    def scope(self):
        return "entire-rectangle-coverage-with-multiplicity"

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-complex-cover")
        try:
            if type(self) is not AnalyticComplexCoverage:
                return reject
            if type(self.schema_version) is not int or self.schema_version != 1:
                return CheckResult(
                    CheckOutcome.UNSUPPORTED, None, False, "unsupported-contour-schema"
                )
            if (
                not _header(self)
                or not isinstance(self.regions, tuple)
                or not isinstance(self.unresolved, tuple)
                or type(self.complete) is not bool
                or type(self.tested) is not int
                or self.tested < 0
                or self.exhaustion
                not in (None, "cell-budget", "wall-budget", "depth-budget")
            ):
                return reject
            if not entire_source(self.expression, self.variable):
                return (
                    CheckResult(
                        CheckOutcome.UNSUPPORTED,
                        None,
                        False,
                        "unsupported-entire-source-grammar",
                    )
                    if not self.complete and self.multiplicity_count is None
                    else reject
                )
            if not _partition(
                self.rectangle,
                tuple(r.rectangle for r in self.regions) + self.unresolved,
            ):
                return reject
            if any(
                type(r) is not AnalyticContourCertificate
                or r.expression != self.expression
                or r.variable != self.variable
                or not r.complete
                or not r.verify()
                for r in self.regions
            ):
                return reject
            complete = not self.unresolved
            count = sum(r.zero_count for r in self.regions) if complete else None
            if (
                self.complete is not complete
                or self.multiplicity_count != count
                or (count is not None and type(self.multiplicity_count) is not int)
            ):
                return reject
            return CheckResult(
                CheckOutcome.COMPLETE
                if complete
                else CheckOutcome.EXHAUSTED
                if self.exhaustion
                else CheckOutcome.LOCAL_VALID,
                True,
                complete,
            )
        except _ERRORS:
            return reject


def analytic_complex_coverage(expr, var, lower_left, upper_right, *, policy=None):
    """Subdivide rectangles with unproved contours; every counted seam is clear."""
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "analytic_complex_coverage",
            expr,
            (var, lower_left, upper_right),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    seed = _seed(expr, var, lower_left, upper_right, "unresolved-boundary")
    tasks, leaves, pending, tested = [(seed.rectangle, 0)], [], [], 0
    while tasks:
        box, depth = tasks.pop(0)
        if (
            tested >= policy.max_cells
            or not _header(seed)
            or not entire_source(seed.expression, seed.variable)
        ):
            pending.append(box)
            continue
        c = certify_analytic_contour(
            seed.expression,
            seed.variable,
            box.lower_left,
            box.upper_right,
            policy=replace(policy, max_cells=policy.max_cells - tested),
        )
        tested += c.tested
        if c.complete:
            leaves.append(c)
        elif depth >= policy.max_depth or tested >= policy.max_cells:
            pending.append(box)
        else:
            a, b, d, e = box.bounds()
            if d - a >= e - b:
                mid = (a + d) / 2
                boxes = (
                    CoverageRectangle(a + b * sp.I, mid + e * sp.I),
                    CoverageRectangle(mid + b * sp.I, d + e * sp.I),
                )
            else:
                mid = (b + e) / 2
                boxes = (
                    CoverageRectangle(a + b * sp.I, d + mid * sp.I),
                    CoverageRectangle(a + mid * sp.I, d + e * sp.I),
                )
            tasks.extend((v, depth + 1) for v in boxes)
    complete = not pending
    return AnalyticComplexCoverage(
        seed.expression,
        seed.variable,
        seed.rectangle,
        tuple(leaves),
        tuple(pending),
        complete,
        sum(c.zero_count for c in leaves) if complete else None,
        tested,
        exhaustion=None
        if complete
        else "cell-budget"
        if tested >= policy.max_cells
        else "depth-budget",
    )
