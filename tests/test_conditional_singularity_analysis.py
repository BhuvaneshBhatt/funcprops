import sympy as sp

from funcprops import (
    Analyticity,
    ConditionalExpression,
    Continuity,
    Meromorphicity,
    analytic,
    branch_cuts,
    branch_points,
    continuous,
    discontinuities,
    geometry,
    meromorphic,
    poles,
    singularities,
)
from funcprops.results import SingularityKind


def test_integer_bessel_order_shadows_generic_branch_rule():
    z = sp.Symbol("z")
    n = sp.Symbol("n", integer=True)
    assert branch_cuts(sp.besselj(n, z), z) == ()
    assert branch_points(sp.besselj(n, z), z) is sp.S.false
    assert meromorphic(sp.besselj(n, z), z) == Meromorphicity.MEROMORPHIC


def test_generic_bessel_order_retains_parameter_guard():
    z, n = sp.symbols("z n")
    points = branch_points(sp.besselj(n, z), z, return_result=True)
    assert len(points) == 1
    assert points[0].condition == sp.Eq(z, 0)
    assert points[0].guard.has(n)
    result = meromorphic(sp.besselj(n, z), z, return_result=True)
    assert result.primary == Meromorphicity.UNKNOWN
    assert len(result.cases) == 2


def test_noninteger_bessel_has_origin_branch_point():
    z = sp.Symbol("z")
    points = branch_points(sp.besselj(sp.Rational(1, 2), z), z, return_result=True)
    assert any(p.condition == sp.Eq(z, 0) and p.guard is sp.S.true for p in points)


def test_local_order_cancels_denominator_multiplicity():
    x = sp.Symbol("x")
    pole_values = poles(sp.sin(x) / x**3, x)
    assert pole_values == [(0, 2)]
    records = poles(sp.sin(x) / x**3, x, return_result=True)
    assert records[0].condition == sp.Eq(x, 0)


def test_removable_singularity_is_separate_from_poles():
    x = sp.Symbol("x")
    expr = sp.sin(x) / x
    assert poles(expr, x) == []
    singular = singularities(expr, x, return_result=True)
    assert singular.singularities == (sp.Eq(sp.re(x), 0) & sp.Eq(sp.im(x), 0))
    assert singular.removable == (sp.Eq(sp.re(x), 0) & sp.Eq(sp.im(x), 0))
    assert any(
        s.kind == SingularityKind.REMOVABLE and s.condition == sp.Eq(x, 0)
        for s in singular.records
    )


def test_generic_reciprocal_keeps_unsolved_zero_condition():
    x = sp.Symbol("x")
    f = sp.Function("f")
    pole_values = poles(1 / f(x), x)
    assert pole_values == [(sp.Eq(f(x), 0), None)]


def test_branchcut_composition_is_pulled_back_without_solving():
    z = sp.Symbol("z")
    cuts = branch_cuts(sp.log(1 - z), z)
    assert cuts == (z > 1,)


def test_nested_branchcuts_keep_outer_and_inner_loci():
    z = sp.Symbol("z")
    cuts = branch_cuts(sp.sqrt(sp.log(1 - z)), z)
    assert len(cuts) == 2
    assert any(c.has(sp.log(1 - z)) for c in cuts)
    assert any(c.has(1 - z) for c in cuts)


def test_principal_log_domain():
    z = sp.Symbol("z")
    assert analytic(sp.log(z), z, domain=sp.S.Complexes) == Analyticity.ANALYTIC
    assert meromorphic(sp.log(z), z) == Meromorphicity.NOT_MEROMORPHIC


def test_gamma_is_analytic_on_natural_domain_and_meromorphic():
    z = sp.Symbol("z")
    assert analytic(sp.gamma(z), z, domain=sp.S.Complexes) == Analyticity.ANALYTIC
    assert meromorphic(sp.gamma(z), z) == Meromorphicity.MEROMORPHIC
    assert poles(sp.gamma(z), z)


def test_essential_composition_is_not_meromorphic():
    z = sp.Symbol("z")
    expr = sp.exp(1 / z)
    assert analytic(expr, z, domain=sp.S.Complexes) == Analyticity.ANALYTIC
    assert meromorphic(expr, z) == Meromorphicity.NOT_MEROMORPHIC
    singular = singularities(expr, z, return_result=True)
    assert singular.essential == (sp.Eq(sp.re(z), 0) & sp.Eq(sp.im(z), 0))
    assert any(s.kind == SingularityKind.ESSENTIAL for s in singular.records)


def test_sqrt_is_continuous_but_not_real_analytic_at_zero():
    x = sp.Symbol("x", real=True)
    assert analytic(sp.sqrt(x), x) == Analyticity.NOT_ANALYTIC
    assert continuous(sp.sqrt(x), x) == Continuity.CONTINUOUS


def test_abs_is_continuous_but_not_real_analytic():
    x = sp.Symbol("x", real=True)
    assert analytic(sp.Abs(x), x) == Analyticity.NOT_ANALYTIC
    assert continuous(sp.Abs(x), x) == Continuity.CONTINUOUS


def test_sign_has_explicit_discontinuity():
    x = sp.Symbol("x", real=True)
    d = discontinuities(sp.sign(x), x)
    assert d == sp.Eq(x, 0)
    assert continuous(sp.sign(x), x) == Continuity.DISCONTINUOUS


def test_acos_endpoint_regularity():
    x = sp.Symbol("x", real=True)
    assert analytic(sp.acos(x), x) == Analyticity.NOT_ANALYTIC
    assert continuous(sp.acos(x), x) == Continuity.CONTINUOUS


def test_gamma_is_continuous_on_its_natural_real_domain():
    x = sp.Symbol("x", real=True)
    assert continuous(sp.gamma(x), x) == Continuity.CONTINUOUS


def test_piecewise_step_discontinuity_is_found():
    x = sp.Symbol("x", real=True)
    expr = sp.Piecewise((0, x < 0), (1, True))
    d = discontinuities(expr, x)
    assert d == sp.Eq(x, 0)
    assert continuous(expr, x) == Continuity.DISCONTINUOUS


def test_continuous_piecewise_seam():
    x = sp.Symbol("x", real=True)
    expr = sp.Piecewise((-x, x < 0), (x, True))
    assert discontinuities(expr, x) is sp.S.false
    assert continuous(expr, x) == Continuity.CONTINUOUS


def test_multivariate_condition_preserves_domain_dimension():
    x, y = sp.symbols("x y", real=True)
    expr = ConditionalExpression(x**2 + y**2, sp.And(x > 0, y > 0))
    result = geometry(expr, (x, y))
    assert result.domain == sp.And(x > 0, y > 0)


def test_unresolved_seam_equality():
    from funcprops.singularities import _piecewise_discontinuous_at

    x = sp.Symbol("x", real=True)
    f = sp.Function("f")
    g = sp.Function("g")
    expr = sp.Piecewise((f(x), x < 0), (g(x), True))
    assert _piecewise_discontinuous_at(expr, x, sp.Eq(x, 0)) is None


def test_piecewise_boundaries_include_a_conditional_final_branch():
    from funcprops.singularities import _piecewise_boundaries

    x = sp.Symbol("x", real=True)
    expr = sp.Piecewise((0, x < 0), (1, x > 1))
    boundaries = set(_piecewise_boundaries(expr))
    assert sp.Eq(x, 0) in boundaries
    assert sp.Eq(x, 1) in boundaries


def test_conditioned_records_use_global_assumptions():
    from funcprops.results import Singularity
    from funcprops.singularities.analysis import _conditioned

    x, a = sp.symbols("x a", real=True)
    record = Singularity(SingularityKind.POLE, sp.Eq(x, 0), a < 0)
    assert _conditioned((record,), sp.S.true, assumptions=a > 0) == ()
