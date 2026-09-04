import sympy as sp
from sympy import S

from funcprops import (
    Convexity,
    ConvexityCertificate,
    IndexedZero,
    Monotonicity,
    PropertyIntervalDecomposition,
    PropertyResult,
    function_convexity,
    function_monotonicity,
    transcendental_roots,
    zero_geometry,
)

x = sp.symbols("x", real=True)


def test_bessel_indexed_zero_geometry_and_ordering():
    nu = sp.symbols("nu", real=True, nonnegative=True)
    g = zero_geometry(sp.besselj(nu, x), x)[0]
    assert g.family == "BesselJ"
    assert g.count is sp.oo
    assert g.simple is True
    assert isinstance(g.indexed_family[0], IndexedZero)
    assert any(q.source == "DLMF 10.21.E2" for i in g.interlacings for q in i.pattern)
    assert any(q.source == "DLMF 10.21.E3" for i in g.interlacings for q in i.pattern)


def test_bessel_positive_root_result_keeps_geometry():
    nu = sp.symbols("nu", real=True, nonnegative=True)
    r = transcendental_roots(
        sp.besselj(nu, x), x, sp.Interval.open(0, sp.oo), allow_numerical=False
    )
    assert r.complete
    assert r.method == "zero_geometry"
    assert r.geometry and r.geometry[0].count is sp.oo


def test_bessel_all_real_not_overcertified():
    nu = sp.symbols("nu", real=True, nonnegative=True)
    r = transcendental_roots(sp.besselj(nu, x), x, S.Reals, allow_numerical=False)
    assert not r.complete
    assert r.geometry


def test_airy_indexed_function_derivative_interlacing():
    g = zero_geometry(sp.airyai(x), x)[0]
    assert g.family == "AiryAi"
    assert g.count is sp.oo
    assert g.interlacings
    rel = g.interlacings[0].pattern
    assert len(rel) == 2
    assert all(
        isinstance(q.left, IndexedZero) and isinstance(q.right, IndexedZero)
        for q in rel
    )


def test_airy_roots_complete_on_real_line():
    r = transcendental_roots(sp.airyai(x), x, S.Reals, allow_numerical=False)
    assert r.complete and r.geometry


def test_ferrers_q_named_function_interlacing_metadata():
    LegendreQ = sp.Function("LegendreQ")
    nu, mu = sp.symbols("nu mu", real=True)
    g = zero_geometry(LegendreQ(nu, mu, x), x)[0]
    assert g.family == "FerrersQ"
    assert isinstance(g.count, sp.FiniteSet)
    assert g.interlacings and "interlace" in g.interlacings[0].source


def test_monotonicity_consumes_bessel_derivative_geometry():
    nu = sp.symbols("nu", real=True, nonnegative=True)
    r = function_monotonicity(sp.besselj(nu, x), x, domain=x > 0, intervals=True)
    assert isinstance(r, PropertyResult)
    assert r.primary is Monotonicity.NOT_MONOTONE
    assert r.evidence and isinstance(r.evidence[0], PropertyIntervalDecomposition)
    assert r.evidence[0].alternating is True


def test_monotonicity_consumes_airy_derivative_geometry():
    r = function_monotonicity(sp.airyai(x), x, intervals=True)
    assert isinstance(r, PropertyResult)
    assert r.primary is Monotonicity.NOT_MONOTONE
    assert r.evidence and r.evidence[0].boundary_geometry


def test_convexity_airy_uses_ode_zero_geometry():
    r = function_convexity(sp.airyai(x), x, intervals=True)
    assert isinstance(r, PropertyResult)
    assert r.primary is Convexity.NEITHER
    certificate = r.evidence[0]
    assert isinstance(certificate, ConvexityCertificate)
    dec = certificate.proof[0]
    assert isinstance(dec, PropertyIntervalDecomposition)
    assert dec.derivative_order == 2
    assert dec.alternating is True


def test_orthogonal_derivative_geometry_drives_interval_reasoning():
    f = sp.legendre(4, x)
    m = function_monotonicity(f, x, domain=(x > -1) & (x < 1), intervals=True)
    assert isinstance(m, PropertyResult) and m.primary is Monotonicity.NOT_MONOTONE
    assert m.evidence and m.evidence[0].boundary_geometry
    c = function_convexity(f, x, domain=(x > -1) & (x < 1), intervals=True)
    assert isinstance(c, PropertyResult) and c.primary is Convexity.NEITHER
    assert c.evidence and isinstance(c.evidence[0], ConvexityCertificate)
    assert c.evidence[0].proof and c.evidence[0].proof[0].boundary_geometry


def test_indexed_zero_ordering_bounds_api():
    from funcprops import zero_ordering_bounds

    nu = sp.symbols("nu", real=True, nonnegative=True)
    k = sp.symbols("k", integer=True, positive=True)
    z = IndexedZero("BesselJ", k, nu, 0, "positive")
    b = zero_ordering_bounds(z)
    assert len(b) >= 3
    assert all(q.relation == "<" for q in b)
    a = IndexedZero("AiryAi", k, S.NaN, 0, "negative")
    assert len(zero_ordering_bounds(a)) == 2


def test_sign_partition_orders_exact_algebraic_roots_mathematically():
    f = sp.diff(sp.legendre(4, x), x)
    from funcprops import Sign, function_sign

    assert function_sign(f, x, domain=(x > -1) & (x < 1)) is Sign.SIGN_CHANGING
