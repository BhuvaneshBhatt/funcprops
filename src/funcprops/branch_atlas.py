"""Finite logarithm charts, exact overlap transitions, and power gluing.

A chart proves Re(F/phase)>0 on a closed rational rectangle. It defines a
selected analytic logarithm on a neighborhood, including across the old
principal cut. A nonzero overlap transition is an obstruction, not a global log.
"""

from collections import deque
from dataclasses import dataclass, replace
from itertools import combinations, pairwise

import sympy as sp

from .analytic_contours import ComplexBoxWitness, _header
from .complex_coverage import CoverageRectangle
from .complex_interval import complex_box_evaluate, entire_source
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy

_PHASES = (sp.S.One, sp.I, -sp.S.One, -sp.I)
_ERRORS = (AttributeError, TypeError, ValueError, ArithmeticError, NotImplementedError)


def _overlap(a, b):
    x, y, u, v = a.bounds()
    p, q, r, s = b.bounds()
    return max(x, p) <= min(u, r) and max(y, q) <= min(v, s)


def _positive_projection(bounds, phase):
    a, b, c, d = bounds
    return (a, b, -c, -d)[phase] > 0


def _turn(a, b):
    # Principal argument centers in units of pi/2; -I uses -pi/2.
    pa, pb = (0, 1, 2, -1)[a.phase], (0, 1, 2, -1)[b.phase]
    center = sp.Rational(pb - pa, 4) + b.sheet - a.sheet
    low, high = sp.floor(center - sp.S.Half) + 1, sp.ceiling(center + sp.S.Half) - 1
    return int(low) if low == high else None


def _union_equal(left, right):
    all_rectangles = left + right
    if any(type(r) is not CoverageRectangle or not r.valid() for r in all_rectangles):
        return False
    xs = sorted({v for r in all_rectangles for v in (r.bounds()[0], r.bounds()[2])})
    ys = sorted({v for r in all_rectangles for v in (r.bounds()[1], r.bounds()[3])})
    xs += [(a + b) / 2 for a, b in pairwise(xs)]
    ys += [(a + b) / 2 for a, b in pairwise(ys)]

    def inside(rectangles, x, y):
        return any(
            a <= x <= c and b <= y <= d
            for a, b, c, d in (r.bounds() for r in rectangles)
        )

    return all(inside(left, x, y) == inside(right, x, y) for x in xs for y in ys)


class _Replay:
    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def certified(self):
        return self.verify()


@dataclass(frozen=True)
class LogBranchChart(_Replay):
    """Define a logarithm on a rectangle whose base image lies in a rotated half-plane."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    enclosure: ComplexBoxWitness
    phase: int
    sheet: int = 0
    schema_version: int = 1

    @property
    def source_syntax(self):
        return sp.srepr(self.expression)

    @property
    def coordinate_assumptions(self):
        return tuple(sorted(self.variable.assumptions0.items()))

    @property
    def logarithm(self):
        a = _PHASES[self.phase]
        return sp.log(self.expression / a) + sp.log(a) + 2 * sp.pi * sp.I * self.sheet

    @property
    def complete(self):
        return True

    @property
    def scope(self):
        return "selected-holomorphic-logarithm-on-rectangle-neighborhood"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        try:
            w = self.enclosure
            valid = (
                type(self) is LogBranchChart
                and _header(self)
                and type(self.phase) is int
                and 0 <= self.phase < 4
                and type(self.sheet) is int
                and entire_source(self.expression, self.variable)
                and type(w) is ComplexBoxWitness
                and w.expression == self.expression
                and w.variable == self.variable
                and w.box == self.rectangle.bounds()
                and w.verify()
                and _positive_projection(w.bounds, self.phase)
            )
            return CheckResult(
                CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
                bool(valid),
                bool(valid),
                None if valid else "false-log-chart",
            )
        except _ERRORS:
            return CheckResult(CheckOutcome.REJECTED, False, False, "false-log-chart")


@dataclass(frozen=True)
class LogChartTransition:
    """Record the exact integer sheet difference on a chart overlap."""

    left: int
    right: int
    turns: int


@dataclass(frozen=True)
class LogAtlasProof(_Replay):
    """Check rectangle coverage, overlap transitions and logarithm gluing obstructions."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: tuple
    charts: tuple
    transitions: tuple
    unresolved: tuple = ()
    tested: int = 0
    exhaustion: str | None = None
    schema_version: int = 1

    @property
    def coverage_complete(self):
        return bool(self.charts) and not self.unresolved

    @property
    def gluing_complete(self):
        return self.coverage_complete and all(t.turns == 0 for t in self.transitions)

    @property
    def complete(self):
        return self.gluing_complete

    @property
    def obstructions(self):
        return tuple(t for t in self.transitions if t.turns)

    @property
    def scope(self):
        return "finite-log-chart-cover-with-checked-overlap-transitions"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-log-atlas")
        try:
            f, z = self.expression, self.variable
            if (
                type(self) is not LogAtlasProof
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or not isinstance(z, sp.Symbol)
                or z.assumptions0 != {"commutative": True}
                or f.free_symbols - {z}
                or f.has(sp.Float)
                or not entire_source(f, z)
                or any(
                    type(v) is not tuple
                    for v in (
                        self.requested,
                        self.charts,
                        self.transitions,
                        self.unresolved,
                    )
                )
                or not self.requested
                or type(self.tested) is not int
                or self.tested < 0
                or self.exhaustion not in (None, "cell-budget", "depth-budget")
            ):
                return reject
            if any(
                type(c) is not LogBranchChart
                or c.expression != f
                or c.variable != z
                or not c.verify()
                for c in self.charts
            ):
                return reject
            rectangles = tuple(c.rectangle for c in self.charts)
            if len(set(rectangles)) != len(rectangles) or not _union_equal(
                self.requested, rectangles + self.unresolved
            ):
                return reject
            expected = _transitions(self.charts)
            if expected is None or any(
                type(t) is not LogChartTransition
                or any(type(k) is not int for k in (t.left, t.right, t.turns))
                for t in self.transitions
            ):
                return reject
            if self.transitions != expected:
                return reject
            return CheckResult(
                CheckOutcome.COMPLETE if self.complete else CheckOutcome.LOCAL_VALID,
                True,
                self.complete,
                "nontrivial-log-transition" if self.obstructions else self.exhaustion,
            )
        except _ERRORS:
            return reject


@dataclass(frozen=True)
class GluedPowerProof(_Replay):
    """Bind a selected power to compatible logarithm-chart transitions."""

    atlas: LogAtlasProof
    exponent: sp.Expr
    schema_version: int = 1

    @property
    def expression(self):
        return sp.Pow(self.atlas.expression, self.exponent, evaluate=False)

    @property
    def variable(self):
        return self.atlas.variable

    @property
    def multipliers(self):
        return tuple(
            sp.simplify(sp.exp(2 * sp.pi * sp.I * self.exponent * t.turns))
            for t in self.atlas.transitions
        )

    @property
    def complete(self):
        return self.atlas.coverage_complete and all(m == 1 for m in self.multipliers)

    @property
    def scope(self):
        return "selected-power-chart-gluing-not-principal-power-identity"

    def branch(self, index):
        return sp.exp(self.exponent * self.atlas.charts[index].logarithm)

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        try:
            valid = (
                type(self) is GluedPowerProof
                and type(self.schema_version) is int
                and self.schema_version == 1
                and type(self.atlas) is LogAtlasProof
                and self.atlas.verify()
                and isinstance(self.exponent, sp.Expr)
                and not self.exponent.free_symbols
                and not self.exponent.has(sp.Float)
                and self.exponent.is_finite is True
            )
            return CheckResult(
                CheckOutcome.COMPLETE
                if valid and self.complete
                else CheckOutcome.LOCAL_VALID
                if valid
                else CheckOutcome.REJECTED,
                valid,
                bool(valid and self.complete),
                None
                if valid and self.complete
                else "power-transition-obstruction"
                if valid
                else "false-power-atlas",
            )
        except _ERRORS:
            return CheckResult(CheckOutcome.REJECTED, False, False, "false-power-atlas")


def _transitions(charts):
    result = []
    for i, j in combinations(range(len(charts)), 2):
        if _overlap(charts[i].rectangle, charts[j].rectangle):
            n = _turn(charts[i], charts[j])
            if n is None:
                return None
            result.append(LogChartTransition(i, j, n))
    return tuple(result)


def glue_log_charts(
    charts,
    *,
    requested=None,
    normalize_sheets=True,
    unresolved=(),
    tested=0,
    exhaustion=None,
):
    """Check every shared boundary/overlap, retaining nontrivial transition cycles."""
    if (
        type(charts) is not tuple
        or not charts
        or any(type(c) is not LogBranchChart or not c.verify() for c in charts)
    ):
        raise ValueError("charts must be a nonempty tuple of checked logarithm charts")
    if normalize_sheets:
        sheets = {0: charts[0].sheet}
        for root in range(len(charts)):
            if root not in sheets:
                sheets[root] = charts[root].sheet
            queue = deque([root])
            while queue:
                i = queue.popleft()
                for j in range(len(charts)):
                    if j not in sheets and _overlap(
                        charts[i].rectangle, charts[j].rectangle
                    ):
                        n = _turn(
                            replace(charts[i], sheet=sheets[i]),
                            replace(charts[j], sheet=0),
                        )
                        if n is None:
                            raise ValueError("incompatible chart phases")
                        sheets[j] = -n
                        queue.append(j)
        charts = tuple(replace(c, sheet=sheets[i]) for i, c in enumerate(charts))
    proof = LogAtlasProof(
        charts[0].expression,
        charts[0].variable,
        tuple(c.rectangle for c in charts) if requested is None else requested,
        charts,
        _transitions(charts),
        unresolved,
        tested,
        exhaustion,
    )
    if not proof.verify():
        raise ValueError("invalid atlas assembly")
    return proof


def certify_log_atlas(expr, var, rectangles, *, policy=None):
    """Boundedly subdivide requested rectangles until half-plane charts are proved."""
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_log_atlas",
            expr,
            (var, rectangles),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    f, z = sp.sympify(expr), sp.sympify(var)
    if (
        type(rectangles) is not tuple
        or not rectangles
        or any(type(r) is not CoverageRectangle or not r.valid() for r in rectangles)
    ):
        raise ValueError("rectangles must be a nonempty exact rectangle tuple")
    if (
        not isinstance(z, sp.Symbol)
        or z.assumptions0 != {"commutative": True}
        or f.free_symbols - {z}
        or f.has(sp.Float)
        or not entire_source(f, z)
    ):
        raise ValueError("atlas bases require the parameter-free entire grammar")
    queue, charts, pending, tested = deque((r, 0) for r in rectangles), [], [], 0
    reason = None
    while queue:
        r, depth = queue.popleft()
        chart = None
        for precision in policy.precisions:
            if tested >= policy.max_cells:
                break
            tested += 1
            bounds = complex_box_evaluate(
                f,
                z,
                r.bounds(),
                precision=precision,
                max_series_terms=policy.max_series_terms,
            )
            if bounds is not None:
                for phase in range(4):
                    if _positive_projection(bounds, phase):
                        chart = LogBranchChart(
                            f,
                            z,
                            r,
                            ComplexBoxWitness(
                                f,
                                z,
                                r.bounds(),
                                bounds,
                                precision,
                                policy.max_series_terms,
                            ),
                            phase,
                        )
                        break
            if chart is not None:
                break
        if chart is not None:
            if r not in [c.rectangle for c in charts]:
                charts.append(chart)
        elif tested >= policy.max_cells or depth >= policy.max_depth:
            pending.append(r)
            reason = "cell-budget" if tested >= policy.max_cells else "depth-budget"
        else:
            a, b, c, d = r.bounds()
            if c - a >= d - b:
                m = (a + c) / 2
                children = (
                    CoverageRectangle(a + b * sp.I, m + d * sp.I),
                    CoverageRectangle(m + b * sp.I, c + d * sp.I),
                )
            else:
                m = (b + d) / 2
                children = (
                    CoverageRectangle(a + b * sp.I, c + m * sp.I),
                    CoverageRectangle(a + m * sp.I, c + d * sp.I),
                )
            queue.extend((s, depth + 1) for s in children)
    if not charts:
        return LogAtlasProof(f, z, rectangles, (), (), tuple(pending), tested, reason)
    return glue_log_charts(
        tuple(charts),
        requested=rectangles,
        unresolved=tuple(pending),
        tested=tested,
        exhaustion=reason,
    )
