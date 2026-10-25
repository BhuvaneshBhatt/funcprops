import sympy as sp

from funcprops.complex_certification import rouche_polynomial_rectangle
from funcprops.multivariate_intervals import krawczyk_box


def test_true_nonlinear_krawczyk_diagonal_system():
    x, y = sp.symbols("x y", real=True)
    c = krawczyk_box(
        (x**2 - 2, y**2 - 3),
        (x, y),
        (
            sp.Interval(sp.Rational(7, 5), sp.Rational(3, 2)),
            sp.Interval(sp.Rational(17, 10), sp.Rational(9, 5)),
        ),
    )
    assert c.source == "interval-krawczyk" and c.verify()


def test_krawczyk_refuses_singular_or_wide_box():
    x, y = sp.symbols("x y", real=True)
    assert (
        krawczyk_box((x**2, y**2), (x, y), (sp.Interval(-1, 1), sp.Interval(-1, 1)))
        is None
    )


def test_rectangle_rouche_count():
    z = sp.symbols("z")
    c = rouche_polynomial_rectangle(z**3 + sp.Rational(1, 100), z, -1 - sp.I, 1 + sp.I)
    assert c.count == 3 and c.verify()
