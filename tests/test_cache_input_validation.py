import sympy as sp

from funcprops.proof_cache import cached_zero_geometry


def test_zero_geometry_rejects_fractional_derivative_order():
    x = sp.symbols("x", real=True)
    for bad_order in (0.5, sp.Rational(1, 2), True):
        try:
            cached_zero_geometry(sp.sin(x), x, derivative_order=bad_order)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid derivative order accepted: {bad_order!r}")
