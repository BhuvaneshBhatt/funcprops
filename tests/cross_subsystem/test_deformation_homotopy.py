import sympy as sp

import funcprops as fp


def test_deformation_uses_all_poles():
    z, t = sp.symbols("z t", real=True)
    first = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    second = fp.ParametricContour(3 * (sp.cos(t) + sp.I * sp.sin(t)), (t, 0, 2 * sp.pi))
    function = 1 / ((z - 1) * (z + 1))
    homotopy = fp.homotopic(first, second, punctures=(-1, 1), return_certificate=True)
    deformation = fp.deform_contour(function, z, first, second, return_certificate=True)
    assert homotopy.verify()
    assert deformation.verify()
    assert deformation.punctures == (-1, 1)


def test_crossing_pole_changes_class():
    z, t = sp.symbols("z t", real=True)
    outer = fp.ParametricContour(2 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    inner = fp.ParametricContour(
        sp.Rational(1, 2) * sp.exp(sp.I * t), (t, 0, 2 * sp.pi)
    )
    assert fp.deform_contour(1 / (z - 1), z, outer, inner) is False
