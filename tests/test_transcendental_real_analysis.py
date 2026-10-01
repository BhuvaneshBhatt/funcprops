import sympy as sp

from funcprops import (
    Convexity,
    Monotonicity,
    Sign,
    convexity,
    domain,
    monotonicity,
    range,
    sign,
)

x, y = sp.symbols("x y", real=True)


def equivalent(a, b):
    return sp.simplify_logic(sp.Equivalent(a, b)) is sp.S.true


def test_transcendental_domain_composition():
    assert equivalent(domain(sp.log(x**2 - 1), x), x**2 > 1)
    assert equivalent(domain(sp.sqrt(sp.sin(x)), x), sp.sin(x) >= 0)
    assert equivalent(
        domain(sp.asin(2 * x), x),
        sp.And(x >= -sp.Rational(1, 2), x <= sp.Rational(1, 2)),
    )
    assert domain(sp.tan(x), x) == sp.Ne(sp.cos(x), 0)


def test_sign_engine_structural_and_interval_certification():
    assert sign(sp.exp(x), x) is Sign.POSITIVE
    assert sign(x**2, x) is Sign.NONNEGATIVE
    assert sign(sp.log(x), x, domain=x > 1) is Sign.POSITIVE
    assert sign(sp.sin(x), x, domain=sp.And(x > 0, x < sp.pi)) is Sign.POSITIVE
    assert sign(sp.cos(x), x, domain=sp.And(x >= 0, x <= sp.pi)) is Sign.SIGN_CHANGING


def test_transcendental_monotonicity():
    assert monotonicity(sp.exp(x), x) is Monotonicity.STRICTLY_INCREASING
    assert monotonicity(sp.log(x), x) is Monotonicity.STRICTLY_INCREASING
    assert monotonicity(sp.atan(x), x) is Monotonicity.STRICTLY_INCREASING
    assert monotonicity(sp.sin(x), x) is Monotonicity.NOT_MONOTONE
    assert (
        monotonicity(sp.sin(x), x, domain=sp.And(x > 0, x < sp.pi / 2))
        is Monotonicity.STRICTLY_INCREASING
    )


def test_transcendental_ranges_and_endpoint_attainment():
    assert equivalent(range(sp.exp(x), x, y), y > 0)
    assert equivalent(range(sp.log(x), x, y), sp.S.true)
    assert equivalent(range(sp.sin(x), x, y), sp.And(y >= -1, y <= 1))
    assert equivalent(range(sp.atan(x), x, y), sp.And(y > -sp.pi / 2, y < sp.pi / 2))
    assert equivalent(
        range(sp.exp(sp.sin(x)), x, y), sp.And(y >= sp.exp(-1), y <= sp.E)
    )
    assert equivalent(range(2 * sp.exp(x) + 1, x, y), y > 1)


def test_transcendental_convexity_and_domain_convexity():
    assert convexity(sp.exp(x), x) is Convexity.STRICTLY_CONVEX
    assert convexity(sp.log(x), x) is Convexity.STRICTLY_CONCAVE
    assert convexity(sp.sqrt(x), x) in (
        Convexity.STRICTLY_CONCAVE,
        Convexity.CONCAVE,
    )
    assert convexity(sp.cosh(x), x) is Convexity.STRONGLY_CONVEX
    assert convexity(sp.exp(x**2), x) is Convexity.STRONGLY_CONVEX
    assert convexity(sp.log(x**2), x) is Convexity.NEITHER
    assert convexity(sp.sin(x), x) is Convexity.NEITHER
