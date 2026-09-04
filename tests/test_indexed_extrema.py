import sympy as sp
from sympy import S

from funcprops import (
    Boundedness,
    ExtremumRange,
    IndexedExtremumValue,
    IndexedZero,
    extremum_geometry,
    function_boundedness,
    function_range,
    symbolic_extremum_range,
)

x, y = sp.symbols("x y", real=True)


def test_airy_indexed_extremum_family():
    e = extremum_geometry(sp.airyai(x), x)
    assert e and e[0].complete
    z = e[0].extrema[0]
    assert isinstance(z, IndexedExtremumValue)
    assert z.point.derivative_order == 1
    assert z.value == sp.airyai(z.point)


def test_bessel_indexed_extremum_family():
    e = extremum_geometry(sp.besselj(0, x), x, domain=sp.Interval.open(0, sp.oo))
    assert e and e[0].alternating is True
    assert e[0].extrema[0].point.family == "BesselJ"


def test_closed_bounded_exact_critical_range():
    r = symbolic_extremum_range(x**3 - 3 * x, x, sp.Interval(-2, 2))
    assert isinstance(r, ExtremumRange)
    assert r.complete and r.lower == -2 and r.upper == 2
    assert r.lower_attained is True and r.upper_attained is True
    assert r.as_condition(y) == sp.And(y >= -2, y <= 2)


def test_function_range_uses_finite_extrema():
    r = function_range(x**3 - 3 * x, x, y, constraints=sp.And(x >= -2, x <= 2))
    assert sp.simplify_logic(sp.Equivalent(r, sp.And(y >= -2, y <= 2))) is S.true


def test_bessel_semiaxis_range_is_exact_indexed_envelope():
    r = function_range(sp.besselj(0, x), x, y, constraints=x > 0)
    # 0.13 simplifies the indexed envelope using exact extremum ordering.
    expected_lower = sp.besselj(0, IndexedZero("BesselJ", 2, 0, 1, "positive"))
    assert (
        sp.simplify_logic(sp.Equivalent(r, sp.And(y >= expected_lower, y < 1)))
        is S.true
    )


def test_airy_negative_semiaxis_range_is_indexed_not_false():
    r = function_range(sp.airyai(x), x, y, constraints=x <= 0)
    lo = sp.airyai(IndexedZero("AiryAi", 2, S.NaN, 1, "negative"))
    hi = sp.airyai(IndexedZero("AiryAi", 1, S.NaN, 1, "negative"))
    assert sp.simplify_logic(sp.Equivalent(r, sp.And(y >= lo, y <= hi))) is S.true


def test_indexed_extremum_range_drives_boundedness():
    assert (
        function_boundedness(sp.besselj(0, x), x, domain=x > 0) == Boundedness.BOUNDED
    )
    assert function_boundedness(sp.airyai(x), x, domain=x <= 0) == Boundedness.BOUNDED


def test_open_finite_interval_keeps_attainment_unknown():
    r = symbolic_extremum_range(x**2, x, sp.Interval.open(-1, 1))
    assert r.complete
    assert r.lower == 0 and r.upper == 1
    assert r.lower_attained is True and r.upper_attained is False
    assert r.as_condition(y) == sp.And(y >= 0, y < 1)
