import sympy as sp

from funcprops.results import SingularityKind
from funcprops.singularities.geometry import _multivariate_denominator_records
from funcprops.singularities.records import _denominator_singularity_records, order_at


def test_opaque_univariate_numerator():
    x = sp.symbols("x")
    f = sp.Function("f")
    assert order_at(f(x) / x, x, 0) is None
    poles, removable = _denominator_singularity_records(f(x) / x, x)
    assert removable == ()
    assert len(poles) == 1
    assert poles[0].kind is SingularityKind.POLE
    assert poles[0].condition == sp.Eq(x, 0)
    assert poles[0].guard == sp.Ne(f(0), 0)


def test_opaque_multivariate_numerator():
    x, y = sp.symbols("x y")
    f = sp.Function("f")
    records = _multivariate_denominator_records(f(x + y) / (x + y), (x, y))
    assert len(records) == 1
    assert records[0].kind is SingularityKind.POLE
    assert records[0].condition == sp.Eq(x + y, 0)
    assert records[0].guard is not sp.S.true


def test_local_order_certifies_nonzero_leading_coefficients():
    x = sp.symbols("x")
    assert order_at(sp.sin(x) / x**3, x, 0) == -2
    assert order_at((1 + x) / x**2, x, 0) == -2


def test_affine_periodicity_requires_real_frequency():
    from funcprops.real_analysis.structural_properties import periodicity
    from funcprops.results import Periodicity

    x, a = sp.symbols("x a")
    result = periodicity(sp.sin(a * x), x, return_result=True)
    assert result.classification is Periodicity.PERIODIC
    assert result.conditions.has(sp.Q.real(a))
    assert result.conditions.has(sp.Ne(a, 0))

    nonreal = periodicity(sp.sin((1 + sp.I) * x), x, return_result=True)
    assert nonreal.classification is Periodicity.UNKNOWN
