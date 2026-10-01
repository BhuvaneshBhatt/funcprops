import sympy as sp
from sympy import S

from funcprops import (
    ExtremumOrderingTheorem,
    ExtremumRange,
    IndexedZero,
    extremum_ordering_theorems,
    range,
    symbolic_extremum_range,
)

x, y = sp.symbols("x y", real=True)


def test_airy_ordering_theorem_is_exact_and_derived():
    t = extremum_ordering_theorems(sp.airyai(x), x)[0]
    assert isinstance(t, ExtremumOrderingTheorem)
    assert t.magnitude_direction == "decreasing"
    assert t.global_max_index == 1 and t.global_min_index == 2
    assert "Airy energy" in t.proof


def test_airy_envelope_collapses_to_first_two_extrema_on_negative_halfline():
    r = symbolic_extremum_range(sp.airyai(x), x, sp.Interval(-sp.oo, 0))
    assert isinstance(r, ExtremumRange) and r.complete
    assert r.lower.func is sp.airyai and isinstance(r.lower.args[0], IndexedZero)
    assert r.lower.args[0].index == 2
    assert r.upper.args[0].index == 1
    assert r.lower_attained is True and r.upper_attained is True
    assert r.as_condition(y) == sp.And(y >= r.lower, y <= r.upper)


def test_airy_full_real_range_uses_same_global_extrema():
    r = symbolic_extremum_range(sp.airyai(x), x, S.Reals)
    assert r.complete
    assert r.lower.func is sp.airyai and r.lower.args[0].index == 2
    assert r.upper.func is sp.airyai and r.upper.args[0].index == 1


def test_bessel_j0_positive_semiaxis_collapses_exactly():
    r = symbolic_extremum_range(sp.besselj(0, x), x, sp.Interval.open(0, sp.oo))
    assert r.complete
    assert r.lower.func is sp.besselj
    assert r.lower.args[1].index == 2
    assert r.upper == 1
    assert r.lower_attained is True and r.upper_attained is False
    assert r.as_condition(y) == sp.And(y >= r.lower, y < 1)


def test_bessel_j_positive_order_first_two_extrema_dominate():
    r = symbolic_extremum_range(sp.besselj(1, x), x, sp.Interval.open(0, sp.oo))
    assert r.complete
    assert r.upper.func is sp.besselj and r.upper.args[1].index == 1
    assert r.lower.func is sp.besselj and r.lower.args[1].index == 2
    assert r.lower_attained is True and r.upper_attained is True


def test_range_collapses_j0_envelope():
    r = range(sp.besselj(0, x), x, y, constraints=x > 0)
    if isinstance(r, ExtremumRange):
        assert r.as_condition(y) is not None
        assert r.upper == 1 and r.upper_attained is False


def test_bessel_y0_positive_semiaxis_first_max_dominates():
    r = symbolic_extremum_range(sp.bessely(0, x), x, sp.Interval.open(0, sp.oo))
    assert r.complete and r.lower is -sp.oo
    assert r.upper.func is sp.bessely and r.upper.args[1].index == 1
    assert r.upper_attained is True


def test_airy_bi_full_real_first_minimum_dominates():
    r = symbolic_extremum_range(sp.airybi(x), x, S.Reals)
    assert r.complete and r.upper is sp.oo
    assert r.lower.func is sp.airybi and r.lower.args[0].index == 1
    assert r.lower_attained is True
