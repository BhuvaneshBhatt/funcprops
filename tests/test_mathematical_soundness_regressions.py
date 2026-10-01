import sympy as sp

import funcprops as fp
from funcprops.taylor_models import taylor_model


def test_taylor_odd_remainder_keeps_sign_range():
    x = sp.symbols("x", real=True)
    m = taylor_model(x**3, x, sp.Interval(-1, 1), order=2, center=0)
    assert m is not None and m.verify()
    assert m.remainder_lower <= -1 and m.remainder_upper >= 1


def test_trig_contour_through_pole_is_not_certified():
    z, t = sp.symbols("z t", real=True)
    c = fp.ParametricContour(sp.cos(t) + sp.I * sp.sin(t), (t, 0, 2 * sp.pi))
    r = fp.integrate(1 / (z - 1), (z, c), return_result=True)
    assert not r.certified and not r.complete and r.value is None


def test_argument_principle_rejects_essential_singularity():
    z, t = sp.symbols("z t")
    c = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    assert fp.argument_principle(sp.exp(1 / z), z, c) is None


def test_multipuncture_homotopy_uses_nonabelian_free_word_certificate():
    t = sp.symbols("t", real=True)
    c1 = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    c2 = fp.ParametricContour(3 * (sp.cos(t) + sp.I * sp.sin(t)), (t, 0, 2 * sp.pi))
    cert = fp.homotopic(c1, c2, punctures=(-1, 1), return_certificate=True)
    assert cert is not None and cert.verify()
    assert cert.cut_direction is not None
    assert len(cert.reduced_word) == 2


def test_free_group_reduction_retains_commutator_order():
    from funcprops.certified_operations import _free_reduce

    assert _free_reduce((1, 2, -1, -2)) == (1, 2, -1, -2)
    assert _free_reduce((1, 2, -2, -1)) == ()


def test_log_pole_is_branch_point_but_integral_local_power_is_not():
    z = sp.symbols("z")
    assert fp.classify_singularity(sp.log(1 / z), z, 0) == "branch_point"
    e = sp.Pow(z**2, sp.Rational(1, 2), evaluate=False)
    assert fp.classify_singularity(e, z, 0) != "branch_point"


def test_inverse_certificate_rejects_false_image():
    x, y = sp.symbols("x y", real=True)
    c = fp.inverse(2 * x + 3, x, value=y, return_certificate=True)
    assert c is not None and c.verify()
    bad = type(c)(
        c.expression, c.variable, c.value, c.inverse, c.domain, sp.S.UniversalSet
    )
    assert not bad.verify()
