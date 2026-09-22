import pytest
import sympy as sp

import funcprops as fp
from funcprops.results import Analyticity, Continuity, Convexity, TruthValue

x, y, z = sp.symbols("x y z", real=True)
f = sp.Symbol("f", real=True)


@pytest.mark.parametrize(
    "expr,var,expected",
    [
        (sp.sin(x), x, Continuity.CONTINUOUS),
        (sp.tanh(x), x, Continuity.CONTINUOUS),
        (sp.floor(x), x, Continuity.DISCONTINUOUS),
        (4 / (x**2 + 4), x, Continuity.CONTINUOUS),
        (1 / (x**2 - 4), x, Continuity.CONTINUOUS),
        (sp.sin(x**2 + 3 * x + 2), x, Continuity.CONTINUOUS),
        (sp.exp(sp.sin(x)), x, Continuity.CONTINUOUS),
        (
            sp.sin(x) * sp.cos(x) + sp.cos(sp.sin(x)) ** 2 + sp.exp(-x),
            x,
            Continuity.CONTINUOUS,
        ),
        (sp.sqrt(x), x, Continuity.CONTINUOUS),
        (sp.sin(x) / x, x, Continuity.CONTINUOUS),
    ],
)
def test_real_continuity_regressions(expr, var, expected):
    assert fp.function_continuous(expr, var) is expected


def test_restricted_real_continuity_regressions():
    assert fp.function_continuous(sp.log(x), x, domain=x > 0) is Continuity.CONTINUOUS
    assert fp.function_continuous(sp.sqrt(x), x, domain=x > 0) is Continuity.CONTINUOUS
    assert fp.function_continuous(sp.sqrt(x), x, domain=x >= 0) is Continuity.CONTINUOUS


@pytest.mark.parametrize(
    "expr,var,domain,expected",
    [
        (sp.sin(x), x, sp.S.Reals, Analyticity.ANALYTIC),
        (sp.tanh(x), x, sp.S.Reals, Analyticity.ANALYTIC),
        (sp.floor(x), x, sp.S.Reals, Analyticity.NOT_ANALYTIC),
        (x + sp.exp(x), x, sp.S.Complexes, Analyticity.ANALYTIC),
        (sp.exp(z), z, sp.S.Complexes, Analyticity.ANALYTIC),
        (4 / (x**2 + 4), x, sp.S.Reals, Analyticity.ANALYTIC),
        (sp.sin(x**2 + 3 * x + 2), x, sp.S.Reals, Analyticity.ANALYTIC),
        (sp.exp(sp.sin(x)), x, sp.S.Reals, Analyticity.ANALYTIC),
        (sp.exp(sp.I * x), x, sp.S.Complexes, Analyticity.ANALYTIC),
    ],
)
def test_analyticity_regressions(expr, var, domain, expected):
    assert fp.function_analytic(expr, var, domain=domain) is expected


def test_nonsmooth_head_is_not_real_analytic_but_restriction_can_be():
    assert fp.function_analytic(sp.Abs(x), x) is Analyticity.NOT_ANALYTIC
    assert fp.function_analytic(sp.Abs(x), x, domain=x > 0) is Analyticity.ANALYTIC


@pytest.mark.parametrize(
    "expr,expected",
    [
        (sp.sinh(x), TruthValue.TRUE),
        (x**3, TruthValue.TRUE),
        (x**3 - x, TruthValue.FALSE),
        (sp.atan(x), TruthValue.FALSE),
        (sp.log(x), TruthValue.TRUE),
        (x**3 / (x**2 + 1), TruthValue.TRUE),
        (x * sp.sin(x), TruthValue.FALSE),
        (sp.erf(x), TruthValue.FALSE),
        (x**2 + x + 1, TruthValue.FALSE),
        (x**3 + x + 1, TruthValue.TRUE),
    ],
)
def test_scalar_bijectivity_regressions(expr, expected):
    assert fp.function_bijective(expr, x) is expected


@pytest.mark.parametrize(
    "expr,expected_set",
    [
        (
            sp.Abs(x),
            {
                Convexity.CONVEX,
                Convexity.STRICTLY_CONVEX,
                Convexity.STRONGLY_CONVEX,
                Convexity.AFFINE,
            },
        ),
        (
            2**x,
            {Convexity.CONVEX, Convexity.STRICTLY_CONVEX, Convexity.STRONGLY_CONVEX},
        ),
        (sp.sin(x), {Convexity.UNKNOWN, Convexity.NEITHER}),
        (
            x**2 + y**2,
            {
                Convexity.CONVEX,
                Convexity.STRICTLY_CONVEX,
                Convexity.STRONGLY_CONVEX,
                Convexity.AFFINE,
            },
        ),
        (x**2 - y**2, {Convexity.UNKNOWN, Convexity.NEITHER}),
    ],
)
def test_convexity_regressions(expr, expected_set):
    var = (x, y) if expr.has(y) else x
    assert fp.function_convexity(expr, var) in expected_set


def test_concavity_on_positive_log_domain():
    assert fp.function_convexity(sp.log(x), x, domain=x > 0) in (
        Convexity.CONCAVE,
        Convexity.STRICTLY_CONCAVE,
        Convexity.STRONGLY_CONCAVE,
    )


def test_discontinuity_records_for_tangent_and_gamma():
    tan_records = fp.function_discontinuities(sp.tan(x), x, return_result=True)
    assert tan_records and any(r.condition == sp.Eq(sp.cos(x), 0) for r in tan_records)
    gamma_records = fp.function_discontinuities(sp.gamma(x), x, return_result=True)
    assert gamma_records


def test_differentiability_uses_domain_regularities_not_symbolic_diff_existence():
    from funcprops.results import Differentiability

    assert (
        fp.function_differentiability(sp.Abs(x), x)
        is Differentiability.NOT_DIFFERENTIABLE
    )
    assert (
        fp.function_differentiability(sp.Abs(x), x, domain=x > 0)
        is Differentiability.SMOOTH
    )
    assert (
        fp.function_differentiability(x ** sp.Rational(3, 2), x, domain=x >= 0, order=1)
        is Differentiability.DIFFERENTIABLE
    )
    assert (
        fp.function_differentiability(x ** sp.Rational(3, 2), x, domain=x >= 0, order=2)
        is Differentiability.NOT_DIFFERENTIABLE
    )


def test_differentiability_all_properties_reports_implication_closure():
    from funcprops.results import Differentiability

    r = fp.function_differentiability(sp.exp(x), x, all_properties=True)
    assert r.primary is Differentiability.SMOOTH
    assert r.all_properties == (Differentiability.CK, Differentiability.DIFFERENTIABLE)
    assert r.evidence
