import sympy as sp

from funcprops import (
    AnalysisSubject,
    Convexity,
    DerivativeRule,
    FunctionRegistry,
    FunctionSlot,
    HessianCertificate,
    JacobianCertificate,
    MultivariateChainRuleCertificate,
    PropertyRule,
    Sign,
    SubjectMap,
    registry_chain_rule,
    registry_hessian,
    registry_jacobian,
    transport_instantiated_rule,
)


class G(sp.Function):
    nargs = 2


def _quadratic_registry():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    return FunctionRegistry(
        [],
        derivative_rules=[
            DerivativeRule(G, u, 2 * u),
            DerivativeRule(G, v, 4 * v),
        ],
    )


def test_analysis_subject_validates_multivariate_variables():
    x, y = sp.symbols("x y", real=True)
    subject = AnalysisSubject((x, y), domain=sp.And(x > 0, y > 0))
    assert subject.variables == (x, y)


def test_subject_map_exposes_full_jacobian():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    x, y = sp.symbols("x y", real=True)
    rule = PropertyRule(G, "sign", (u, v), result=Sign.POSITIVE)
    out = transport_instantiated_rule(rule.instantiate(G(x + y, x - y)), (x, y))
    assert isinstance(out.subject_map, SubjectMap)
    assert out.subject_map.jacobian == sp.ImmutableMatrix([[1, 1], [1, -1]])
    assert out.analysis_variables == (x, y)
    assert out.complete is True


def test_registry_jacobian_is_replayable():
    x, y = sp.symbols("x y", real=True)
    cert = registry_jacobian((x**2 + y, sp.exp(y)), (x, y))
    assert isinstance(cert, JacobianCertificate)
    assert cert.jacobian == sp.ImmutableMatrix([[2 * x, 1], [0, sp.exp(y)]])
    assert cert.verify() is True


def test_registered_outer_hessian_from_partial_rules():
    reg = _quadratic_registry()
    u, v = sp.symbols("u v", real=True)
    cert = registry_hessian(G(u, v), registry=reg)
    assert isinstance(cert, HessianCertificate)
    assert cert.complete is True
    assert cert.hessian == sp.ImmutableMatrix([[2, 0], [0, 4]])
    assert cert.verify() is True


def test_multivariate_chain_rule_gradient_and_hessian():
    reg = _quadratic_registry()
    x, y = sp.symbols("x y", real=True)
    cert = registry_chain_rule(G(x + y, x - y), (x, y), registry=reg, second_order=True)
    assert isinstance(cert, MultivariateChainRuleCertificate)
    assert cert.complete is True
    assert cert.gradient == sp.ImmutableMatrix([6 * x - 2 * y, -2 * x + 6 * y])
    assert cert.hessian == sp.ImmutableMatrix([[6, -2], [-2, 6]])
    assert cert.verify() is True


def test_convexity_transport_uses_composite_hessian_certificate():
    reg = _quadratic_registry()
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    x, y = sp.symbols("x y", real=True)
    rule = PropertyRule(G, "convexity", (u, v), result=Convexity.CONVEX)
    out = transport_instantiated_rule(
        rule.instantiate(G(x + y, x - y)), (x, y), registry=reg
    )
    assert out.complete is True
    assert out.result is Convexity.STRONGLY_CONVEX
    assert out.subject_map.jacobian == sp.ImmutableMatrix([[1, 1], [1, -1]])


def test_missing_outer_partial_refuses_second_order_transport():
    u = FunctionSlot(0, "u")
    reg = FunctionRegistry([], derivative_rules=[DerivativeRule(G, u, 2 * u)])
    x, y = sp.symbols("x y", real=True)
    cert = registry_chain_rule(G(x, y), (x, y), registry=reg, second_order=True)
    assert cert.complete is False
    assert cert.hessian is None


def test_multivariate_pointwise_sign_transport_is_direct():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    x, y = sp.symbols("x y", real=True)
    rule = PropertyRule(
        G, "sign", (u, v), conditions=(u > 0) & (v > 0), result=Sign.POSITIVE
    )
    out = transport_instantiated_rule(rule.instantiate(G(x**2, y**2)), (x, y))
    assert out.complete is True
    assert out.conditions == ((x**2 > 0) & (y**2 > 0))
    assert out.result is Sign.POSITIVE
