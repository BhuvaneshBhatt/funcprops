"""Gluing certified holomorphic branch recipes for entire implicit relations.

Local formulas can combine several selected logarithms through entire functions
and arithmetic, with explicit exclusion proofs for supported denominators.
Overlap replay uses exact log transitions or a derivative identity and anchor.
"""

from dataclasses import dataclass
from itertools import combinations

import sympy as sp

from .analytic_contours import ComplexBoxWitness
from .branch_atlas import LogBranchChart, _overlap, _turn, _union_equal
from .complex_coverage import CoverageRectangle
from .complex_interval import ENTIRE_PRIMITIVES, entire_source
from .coverage_contract import CheckOutcome, CheckResult
from .exactness import certify_equal, certify_identity_equal, certify_zero
from .source_syntax import differentiate, finite_constant_source, same_data
from .work_budget import budgeted_operation

_ERRORS = (AttributeError, TypeError, ValueError, ArithmeticError, NotImplementedError)


def _entire_formula(f, symbols):
    if f in symbols:
        return True
    if not f.free_symbols:
        return not f.has(sp.Float) and finite_constant_source(f) and f.is_finite is True
    if f.is_Add or f.is_Mul:
        return all(_entire_formula(a, symbols) for a in f.args)
    if f.is_Pow:
        return (
            isinstance(f.exp, sp.Integer)
            and f.exp >= 0
            and _entire_formula(f.base, symbols)
        )
    return (
        f.func in ENTIRE_PRIMITIVES
        and len(f.args) == 1
        and _entire_formula(f.args[0], symbols)
    )


def _formula_units(f, symbols, z):
    """Find all nonconstant denominator bases that need a zero-exclusion witness."""
    units = []

    def visit(node):
        if node in symbols:
            return True
        if not node.free_symbols:
            return (
                not node.has(sp.Float)
                and finite_constant_source(node)
                and node.is_finite is True
            )
        if node.is_Add or node.is_Mul:
            return all(visit(a) for a in node.args)
        if node.is_Pow and isinstance(node.exp, sp.Integer):
            if not visit(node.base):
                return False
            if node.exp < 0 and node.base.func is not sp.exp:
                if not entire_source(node.base, z):
                    return False
                if node.base not in units:
                    units.append(node.base)
            return True
        return (
            node.func in ENTIRE_PRIMITIVES
            and len(node.args) == 1
            and visit(node.args[0])
        )

    return tuple(units) if visit(f) else None


def _clear(bounds):
    a, b, c, d = bounds
    return a > 0 or c < 0 or b > 0 or d < 0


@dataclass(frozen=True)
class HolomorphicBranchChart:
    """Select a holomorphic solution of an entire implicit relation on a rectangle."""

    relation: sp.Expr
    variable: sp.Symbol
    value_symbol: sp.Symbol
    rectangle: CoverageRectangle
    formula: sp.Expr
    logarithms: tuple = ()
    units: tuple = ()

    @property
    def expression(self):
        return self.relation

    @property
    def value(self):
        return self.formula.xreplace({u: c.logarithm for u, c in self.logarithms})

    @property
    def complete(self):
        return True

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "selected-holomorphic-solution-of-entire-implicit-relation"

    def verify(self):
        """Check local holomorphy, source definition and the exact implicit identity."""
        try:
            z, w = self.variable, self.value_symbol
            if (
                type(self) is not HolomorphicBranchChart
                or not isinstance(z, sp.Symbol)
                or not isinstance(w, sp.Symbol)
                or z == w
                or any(v.assumptions0 != {"commutative": True} for v in (z, w))
                or type(self.rectangle) is not CoverageRectangle
                or not self.rectangle.valid()
                or type(self.logarithms) is not tuple
                or type(self.units) is not tuple
                or not self.relation.has(w)
                or not _entire_formula(self.relation, {z, w})
            ):
                return False
            symbols = {z}
            for u, chart in self.logarithms:
                if (
                    not isinstance(u, sp.Symbol)
                    or u.assumptions0 != {"commutative": True}
                    or u in symbols
                    or u == w
                    or type(chart) is not LogBranchChart
                    or chart.variable != z
                    or chart.rectangle != self.rectangle
                    or not chart.verify()
                ):
                    return False
                symbols.add(u)
            bases = _formula_units(self.formula, symbols, z)
            if (
                bases is None
                or len(bases) != len(self.units)
                or any(
                    type(p) is not ComplexBoxWitness
                    or p.expression != base
                    or p.variable != z
                    or p.box != self.rectangle.bounds()
                    or not p.verify()
                    or not _clear(p.bounds)
                    for base, p in zip(bases, self.units, strict=True)
                )
            ):
                return False
            return certify_identity_equal(self.relation.subs(w, self.value), 0) is True
        except _ERRORS:
            return False


def _anchor(a, b):
    x, y, u, v = a.bounds()
    p, q, r, s = b.bounds()
    return (max(x, p) + min(u, r)) / 2 + sp.I * (max(y, q) + min(v, s)) / 2


def _transition_identity(left, right):
    """Compare local recipes after transferring equal logarithm bases exactly."""
    lmap = {}
    rmap = {}
    turns = []
    if len(left.logarithms) != len(right.logarithms):
        return None
    remaining = list(enumerate(right.logarithms))
    for i, (u, a) in enumerate(left.logarithms):
        matches = [(j, v, b) for j, (v, b) in remaining if a.expression == b.expression]
        if len(matches) != 1:
            return None
        j, v, b = matches[0]
        n = _turn(a, b)
        if n is None:
            return None
        t = sp.Dummy("log_coordinate")
        lmap[u] = t
        rmap[v] = t + 2 * sp.pi * sp.I * n
        turns.append((i, j, n))
        remaining = [r for r in remaining if r[0] != j]
    a = left.formula.xreplace(lmap)
    b = right.formula.xreplace(rmap)
    return tuple(turns) if certify_identity_equal(a, b) is True else None


def _derivative_identity(left, right, anchor):
    difference = differentiate(left.value, left.variable) - differentiate(
        right.value, right.variable
    )
    return (
        certify_identity_equal(difference, 0) is True
        and certify_equal(
            left.value.subs(left.variable, anchor),
            right.value.subs(right.variable, anchor),
        )
        is True
    )


@dataclass(frozen=True)
class BranchOverlapProof:
    """Prove equality or disagreement of two local germs, or retain an unresolved overlap."""

    left: int
    right: int
    anchor: sp.Expr
    status: str
    method: str
    turns: tuple = ()


def _overlap_valid(proof, charts):
    if (
        type(proof) is not BranchOverlapProof
        or type(proof.left) is not int
        or type(proof.right) is not int
        or not 0 <= proof.left < proof.right < len(charts)
        or type(proof.turns) is not tuple
    ):
        return False
    a, b = charts[proof.left], charts[proof.right]
    point = _anchor(a.rectangle, b.rectangle)
    if proof.anchor != point:
        return False
    if proof.status == "unresolved":
        return proof.method == "unresolved" and not proof.turns
    if proof.status == "different":
        return (
            proof.method == "anchor-disagreement"
            and not proof.turns
            and certify_zero(
                a.value.subs(a.variable, point) - b.value.subs(b.variable, point)
            )
            is False
        )
    if proof.status != "equal":
        return False
    if proof.method == "log-transitions":
        turns = _transition_identity(a, b)
        return turns is not None and same_data(proof.turns, turns)
    if proof.method == "derivative-anchor":
        return not proof.turns and _derivative_identity(a, b, point)
    return False


@dataclass(frozen=True)
class BranchGluingProof:
    """Cover a requested region and check every local-germ overlap for one relation."""

    relation: sp.Expr
    variable: sp.Symbol
    value_symbol: sp.Symbol
    requested: tuple
    charts: tuple
    overlaps: tuple
    unresolved: tuple = ()

    @property
    def expression(self):
        return self.relation

    @property
    def coverage_complete(self):
        return bool(self.charts) and not self.unresolved

    @property
    def gluing_complete(self):
        return self.coverage_complete and all(
            p.status == "equal" for p in self.overlaps
        )

    @property
    def complete(self):
        return self.gluing_complete

    @property
    def obstructions(self):
        return tuple(p for p in self.overlaps if p.status == "different")

    @property
    def unresolved_overlaps(self):
        return tuple(p for p in self.overlaps if p.status == "unresolved")

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "finite-certified-holomorphic-chart-gluing-for-an-entire-relation"

    def check(self):
        """Replay chart identities, rectangle coverage and every required overlap."""
        reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-branch-gluing")
        try:
            if (
                not isinstance(self.variable, sp.Symbol)
                or not isinstance(self.value_symbol, sp.Symbol)
                or self.variable == self.value_symbol
                or any(
                    v.assumptions0 != {"commutative": True}
                    for v in (self.variable, self.value_symbol)
                )
                or not self.relation.has(self.value_symbol)
                or not _entire_formula(
                    self.relation, {self.variable, self.value_symbol}
                )
                or type(self) is not BranchGluingProof
                or any(
                    type(v) is not tuple
                    for v in (
                        self.requested,
                        self.charts,
                        self.overlaps,
                        self.unresolved,
                    )
                )
                or not self.requested
                or any(
                    type(c) is not HolomorphicBranchChart
                    or c.relation != self.relation
                    or c.variable != self.variable
                    or c.value_symbol != self.value_symbol
                    or not c.verify()
                    for c in self.charts
                )
            ):
                return reject
            if len(set(self.charts)) != len(self.charts) or not _union_equal(
                self.requested,
                tuple(c.rectangle for c in self.charts) + self.unresolved,
            ):
                return reject
            pairs = tuple(
                (i, j)
                for i, j in combinations(range(len(self.charts)), 2)
                if _overlap(self.charts[i].rectangle, self.charts[j].rectangle)
            )
            if tuple((p.left, p.right) for p in self.overlaps) != pairs or any(
                not _overlap_valid(p, self.charts) for p in self.overlaps
            ):
                return reject
            return CheckResult(
                CheckOutcome.COMPLETE if self.complete else CheckOutcome.LOCAL_VALID,
                True,
                self.complete,
                "branch-disagreement"
                if self.obstructions
                else "unresolved-overlap-or-coverage"
                if not self.complete
                else None,
            )
        except _ERRORS:
            return reject

    def verify(self):
        """Return whether the chart gluing and any retained partial obligations replay."""
        return self.check().certified is True


@budgeted_operation
def certify_branch_chart(
    relation, variable, value_symbol, rectangle, formula, *, logarithms=(), units=()
):
    """Check a local explicit recipe as a branch of an entire implicit relation."""
    proof = HolomorphicBranchChart(
        sp.sympify(relation),
        sp.sympify(variable),
        sp.sympify(value_symbol),
        rectangle,
        sp.sympify(formula),
        tuple(logarithms),
        tuple(units),
    )
    if not proof.verify():
        raise ValueError("unproved local holomorphic branch recipe")
    return proof


@budgeted_operation
def glue_branch_charts(charts, *, requested=None, unresolved=()):
    """Glue arbitrary supported local branch recipes using certified overlaps.

    This assembles given charts; it does not discover arbitrary inverse branches
    or invent identities. Undecided overlaps and uncovered rectangles remain partial.
    """
    charts = tuple(charts)
    if not charts or any(
        type(c) is not HolomorphicBranchChart or not c.verify() for c in charts
    ):
        raise ValueError("checked branch charts are required")
    overlaps = []
    for i, j in combinations(range(len(charts)), 2):
        a, b = charts[i], charts[j]
        if not _overlap(a.rectangle, b.rectangle):
            continue
        point = _anchor(a.rectangle, b.rectangle)
        turns = _transition_identity(a, b)
        if turns is not None:
            p = BranchOverlapProof(i, j, point, "equal", "log-transitions", turns)
        elif _derivative_identity(a, b, point):
            p = BranchOverlapProof(i, j, point, "equal", "derivative-anchor")
        elif (
            certify_zero(
                a.value.subs(a.variable, point) - b.value.subs(b.variable, point)
            )
            is False
        ):
            p = BranchOverlapProof(i, j, point, "different", "anchor-disagreement")
        else:
            p = BranchOverlapProof(i, j, point, "unresolved", "unresolved")
        overlaps.append(p)
    first = charts[0]
    proof = BranchGluingProof(
        first.relation,
        first.variable,
        first.value_symbol,
        tuple(c.rectangle for c in charts) if requested is None else tuple(requested),
        charts,
        tuple(overlaps),
        tuple(unresolved),
    )
    if not proof.verify():
        raise ValueError("invalid branch-gluing assembly")
    return proof
