import sympy as sp

import funcprops as fp


def circle(radius, t):
    return fp.ParametricContour(radius * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))


def test_argument_principle_matches_divisor_winding():
    z = sp.Symbol("z")
    t = sp.Symbol("t", real=True)
    contour = circle(3, t)
    function = (z - 1) ** 2 / ((z + 1) * (z - 4))
    expected = (
        2 * fp.winding_number(contour, 1)
        - fp.winding_number(contour, -1)
        - fp.winding_number(contour, 4)
    )
    assert fp.argument_principle(function, z, contour) == expected == 1


def test_residue_matches_contour_integral():
    z, t = sp.symbols("z t")
    contour = circle(1, t)
    function = sp.exp(z) / z
    result = fp.integrate(function, (z, contour), return_result=True)
    assert result.certified
    expected = 2 * sp.pi * sp.I * fp.residue(function, z, 0)
    error = abs(complex(sp.N(result.value - expected, 30)))
    assert error <= float(sp.N(result.error_bound, 30))


def test_monodromy_matches_winding():
    z, t = sp.symbols("z t")
    contour = circle(1, t)
    winding = fp.winding_number(contour, 0)
    continued = fp.monodromy(sp.log(z), z, contour)
    assert sp.simplify(continued - sp.log(z) - 2 * sp.pi * sp.I * winding) == 0
