import sympy as sp

import funcprops as fp


def test_essential_argument_principle_unknown():
    z, t = sp.symbols("z t")
    contour = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    assert fp.argument_principle(sp.exp(1 / z), z, contour) is None


def test_open_homotopy_unknown():
    t = sp.symbols("t", real=True)
    first = fp.ParametricContour(t, (t, 0, 1))
    second = fp.ParametricContour(t**2, (t, 0, 1))
    assert fp.homotopic(first, second, punctures=(2, 3)) is None


def test_unresolved_transcendental_cut_geometry_unknown():
    t = sp.symbols("t", real=True)
    first = fp.ParametricContour(3 * sp.exp(sp.I * (t + sp.sin(t))), (t, 0, 2 * sp.pi))
    second = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    assert fp.homotopic(first, second, punctures=(-1, 1)) is None
