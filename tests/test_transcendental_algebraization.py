import sympy as sp

from funcprops import (
    convexity,
    monotonicity,
    range,
    sign,
)
from funcprops.results import Convexity, Monotonicity, Sign
from funcprops.transcendental import (
    PeriodicCondition,
    algebraize,
    condition_to_intervals,
    reduce_univariate_condition,
    transcendental_roots,
)

x = sp.symbols("x", real=True)
y = sp.symbols("y", real=True)


def test_periodic_condition_sin_positive():
    r = reduce_univariate_condition(sp.sin(x) > 0, x)
    assert r.complete
    assert isinstance(r.condition, PeriodicCondition)
    ps = r.condition.set
    assert sp.simplify(ps.period - 2 * sp.pi) == 0
    assert ps.base == sp.Interval.open(0, sp.pi)


def test_periodic_condition_tan_positive_partitions_at_pole():
    r = reduce_univariate_condition(sp.tan(x) > 0, x)
    assert r.complete
    assert isinstance(r.condition, PeriodicCondition)
    assert sp.simplify(r.condition.set.period - sp.pi) == 0
    assert r.condition.set.base == sp.Interval.open(0, sp.pi / 2)


def test_structural_periodic_root_certificate():
    r = transcendental_roots(sp.sin(2 * x + 1), x)
    assert r.complete and r.periodic is not None
    assert sp.simplify(r.periodic.period - sp.pi / 2) == 0


def test_special_root_certificate_erf():
    r = transcendental_roots(sp.erf(3 * x - 2), x, sp.Interval(-5, 5))
    assert r.complete
    assert r.roots == (sp.Rational(2, 3),)


def test_numerical_fallback_is_never_certified():
    r = transcendental_roots(
        sp.sin(x) - x / 10, x, sp.Interval(1, 20), allow_numerical=True
    )
    if r.method == "numerical_scan":
        assert not r.complete


def test_exponential_algebraization():
    e = sp.exp(2 * x) - 3 * sp.exp(x) + 2
    a = algebraize(e, x)
    assert a.changed and a.exact
    u, _ = a.substitutions[0]
    assert sp.expand(a.expression - (u**2 - 3 * u + 2)) == 0
    assert a.constraints == (u > 0)


def test_hyperbolic_algebraization():
    a = algebraize(sp.cosh(x) - 2, x)
    assert a.changed and a.exact
    assert not a.expression.has(sp.cosh)


def test_sign_uses_exponential_algebraization():
    assert sign(sp.exp(2 * x) - 3 * sp.exp(x) + 2, x) is Sign.SIGN_CHANGING


def test_monotonicity_uses_algebraized_derivative():
    # derivative = 2*exp(2x)-3*exp(x) changes sign on R
    assert monotonicity(sp.exp(2 * x) - 3 * sp.exp(x), x) is Monotonicity.NOT_MONOTONE


def test_range_uses_exponential_algebraization():
    r = range(sp.exp(2 * x) - 2 * sp.exp(x), x, y)
    s = r.as_set()
    assert s == sp.Interval(-1, sp.oo)


def test_convexity_uses_algebraized_second_derivative():
    assert convexity(sp.exp(x) + sp.exp(2 * x), x) is Convexity.STRICTLY_CONVEX


def test_condition_to_intervals_helper():
    got = condition_to_intervals((x < 0) | (x >= 1), x)
    assert got == (sp.Interval.open(-sp.oo, 0), sp.Interval(1, sp.oo))
