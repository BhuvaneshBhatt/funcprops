import sympy as sp

from funcprops import (
    Analyticity,
    FunctionSlot,
    Monotonicity,
    PropertyRule,
    Sign,
    TransportedPropertyRule,
    transport_instantiated_rule,
)


class F(sp.Function):
    nargs = 1


def test_sign_fact_substitutes_through_unary_composition():
    z = FunctionSlot(0, "z")
    rule = PropertyRule(F, "sign", z, conditions=z > 0, result=Sign.POSITIVE)
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(F(x**2)), x)
    assert isinstance(out, TransportedPropertyRule)
    assert out.subject_map.expressions == (x**2,)
    assert out.conditions == (x**2 > 0)
    assert out.result is Sign.POSITIVE
    assert out.complete is True


def test_zero_set_is_pulled_back_through_inner_map():
    z = FunctionSlot(0, "z")
    rule = PropertyRule(F, "zeros", z, result=sp.FiniteSet(1, 4))
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(F(x**2)), x, domain=sp.S.Reals)
    assert out.complete is True
    assert out.result == sp.FiniteSet(-2, -1, 1, 2)


def test_monotonicity_composes_directions():
    z = FunctionSlot(0, "z")
    rule = PropertyRule(
        F,
        "monotonicity",
        z,
        conditions=z > 0,
        result=Monotonicity.STRICTLY_DECREASING,
    )
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(
        rule.instantiate(F(sp.exp(x))), x, domain=sp.S.Reals
    )
    assert out.result is Monotonicity.STRICTLY_DECREASING
    assert out.complete is True


def test_analyticity_requires_analytic_inner_map():
    z = FunctionSlot(0, "z")
    rule = PropertyRule(F, "analyticity", z, result=Analyticity.ANALYTIC)
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(F(sp.exp(x))), x)
    assert out.result is Analyticity.ANALYTIC
    assert out.complete is True


def test_unary_subject_map_remains_available_after_p3_extension():
    z = FunctionSlot(0, "z")
    rule = PropertyRule(F, "sign", z, result=Sign.POSITIVE)
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(F(x**2)), x)
    assert out.subject_map.expressions == (x**2,)
    assert out.subject_map.tangent == (2 * x,)
