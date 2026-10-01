import sympy as sp

from funcprops import (
    Monotonicity,
    PropertyResult,
    as_detailed_result,
    cache_info,
    change_of_variables,
    clear_caches,
    explain_result,
    monotonicity,
)


def test_assumptions_collapse_parameter_strata():
    a, x = sp.symbols("a x", real=True)
    result = monotonicity(a * x, x, assumptions=a > 0)
    assert result is Monotonicity.STRICTLY_INCREASING


def test_detailed_result_exposes_self_verifying_certificate():
    x = sp.symbols("x", real=True)
    cert = change_of_variables((2 * x,), x)
    detail = as_detailed_result(cert)
    assert detail.primary == cert.classification
    assert detail.certificate is cert
    assert "Certificate: ChangeOfVariablesCertificate" in explain_result(cert)


def test_property_result_resolved_value():
    result = PropertyResult(primary=Monotonicity.STRICTLY_INCREASING)
    assert result.resolved is Monotonicity.STRICTLY_INCREASING
    assert result.as_detailed_result().resolved is Monotonicity.STRICTLY_INCREASING


def test_unified_cache_management():
    x = sp.symbols("x", real=True)
    monotonicity(x**2, x)
    before = cache_info()
    assert "derivative" in before
    assert all(hasattr(info, "hits") for info in before.values())
    clear_caches()
    after = cache_info()
    assert all(info.currsize == 0 for info in after.values())
