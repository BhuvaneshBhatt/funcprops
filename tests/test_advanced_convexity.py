import sympy as sp

from funcprops import (
    Convexity,
    Monotonicity,
    PropertyResult,
    Sign,
    convexity,
    monotonicity,
    sign,
)

x = sp.symbols("x", real=True)
a = sp.symbols("a", real=True)


def test_power_parameter_convexity_strata():
    r = convexity(x**a, x, domain=x > 0, return_result=True)
    assert isinstance(r, PropertyResult)
    vals = {c.value for c in r.cases}
    assert Convexity.STRICTLY_CONVEX in vals
    assert Convexity.STRICTLY_CONCAVE in vals
    assert Convexity.AFFINE in vals


def test_power_parameter_monotonicity_strata():
    r = monotonicity(x**a, x, domain=x > 0, return_result=True)
    assert isinstance(r, PropertyResult)
    vals = {c.value for c in r.cases}
    assert vals == {
        Monotonicity.STRICTLY_INCREASING,
        Monotonicity.STRICTLY_DECREASING,
        Monotonicity.CONSTANT,
    }


def test_exp_parameter_strata():
    r = convexity(sp.exp(a * x), x, return_result=True)
    assert isinstance(r, PropertyResult)
    assert {c.value for c in r.cases} == {Convexity.STRICTLY_CONVEX, Convexity.AFFINE}


def test_strong_convexity_quadratic():
    r = convexity(x**2, x, all_properties=True, return_result=True)
    assert r.primary is Convexity.STRONGLY_CONVEX
    assert r.evidence and sp.simplify(r.evidence[0].modulus - 2) == 0


def test_exp_all_properties():
    r = convexity(sp.exp(x), x, all_properties=True, return_result=True)
    assert r.primary is Convexity.STRICTLY_CONVEX
    assert Convexity.LOG_CONVEX in r.all_properties
    assert Convexity.LOG_CONCAVE in r.all_properties
    assert Convexity.QUASICONVEX in r.all_properties
    assert Convexity.PSEUDOCONVEX in r.all_properties


def test_gamma_positive_log_convex():
    r = convexity(sp.gamma(x), x, domain=x > 0, all_properties=True, return_result=True)
    assert Convexity.LOG_CONVEX in r.all_properties
    assert sign(sp.gamma(x), x, domain=x > 0) is Sign.POSITIVE


def test_besselk_special_properties():
    r = convexity(
        sp.besselk(0, x), x, domain=x > 0, all_properties=True, return_result=True
    )
    assert r.primary in (Convexity.STRICTLY_CONVEX, Convexity.STRONGLY_CONVEX)
    assert Convexity.LOG_CONVEX in r.all_properties
