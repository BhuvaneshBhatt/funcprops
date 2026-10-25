import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
t = sp.Symbol("t", real=True)


def test_exact_default_and_result():
    assert fp.integrate(z**2, (z, 0, 2)) == sp.Rational(8, 3)
    r = fp.integrate(z**2, (z, 0, 2), return_result=True)
    assert r.certified and r.complete and r.verify()


def test_polygon_closed_curve_orientation():
    ccw = [1 + sp.I, -1 + sp.I, -1 - sp.I, 1 - sp.I, 1 + sp.I]
    cw = list(reversed(ccw))
    assert sp.simplify(fp.integrate(1 / z, (z, ccw)) - 2 * sp.pi * sp.I) == 0
    assert sp.simplify(fp.integrate(1 / z, (z, cw)) + 2 * sp.pi * sp.I) == 0


def test_parametric_polynomial_and_reversal():
    c = fp.ParametricContour(t + sp.I * t**2, (t, -1, 1))
    v = fp.integrate(z, (z, c))
    vr = fp.integrate(z, (z, c.reversed()))
    assert sp.simplify(v + vr) == 0
    assert "rational" in fp.integrate(z, (z, c), return_result=True).method


def test_trig_circle_keeps_orientation_and_winding():
    c = fp.ParametricContour(sp.cos(t) + sp.I * sp.sin(t), (t, 0, 2 * sp.pi))
    r = fp.integrate(1 / z, (z, c), return_result=True)
    assert sp.simplify(r.value - 2 * sp.pi * sp.I) == 0
    assert "trig" in r.method
    rr = fp.integrate(1 / z, (z, c.reversed()))
    assert sp.simplify(rr + 2 * sp.pi * sp.I) == 0


def test_multiple_winding():
    c = fp.ParametricContour(sp.exp(2 * sp.I * t), (t, 0, 2 * sp.pi))
    assert sp.simplify(fp.integrate(1 / z, (z, c)) - 4 * sp.pi * sp.I) == 0


def test_semialg_rational_avoidance_helper():
    from funcprops.integration import _point_avoided_semialg

    c = fp.ParametricContour(t + sp.I * t**2, (t, -1, 1))
    q = _point_avoided_semialg(c, 2)
    assert q in (True, None)  # True with semialg installed; conservative otherwise.


def test_analytic_exact_fallback():
    c = fp.ParametricContour(sp.exp(t) + sp.I * t, (t, 0, 1))
    r = fp.integrate(1, (z, c), return_result=True)
    assert r.certified and sp.simplify(r.value - (sp.E - 1 + sp.I)) == 0


def test_incomplete_does_not_claim_numeric_value():
    f = sp.Function("f")
    c = fp.ParametricContour(t + sp.I * t, (t, 0, 1))
    r = fp.integrate(f(z), (z, c), return_result=True)
    assert not r.complete and r.value is None


def test_pole_on_rational_path_is_not_certified():
    c = fp.ParametricContour(t, (t, -1, 1))
    r = fp.integrate(1 / z, (z, c), return_result=True)
    assert not r.complete and not r.certified


def test_trig_algebraization_evidence():
    c = fp.ParametricContour(sp.cos(2 * t) + sp.I * sp.sin(2 * t), (t, 0, 2 * sp.pi))
    r = fp.integrate(1 / z, (z, c), return_result=True)
    assert r.method == "parametric-trig-algebraized-exact"
    assert any(k == "trig_algebraization" for k, _ in r.evidence)
    assert sp.simplify(r.value - 4 * sp.pi * sp.I) == 0


def test_general_analytic_adaptive_interval_taylor():
    c = fp.ParametricContour(t, (t, 0, 1))
    r = fp.integrate(
        sp.exp(sp.sin(z)), (z, c), return_result=True, tolerance=sp.Rational(1, 10) ** 8
    )
    assert r.complete and r.certified
    assert r.method == "parametric-analytic-taylor"
    assert float(r.error_bound) <= 1e-8


def test_generic_certificate_replay():
    r = fp.integrate(z**2, (z, 0, 2), return_result=True)
    assert fp.verify_certificate(r)


def test_branch_sensitive_complex_contour_is_not_silently_certified():
    c = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    r = fp.integrate(sp.log(z), (z, c), return_result=True)
    assert not r.complete and not r.certified


def test_positive_real_log_path_remains_exact():
    assert sp.simplify(fp.integrate(sp.log(z), (z, 1, 2)) - (2 * sp.log(2) - 1)) == 0
