import sympy as sp

from funcprops.native_registry import native_registry_snapshot
from funcprops.registry import adapt_catalogue_rule_case, registry
from funcprops.registry_derivatives import registry_derivative, rewrite_with_registry
from funcprops.results import Analyticity


def test_native_special_function_rules_are_installed():
    reg = registry()
    assert reg.property_rules(head=sp.erf, property="analyticity")
    assert reg.derivative_rules(head=sp.airyai, position=0)
    assert reg.derivative_rules(head=sp.besselj, position=1)


def test_erf_and_airy_derivatives_feed_chain_rule():
    x = sp.symbols("x")
    erf_cert = registry_derivative(sp.erf(x**2), x)
    assert erf_cert.complete
    assert (
        sp.simplify(erf_cert.derivative - 4 * x * sp.exp(-(x**4)) / sp.sqrt(sp.pi)) == 0
    )

    airy_cert = registry_derivative(sp.airyai(sp.exp(x)), x)
    assert airy_cert.complete
    assert (
        sp.simplify(airy_cert.derivative - sp.exp(x) * sp.airyaiprime(sp.exp(x))) == 0
    )


def test_bessel_argument_derivative_keeps_order_as_ordinary_argument():
    nu, x = sp.symbols("nu x")
    cert = registry_derivative(sp.besselj(nu, x**2), x)
    expected = x * (sp.besselj(nu - 1, x**2) - sp.besselj(nu + 1, x**2))
    assert cert.complete
    assert sp.simplify(cert.derivative - expected) == 0


def test_lambertw_optional_arity_rules_do_not_collide():
    x = sp.symbols("x")
    for expr in (sp.LambertW(x), sp.LambertW(x, 1)):
        cert = registry_derivative(expr, x)
        assert cert.complete
        assert cert.conditions is not sp.S.false


def test_identity_rules_are_exact_but_not_automatically_recursive():
    x = sp.symbols("x")
    inst = rewrite_with_registry(sp.erfc(x))
    assert inst is not None
    assert sp.simplify(inst.replacement - (1 - sp.erf(x))) == 0


def test_native_entire_property_rule_is_localized():
    x = sp.symbols("x")
    rule = registry().property_rules(head=sp.erf, property="analyticity")[0]
    inst = rule.instantiate(sp.erf(x**2))
    assert inst.subject == (x**2,)
    assert inst.result is Analyticity.ANALYTIC


def test_conservative_catalogue_case_adapter_on_real_catalogue_case():
    fam = registry().require("erf")
    case = fam.cases("LocallyAnalytic")[0]
    rule = adapt_catalogue_rule_case(sp.erf, "LocallyAnalytic", case)
    assert rule is not None
    x = sp.symbols("x")
    inst = rule.instantiate(sp.erf(x))
    assert inst.subject == (x,)
    assert inst.result is sp.S.true
    assert inst.conditions is sp.S.true


def test_native_coverage_snapshot_tracks_real_theorems():
    snap = native_registry_snapshot()
    assert snap["family_count"] >= 11
    assert snap["property_rule_counts"]["analyticity"] >= 7
    assert snap["derivative_positions"]["besselj"] == [1]
    assert snap["identity_rule_counts"]["erfc"] >= 1


def test_orthogonal_polynomial_argument_derivatives():
    x = sp.symbols("x")
    n = sp.symbols("n", integer=True, nonnegative=True)
    cases = (
        (sp.hermite(n, x), 2 * n * sp.hermite(n - 1, x)),
        (sp.laguerre(n, x), -sp.assoc_laguerre(n - 1, 1, x)),
        (sp.chebyshevt(n, x), n * sp.chebyshevu(n - 1, x)),
    )
    for expr, expected in cases:
        cert = registry_derivative(expr, x)
        assert cert.complete
        assert sp.simplify(cert.derivative - expected) == 0
