import sympy as sp

from funcprops import (
    CertifiedIntegerBracket,
    IndexedZero,
    indexed_tail_integer_bracket,
    indexed_tail_inversion,
)


def test_besselj_function_tail_integer_bracket():
    k = sp.symbols("k", integer=True, positive=True)
    z = IndexedZero("BesselJ", k, sp.Integer(0), 0, "positive")
    b = indexed_tail_integer_bracket(z, sp.Integer(10))
    assert isinstance(b, CertifiedIntegerBracket)
    assert b.lower == 4 and b.upper == 4
    assert b.exact


def test_besselj_derivative_tail_integer_bracket():
    k = sp.symbols("k", integer=True, positive=True)
    z = IndexedZero("BesselJ", k, sp.Integer(1), 1, "positive")
    b = indexed_tail_integer_bracket(z, sp.Integer(100))
    assert b.lower <= b.upper
    assert b.lower == 31 and b.upper == 33


def test_tail_certificate_carries_bracket():
    k = sp.symbols("k", integer=True, positive=True)
    z = IndexedZero("BesselJ", k, sp.Integer(0), 0, "positive")
    c = indexed_tail_inversion(z, sp.Integer(10))
    assert c.first_index == 4
    assert c.integer_bracket.exact
    assert c.integer_bracket.lower == 4


def test_unsupported_airy_does_not_fake_asymptotic_bracket():
    k = sp.symbols("k", integer=True, positive=True)
    z = IndexedZero("AiryAi", k, sp.S.NaN, 1, "negative")
    assert indexed_tail_integer_bracket(z, -100, direction="left") is None


def test_strict_tail_bracket_semantics():
    k = sp.symbols("k", integer=True, positive=True)
    z = IndexedZero("BesselJ", k, sp.Integer(0), 0, "positive")
    #  pi is an upper bound for j_{0,1}; strict inversion cannot certify k=1
    # from that upper bound, but the resulting bracket remains rigorous.
    b = indexed_tail_integer_bracket(z, sp.pi, direction="right", inclusive=False)
    assert b.lower <= b.upper
