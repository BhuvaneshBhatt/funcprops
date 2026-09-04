import sympy as sp

from funcprops import (
    Convexity,
    Monotonicity,
    PropertyResult,
    Sign,
    function_convexity,
    function_monotonicity,
    function_sign,
)

x = sp.symbols("x", real=True)
a = sp.symbols("a", real=True)


def test_power_parameter_convexity_strata():
    r = function_convexity(x**a, x, domain=x > 0)
    assert isinstance(r, PropertyResult)
    vals = {c.value for c in r.cases}
    assert Convexity.STRICTLY_CONVEX in vals
    assert Convexity.STRICTLY_CONCAVE in vals
    assert Convexity.AFFINE in vals


def test_power_parameter_monotonicity_strata():
    r = function_monotonicity(x**a, x, domain=x > 0)
    assert isinstance(r, PropertyResult)
    vals = {c.value for c in r.cases}
    assert vals == {
        Monotonicity.STRICTLY_INCREASING,
        Monotonicity.STRICTLY_DECREASING,
        Monotonicity.CONSTANT,
    }


def test_exp_parameter_strata():
    r = function_convexity(sp.exp(a * x), x)
    assert isinstance(r, PropertyResult)
    assert {c.value for c in r.cases} == {Convexity.STRICTLY_CONVEX, Convexity.AFFINE}


def test_strong_convexity_quadratic():
    r = function_convexity(x**2, x, all_properties=True)
    assert r.primary is Convexity.STRONGLY_CONVEX
    assert r.evidence and sp.simplify(r.evidence[0].modulus - 2) == 0


def test_exp_all_properties():
    r = function_convexity(sp.exp(x), x, all_properties=True)
    assert r.primary is Convexity.STRICTLY_CONVEX
    assert Convexity.LOG_CONVEX in r.all_properties
    assert Convexity.LOG_CONCAVE in r.all_properties
    assert Convexity.QUASICONVEX in r.all_properties
    assert Convexity.PSEUDOCONVEX in r.all_properties


def test_gamma_positive_log_convex():
    r = function_convexity(sp.gamma(x), x, domain=x > 0, all_properties=True)
    assert Convexity.LOG_CONVEX in r.all_properties
    assert function_sign(sp.gamma(x), x, domain=x > 0) is Sign.POSITIVE


def test_besselk_special_properties():
    r = function_convexity(sp.besselk(0, x), x, domain=x > 0, all_properties=True)
    assert r.primary in (Convexity.STRICTLY_CONVEX, Convexity.STRONGLY_CONVEX)
    assert Convexity.LOG_CONVEX in r.all_properties
