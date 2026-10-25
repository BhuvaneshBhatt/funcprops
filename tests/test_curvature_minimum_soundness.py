import sympy as sp

from funcprops.certified_optimization import (
    GlobalMinimumCertificate,
    certify_global_minimum,
)

x = sp.Symbol("x", real=True)


def test_disconnected_stationary_point_is_not_global_minimum():
    f = sp.Piecewise((x**2, x >= 0), ((x + 2) ** 2 - 10, True))
    domain = sp.Union(sp.Interval(-3, -sp.Rational(5, 2)), sp.Interval(0, 1))
    assert f.subs(x, -3) < f.subs(x, 0)
    assert certify_global_minimum(f, x, domain) is None
    assert not GlobalMinimumCertificate(
        f, x, 0, 0, True, "strict-convex-stationary", domain
    ).verify()


def test_discontinuous_curvature_certificate_is_rejected():
    f = sp.Piecewise((x**2, x >= 0), ((x + 2) ** 2 - 10, True))
    assert not GlobalMinimumCertificate(
        f, x, 0, 0, True, "strict-convex-stationary"
    ).verify()


def test_interior_pole_cannot_use_stationary_curvature():
    f = x**2 + 1 / x**2
    result = certify_global_minimum(f, x)
    assert result.verify()
    assert result.unique is False and result.value == 2
    assert result.domain == sp.Union(
        sp.Interval.open(-sp.oo, 0), sp.Interval.open(0, sp.oo)
    )
    assert not GlobalMinimumCertificate(
        f, x, 1, 2, True, "strict-convex-stationary"
    ).verify()


def test_valid_real_interval_minima_replay():
    for domain in (sp.S.Reals, sp.Interval(-2, 3), sp.Interval.open(-2, 3)):
        c = certify_global_minimum(x**4 + x**2, x, domain)
        assert c.verify() and c.point == 0 and c.unique


def test_complex_valued_curvature_is_rejected():
    assert certify_global_minimum(x**2 + sp.I, x) is None


def test_boolean_restriction_is_preserved():
    assert certify_global_minimum(x**2, x, x > 2) is None
    c = certify_global_minimum(x**2, x, sp.And(x > -1, x < 2))
    assert c.domain == sp.Interval.open(-1, 2)
    assert c.verify()
