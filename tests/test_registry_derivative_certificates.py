import sympy as sp

from funcprops import (
    ChainRuleCertificate,
    DerivativeRule,
    FunctionRegistry,
    FunctionSlot,
    IdentityRule,
    registry_derivative,
    rewrite_with_registry,
)


class F(sp.Function):
    nargs = 1


class G(sp.Function):
    nargs = 2


def test_identity_rule_localizes_slots():
    z = FunctionSlot(0, "z")
    reg = FunctionRegistry([], identity_rules=[IdentityRule(F, z**2 + 1)])
    x = sp.symbols("x")
    out = rewrite_with_registry(F(x + 1), registry=reg)
    assert out.replacement == (x + 1) ** 2 + 1
    assert out.conditions is sp.S.true


def test_unary_chain_rule_certificate():
    z = FunctionSlot(0, "z")
    reg = FunctionRegistry([], derivative_rules=[DerivativeRule(F, z, 2 * z)])
    x = sp.symbols("x")
    cert = registry_derivative(F(x**2), x, registry=reg)
    assert isinstance(cert, ChainRuleCertificate)
    assert cert.complete is True
    assert sp.expand(cert.derivative) == 4 * x**3
    assert cert.verify(registry=reg) is True
    assert cert.terms[0].argument_position == 0


def test_multivariate_outer_chain_rule_sums_partial_terms():
    u = FunctionSlot(0, "u")
    v = FunctionSlot(1, "v")
    reg = FunctionRegistry(
        [],
        derivative_rules=[
            DerivativeRule(G, u, 2 * u + v),
            DerivativeRule(G, v, u),
        ],
    )
    x = sp.symbols("x")
    cert = registry_derivative(G(x**2, sp.exp(x)), x, registry=reg)
    expected = (2 * x**2 + sp.exp(x)) * 2 * x + x**2 * sp.exp(x)
    assert cert.complete is True
    assert sp.simplify(cert.derivative - expected) == 0
    assert len(cert.terms) == 2


def test_preserves_derivative_rule_conditions():
    z = FunctionSlot(0, "z")
    reg = FunctionRegistry(
        [], derivative_rules=[DerivativeRule(F, z, 1 / z, conditions=z > 0)]
    )
    x = sp.symbols("x", real=True)
    cert = registry_derivative(F(x**2), x, registry=reg)
    assert cert.complete is True
    assert cert.conditions == (x**2 > 0)


def test_missing_partial_derivative_is_incomplete_not_guessed():
    u = FunctionSlot(0, "u")
    reg = FunctionRegistry([], derivative_rules=[DerivativeRule(G, u, 2 * u)])
    x = sp.symbols("x")
    cert = registry_derivative(G(x, x**2), x, registry=reg)
    assert cert.complete is False
    assert cert.derivative is None


def test_shared_derivative_cache_consumes_unconditional_native_rule():
    from funcprops import registry
    from funcprops.proof_cache import cached_derivative

    class H(sp.Function):
        nargs = 1

    z = FunctionSlot(0, "z")
    registry().register_derivative_rule(DerivativeRule(H, z, 3 * z**2))
    x = sp.symbols("x")
    assert sp.expand(cached_derivative(H(x**2), x)) == 6 * x**5
