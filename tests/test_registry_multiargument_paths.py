import pytest
import sympy as sp

from funcprops import (
    Analyticity,
    DerivativeRule,
    FunctionRegistry,
    FunctionSlot,
    Monotonicity,
    PropertyRule,
    Sign,
    SubjectMap,
    registry_derivative,
    registry_gradient,
    transport_instantiated_rule,
)


class G(sp.Function):
    nargs = 2


def _gradient_registry():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    return FunctionRegistry(
        [],
        derivative_rules=[
            DerivativeRule(G, u, 2 * u + v),
            DerivativeRule(G, v, u),
        ],
    )


def test_subject_map_tracks_multiargument_scalar_path_and_tangent():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    rule = PropertyRule(G, "sign", (u, v), result=Sign.POSITIVE)
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(G(x**2, sp.exp(x))), x)
    assert isinstance(out.subject_map, SubjectMap)
    assert out.subject_map.source_slots == (u, v)
    assert out.subject_map.expressions == (x**2, sp.exp(x))
    assert out.subject_map.tangent == (2 * x, sp.exp(x))
    assert out.result is Sign.POSITIVE
    assert out.complete is True


def test_registered_gradient_is_certified_for_multiargument_outer():
    reg = _gradient_registry()
    u, v = sp.symbols("u v")
    cert = registry_gradient(G(u, v), registry=reg)
    assert cert.complete is True
    assert cert.gradient == (2 * u + v, u)
    assert cert.positions == (0, 1)
    assert cert.missing_positions == ()
    assert cert.verify() is True


def test_path_derivative_is_gradient_dot_tangent():
    reg = _gradient_registry()
    x = sp.symbols("x", real=True)
    cert = registry_derivative(G(x**2, sp.exp(x)), x, registry=reg)
    expected = (2 * x**2 + sp.exp(x)) * 2 * x + x**2 * sp.exp(x)
    assert cert.complete is True
    assert cert.gradient_certificate is not None
    assert cert.gradient_certificate.gradient == (2 * x**2 + sp.exp(x), x**2)
    assert sp.simplify(cert.derivative - expected) == 0
    assert cert.verify() is True


def test_joint_finite_zero_set_pulls_back_along_path():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    rule = PropertyRule(
        G,
        "zeros",
        (u, v),
        result=sp.FiniteSet(sp.Tuple(1, 1), sp.Tuple(4, 2)),
    )
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(
        rule.instantiate(G(x**2, x)), x, domain=sp.S.Reals
    )
    assert out.complete is True
    assert out.result == sp.FiniteSet(1, 2)


def test_multiargument_analyticity_requires_each_path_component_analytic():
    pytest.importorskip("semialg")
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    rule = PropertyRule(G, "analyticity", (u, v), result=Analyticity.ANALYTIC)
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(G(sp.exp(x), x**2 + 1)), x)
    assert out.complete is True
    assert out.result is Analyticity.ANALYTIC


def test_multiargument_monotonicity_can_be_certified_from_path_derivative():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    reg = FunctionRegistry(
        [],
        derivative_rules=[
            DerivativeRule(G, u, 1),
            DerivativeRule(G, v, 1),
        ],
    )
    rule = PropertyRule(G, "monotonicity", (u, v), result=Monotonicity.UNKNOWN)
    x = sp.symbols("x", positive=True)
    out = transport_instantiated_rule(
        rule.instantiate(G(x, x**2)), x, domain=sp.Interval.open(0, sp.oo), registry=reg
    )
    assert out.complete is True
    assert out.result is Monotonicity.STRICTLY_INCREASING
    assert any(item[0] == "chain-rule" for item in out.evidence)


def test_missing_gradient_component_refuses_multiargument_monotonicity():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    reg = FunctionRegistry([], derivative_rules=[DerivativeRule(G, u, 1)])
    rule = PropertyRule(G, "monotonicity", (u, v), result=Monotonicity.UNKNOWN)
    x = sp.symbols("x", real=True)
    out = transport_instantiated_rule(rule.instantiate(G(x, x**2)), x, registry=reg)
    assert out.complete is False
    assert out.result is Monotonicity.UNKNOWN


def test_multiple_analysis_variables_are_still_not_smuggled_in():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    rule = PropertyRule(G, "sign", (u, v), result=Sign.POSITIVE)
    x, y = sp.symbols("x y")
    out = transport_instantiated_rule(rule.instantiate(G(x, y)), x)
    assert out.analysis_variables == (x,)
    assert out.subject_map.tangent == (1, 0)
