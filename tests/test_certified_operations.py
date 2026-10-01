import sympy as sp

import funcprops as fp


def circle(t, n=1):
    return fp.ParametricContour(sp.exp(sp.I * n * t), (t, 0, 2 * sp.pi))


def test_inverse_and_equation():
    x, y = sp.symbols("x y", real=True)
    assert fp.inverse(2 * x + 3, x, value=y) == (y - 3) / 2
    c = fp.solve((x - 1) * (x + 2), x, domain=sp.S.Reals, return_certificate=True)
    assert c.complete and c.solutions == sp.FiniteSet(-2, 1) and c.verify()


def test_laurent_residue():
    z = sp.symbols("z")
    c = fp.residue(sp.exp(z) / z**2, z, 0, return_certificate=True)
    assert c.residue == 1 and c.verify()
    s = fp.laurent_series(1 / z + sp.exp(z), z, 0, order=4, return_certificate=True)
    assert s.verify()


def test_winding_argument_principle_orientation():
    t, z = sp.symbols("t z", real=True)
    c = circle(t)
    cr = c.reversed()
    assert fp.winding_number(c, 0) == 1
    assert fp.winding_number(cr, 0) == -1
    assert fp.argument_principle((z - sp.Rational(1, 2)) / (z - 2), z, c) == 1


def test_homotopy_by_puncture_windings():
    t = sp.symbols("t", real=True)
    c1 = circle(t)
    c2 = fp.ParametricContour(sp.exp(sp.I * (t + sp.sin(t))), (t, 0, 2 * sp.pi))
    h = fp.homotopic(c1, c2, punctures=(0,), return_certificate=True)
    assert h and h.verify()


def test_monodromy_log_and_sqrt():
    t, z = sp.symbols("t z", real=True)
    c = circle(t)
    assert (
        sp.simplify(fp.monodromy(sp.log(z), z, c) - sp.log(z) - 2 * sp.pi * sp.I) == 0
    )
    assert sp.simplify(fp.monodromy(sp.sqrt(z), z, c) + sp.sqrt(z)) == 0


def test_singularity_classification_and_deformation():
    z, t = sp.symbols("z t")
    assert fp.classify_singularity(1 / z**3, z, 0) == "pole"
    assert fp.classify_singularity(sp.log(z), z, 0) == "branch_point"
    assert fp.classify_singularity(sp.exp(1 / z), z, 0) == "essential"
    c1 = fp.ParametricContour(2 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    c2 = fp.ParametricContour(2 * sp.exp(sp.I * (t + sp.sin(t) / 2)), (t, 0, 2 * sp.pi))
    cert = fp.deform_contour(
        1 / (z - sp.Rational(1, 2)), z, c1, c2, return_certificate=True
    )
    assert cert and fp.verify_certificate(cert)


def test_closed_contour_does_not_erase_log_antiderivative_monodromy():
    t, z = sp.symbols("t z")
    c = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    e = (z - sp.Rational(1, 2)) / (z - 2)
    q = sp.diff(e, z) / e
    r = fp.integrate(q, (z, c), return_result=True)
    assert not (r.complete and r.value == 0)


def test_open_paths_are_not_certified_by_closed_loop_windings():
    t = sp.symbols("t", real=True)
    p1 = fp.ParametricContour(t, (t, 0, 1))
    p2 = fp.ParametricContour(t**2, (t, 0, 1))
    assert fp.homotopic(p1, p2, punctures=(2,)) is None


def test_log_of_rational_power_preserves_fractional_divisor_winding():
    t, z = sp.symbols("t z")
    c = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    root = sp.Pow(z, sp.Rational(1, 2), evaluate=False)
    expr = sp.log(root, evaluate=False)
    continued = fp.monodromy(expr, z, c)
    assert sp.simplify(continued - expr - sp.pi * sp.I) == 0


def test_user_punctures_cannot_hide_integrand_poles():
    t, z = sp.symbols("t z")
    outer = fp.ParametricContour(2 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    inner = fp.ParametricContour(
        sp.Rational(1, 2) * sp.exp(sp.I * t), (t, 0, 2 * sp.pi)
    )
    # The pole z=1 distinguishes the loops.  Supplying an unrelated puncture
    # must not replace that mandatory obstacle.
    assert fp.deform_contour(1 / (z - 1), z, outer, inner, punctures=(3,)) is False


def test_certificate_replay_rejects_tampered_status_and_integral_fields():
    x = sp.symbols("x")
    c = fp.solve(x - 1, x, return_certificate=True)
    bad = type(c)(c.expression, c.variable, c.domain, c.solutions, False)
    assert not bad.verify()
    t = sp.symbols("t", real=True)
    circle = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    w = fp.winding_number(circle, 0, return_certificate=True)
    badw = type(w)(w.contour, w.point, w.winding, sp.S.Zero)
    assert not badw.verify()


def test_multipuncture_homotopy_orientation_and_deformation():
    t, z = sp.symbols("t z", real=True)
    c1 = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    c2 = fp.ParametricContour(3 * (sp.cos(t) + sp.I * sp.sin(t)), (t, 0, 2 * sp.pi))
    cert = fp.homotopic(c1, c2, punctures=(-1, 1), return_certificate=True)
    assert cert is not None and cert.verify()
    assert cert.reduced_word in ((1, 2), (2, 1))
    assert fp.homotopic(c1, c1.reversed(), punctures=(-1, 1)) is False
    deformation = fp.deform_contour(
        1 / ((z - 1) * (z + 1)), z, c1, c2, return_certificate=True
    )
    assert deformation is not None and deformation.verify()
