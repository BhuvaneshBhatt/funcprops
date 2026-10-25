import sympy as sp
from sympy import S

from funcprops.real_analysis.common import condition_to_set
from funcprops.transcendental.algebraize import (
    algebraize,
    algebraize_trig_circle,
    algebraize_trigonometric,
)
from funcprops.transcendental.analytic import (
    analytic_neighborhood,
    holomorphic_on_rectangle,
)
from funcprops.transcendental.periodic import PeriodicSet, common_period_values
from funcprops.transcendental.roots import (
    CertifiedRootInterval,
    RootCertificate,
    transcendental_roots,
)

x = sp.symbols("x", real=True)
z = sp.symbols("z")


def test_periodic_union_commensurate_periods():
    a = PeriodicSet(sp.Interval.open(0, sp.pi / 2), sp.pi, x)
    b = PeriodicSet(sp.Interval.open(0, sp.pi), 2 * sp.pi, x)
    u = a.union(b)
    assert isinstance(u, PeriodicSet)
    assert sp.simplify(u.period - 2 * sp.pi) == 0
    assert sp.Contains(sp.pi + sp.pi / 4, u.base) is S.true


def test_periodic_intersection_and_complement():
    a = PeriodicSet(sp.Interval.open(0, sp.pi), 2 * sp.pi, x)
    b = PeriodicSet(sp.Interval.open(sp.pi / 2, 3 * sp.pi / 2), 2 * sp.pi, x)
    i = a.intersection(b)
    assert i.base == sp.Interval.open(sp.pi / 2, sp.pi)
    c = a.complement()
    assert sp.Contains(3 * sp.pi / 2, c.base) is S.true
    assert sp.Contains(sp.pi / 2, c.base) is S.false


def test_periodic_affine_pullback():
    a = PeriodicSet(sp.FiniteSet(0), sp.pi, x)
    p = a.affine_pullback(2, 1, x)
    assert sp.simplify(p.period - sp.pi / 2) == 0
    # 2*x+1 == k*pi has x=-1/2 modulo pi/2
    assert (
        sp.simplify(
            p.normalize_point(-sp.Rational(1, 2)) - p.normalize_point((sp.pi - 1) / 2)
        )
        == 0
    )


def test_root_certificate_exact_solveset():
    r = transcendental_roots(
        sp.exp(x) - 2, x, sp.Interval(-5, 5), allow_numerical=False
    )
    assert r.complete and r.roots == (sp.log(2),)
    assert r.certificates and isinstance(r.certificates[0], RootCertificate)
    assert r.certificates[0].root_count == 1


def test_certified_implicit_monotone_root_interval():
    # x + exp(x) - 3 is strictly increasing and has a unique root in [0,2].
    r = transcendental_roots(
        x + sp.exp(x) - 3, x, sp.Interval(0, 2), allow_numerical=False
    )
    assert r.complete
    assert (len(r.roots) == 1) or (len(r.isolated_intervals) == 1)
    if r.isolated_intervals:
        q = r.isolated_intervals[0]
        assert isinstance(q, CertifiedRootInterval)
        assert q.certificate.root_count == 1


def test_numeric_candidates_remain_uncertified():
    r = transcendental_roots(
        sp.sin(x) - x / 10, x, sp.Interval(1, 20), allow_numerical=True
    )
    if r.method == "numerical_scan":
        assert not r.complete and not r.certificates


def test_holomorphic_rectangle_log_shift_certified():
    r = holomorphic_on_rectangle(sp.log(z + 2), z, (-1 - sp.I / 10, 1 + sp.I / 10))
    assert r.certified and r.holomorphic is True


def test_holomorphic_rectangle_log_cut_detected():
    r = holomorphic_on_rectangle(sp.log(z), z, (-1 - sp.I / 10, 1 + sp.I / 10))
    assert r.certified and r.holomorphic is False


def test_analytic_neighborhood_exp():
    r = analytic_neighborhood(sp.exp(x), x, sp.Interval(-2, 2))
    assert r.certified and r.holomorphic is True


def test_rationally_commensurate_exponential_algebraization():
    e = sp.exp(x / 2) + sp.exp(3 * x / 2) + sp.exp(-x / 2)
    a = algebraize(e, x)
    assert a.changed and a.exact and a.method == "exponential_substitution"
    u, _ = a.substitutions[0]
    assert sp.simplify(a.expression - (u + u**3 + 1 / u)) == 0
    assert condition_to_set(a.constraints, u) == sp.Interval.open(0, sp.oo)


def test_tangent_half_angle_algebraization():
    a = algebraize_trigonometric(sp.sin(x) + sp.cos(x), x)
    assert a.changed and a.exact
    u, _ = a.substitutions[0]
    assert sp.simplify(a.expression - (2 * u + 1 - u**2) / (1 + u**2)) == 0
    assert a.source_domain == sp.Interval.open(-sp.pi, sp.pi)


def test_trig_circle_relation():
    a = algebraize_trig_circle(sp.sin(x) + sp.cos(x), x)
    assert a.changed and a.exact and len(a.substitutions) == 2
    assert a.relations and a.relations[0].rhs == 1


def test_common_period_values():
    assert sp.simplify(common_period_values(sp.pi, 2 * sp.pi) - 2 * sp.pi) == 0
