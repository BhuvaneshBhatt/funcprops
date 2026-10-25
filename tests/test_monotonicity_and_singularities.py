import sympy as sp

from funcprops import (
    Monotonicity,
    SingularityKind,
    monotonic_decomposition,
    monotonic_partition,
    monotonicity,
    singularity_analysis,
)

x = sp.symbols("x", real=True)


def test_monotonic_decomposition_inverse_trig_composition():
    d = monotonic_decomposition(sp.acos(sp.exp(x)), x, return_result=True)
    assert d.direction == -1
    assert d.inner == sp.exp(x)
    assert sp.simplify(d.reconstruct() - sp.acos(sp.exp(x))) == 0
    assert sp.simplify_logic(sp.Implies(d.condition, sp.exp(x) <= 1)) is sp.S.true


def test_sum_closure_monotonicity():
    assert monotonicity(sp.exp(x) + x, x) == Monotonicity.STRICTLY_INCREASING


def test_positive_product_closure_monotonicity():
    dom = x > 0
    assert (
        monotonicity(x * sp.exp(x), x, domain=dom) == Monotonicity.STRICTLY_INCREASING
    )


def test_finite_monotonic_partition():
    p = monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    assert p.complete
    assert len(p.cells) == 3
    assert [c.direction for c in p.cells] == [
        Monotonicity.STRICTLY_INCREASING,
        Monotonicity.STRICTLY_DECREASING,
        Monotonicity.STRICTLY_INCREASING,
    ]
    assert p.cells[0].left_limit == -2
    assert p.cells[0].right_limit == 2


def test_indexed_monotonic_partition_bessel():
    p = monotonic_partition(
        sp.besselj(0, x), x, domain=sp.Interval.open(0, sp.oo), return_result=True
    )
    assert p.complete
    assert p.indexed.boundary_geometry[0].family == "BesselJ"


def test_singularity_analysis_promotes_inner_pole_under_exp():
    a = singularity_analysis(sp.exp(1 / x), x)
    assert a.complete
    assert any(
        s.kind == SingularityKind.ESSENTIAL and s.condition == sp.Eq(x, 0)
        for s in a.essential
    )
    assert not a.poles


def test_piecewise_singularity_guards_propagate():
    f = sp.Piecewise((1 / x, x > 0), (sp.log(-x), True))
    a = singularity_analysis(f, x, domain=sp.S.Reals)
    assert a.complete
    poles = [s for s in a.poles if s.condition == sp.Eq(x, 0)]
    assert poles
    assert any(
        sp.simplify_logic(sp.Implies(s.guard, x > 0)) is sp.S.true for s in poles
    )
    assert any(s.source == "piecewise-boundary" for s in a.definition_cuts)


def test_unknown_head_marks_analysis_incomplete():
    F = sp.Function("F")
    a = singularity_analysis(F(x), x)
    assert not a.complete
    assert "F" in a.unknown_heads
