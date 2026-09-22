import sympy as sp

from funcprops import (
    Analyticity,
    ConditionalExpression,
    Continuity,
    Meromorphicity,
    function_analytic,
    function_branchcuts,
    function_branchpoints,
    function_continuous,
    function_discontinuities,
    function_geometry,
    function_meromorphic,
    function_poles,
    function_singularities,
)
from funcprops.results import SingularityKind


def test_integer_bessel_order_shadows_generic_branch_rule():
    z = sp.Symbol("z")
    n = sp.Symbol("n", integer=True)
    assert function_branchcuts(sp.besselj(n, z), z) == ()
    assert function_branchpoints(sp.besselj(n, z), z) is sp.S.false
    assert function_meromorphic(sp.besselj(n, z), z) == Meromorphicity.MEROMORPHIC


def test_generic_bessel_order_retains_parameter_guard():
    z, n = sp.symbols("z n")
    points = function_branchpoints(sp.besselj(n, z), z, return_result=True)
    assert len(points) == 1
    assert points[0].condition == sp.Eq(z, 0)
    assert points[0].guard.has(n)
    result = function_meromorphic(sp.besselj(n, z), z)
    assert result.primary == Meromorphicity.UNKNOWN
    assert len(result.cases) == 2


def test_noninteger_bessel_has_origin_branch_point():
    z = sp.Symbol("z")
    points = function_branchpoints(
        sp.besselj(sp.Rational(1, 2), z), z, return_result=True
    )
    assert any(p.condition == sp.Eq(z, 0) and p.guard is sp.S.true for p in points)


def test_local_order_cancels_denominator_multiplicity():
    x = sp.Symbol("x")
    poles = function_poles(sp.sin(x) / x**3, x)
    assert poles == [(0, 2)]
    records = function_poles(sp.sin(x) / x**3, x, return_result=True)
    assert records[0].condition == sp.Eq(x, 0)


def test_removable_singularity_is_separate_from_poles():
    x = sp.Symbol("x")
    expr = sp.sin(x) / x
    assert function_poles(expr, x) == []
    singular = function_singularities(expr, x, return_result=True)
    assert singular.singularities == (sp.Eq(sp.re(x), 0) & sp.Eq(sp.im(x), 0))
    assert singular.removable == (sp.Eq(sp.re(x), 0) & sp.Eq(sp.im(x), 0))
    assert any(
        s.kind == SingularityKind.REMOVABLE and s.condition == sp.Eq(x, 0)
        for s in singular.records
    )


def test_generic_reciprocal_keeps_unsolved_zero_condition():
    x = sp.Symbol("x")
    f = sp.Function("f")
    poles = function_poles(1 / f(x), x)
    assert poles == [(sp.Eq(f(x), 0), None)]


def test_branchcut_composition_is_pulled_back_without_solving():
    z = sp.Symbol("z")
    cuts = function_branchcuts(sp.log(1 - z), z)
    assert len(cuts) == 1
    assert cuts[0].has(1 - z)


def test_nested_branchcuts_keep_outer_and_inner_loci():
    z = sp.Symbol("z")
    cuts = function_branchcuts(sp.sqrt(sp.log(1 - z)), z)
    assert len(cuts) == 2
    assert any(c.has(sp.log(1 - z)) for c in cuts)
    assert any(c.has(1 - z) for c in cuts)


def test_principal_log_is_analytic_on_natural_domain_but_not_meromorphic():
    z = sp.Symbol("z")
    assert (
        function_analytic(sp.log(z), z, domain=sp.S.Complexes) == Analyticity.ANALYTIC
    )
    assert function_meromorphic(sp.log(z), z) == Meromorphicity.NOT_MEROMORPHIC


def test_gamma_is_analytic_on_natural_domain_and_meromorphic():
    z = sp.Symbol("z")
    assert (
        function_analytic(sp.gamma(z), z, domain=sp.S.Complexes) == Analyticity.ANALYTIC
    )
    assert function_meromorphic(sp.gamma(z), z) == Meromorphicity.MEROMORPHIC
    assert function_poles(sp.gamma(z), z)


def test_essential_composition_is_not_meromorphic():
    z = sp.Symbol("z")
    expr = sp.exp(1 / z)
    assert function_analytic(expr, z, domain=sp.S.Complexes) == Analyticity.ANALYTIC
    assert function_meromorphic(expr, z) == Meromorphicity.NOT_MEROMORPHIC
    singular = function_singularities(expr, z, return_result=True)
    assert singular.essential == (sp.Eq(sp.re(z), 0) & sp.Eq(sp.im(z), 0))
    assert any(s.kind == SingularityKind.ESSENTIAL for s in singular.records)


def test_sqrt_is_continuous_but_not_real_analytic_at_zero():
    x = sp.Symbol("x", real=True)
    assert function_analytic(sp.sqrt(x), x) == Analyticity.NOT_ANALYTIC
    assert function_continuous(sp.sqrt(x), x) == Continuity.CONTINUOUS


def test_abs_is_continuous_but_not_real_analytic():
    x = sp.Symbol("x", real=True)
    assert function_analytic(sp.Abs(x), x) == Analyticity.NOT_ANALYTIC
    assert function_continuous(sp.Abs(x), x) == Continuity.CONTINUOUS


def test_sign_has_explicit_discontinuity():
    x = sp.Symbol("x", real=True)
    d = function_discontinuities(sp.sign(x), x)
    assert d == sp.Eq(x, 0)
    assert function_continuous(sp.sign(x), x) == Continuity.DISCONTINUOUS


def test_acos_is_continuous_on_closed_real_domain_but_not_real_analytic_at_endpoints():
    x = sp.Symbol("x", real=True)
    assert function_analytic(sp.acos(x), x) == Analyticity.NOT_ANALYTIC
    assert function_continuous(sp.acos(x), x) == Continuity.CONTINUOUS


def test_gamma_is_continuous_on_its_natural_real_domain():
    x = sp.Symbol("x", real=True)
    assert function_continuous(sp.gamma(x), x) == Continuity.CONTINUOUS


def test_piecewise_step_discontinuity_is_found():
    x = sp.Symbol("x", real=True)
    expr = sp.Piecewise((0, x < 0), (1, True))
    d = function_discontinuities(expr, x)
    assert d == sp.Eq(x, 0)
    assert function_continuous(expr, x) == Continuity.DISCONTINUOUS


def test_continuous_piecewise_boundary_is_not_reported_as_discontinuity():
    x = sp.Symbol("x", real=True)
    expr = sp.Piecewise((-x, x < 0), (x, True))
    assert function_discontinuities(expr, x) is sp.S.false
    assert function_continuous(expr, x) == Continuity.CONTINUOUS


def test_multivariate_condition_preserves_domain_dimension():
    x, y = sp.symbols("x y", real=True)
    expr = ConditionalExpression(x**2 + y**2, sp.And(x > 0, y > 0))
    geometry = function_geometry(expr, (x, y))
    assert geometry.domain == sp.And(x > 0, y > 0)
