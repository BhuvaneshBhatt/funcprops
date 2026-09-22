import sympy as sp

import funcprops as fp
from funcprops.real_analysis.sign import prove_relation
from funcprops.results import (
    Boundedness,
    Convexity,
    Monotonicity,
    PropertyResult,
    Sign,
    TruthValue,
)


def _case_map(result):
    assert isinstance(result, PropertyResult)
    return {case.value: sp.simplify(case.condition) for case in result.cases}


def test_parameter_domain_strata_are_shared_across_real_properties():
    x, a = sp.symbols("x a", real=True)
    domain = sp.Or(sp.And(a > 0, x > 0), sp.And(a <= 0, x < 0))

    signs = _case_map(fp.function_sign(x, x, domain=domain))
    assert signs == {Sign.POSITIVE: a > 0, Sign.NEGATIVE: a <= 0}

    monotonicity = _case_map(fp.function_monotonicity(x**2, x, domain=domain))
    assert monotonicity == {
        Monotonicity.STRICTLY_INCREASING: a > 0,
        Monotonicity.STRICTLY_DECREASING: a <= 0,
    }

    boundedness = _case_map(fp.function_boundedness(x, x, domain=domain))
    assert boundedness == {
        Boundedness.BOUNDED_BELOW: a > 0,
        Boundedness.BOUNDED_ABOVE: a <= 0,
    }


def test_zero_sets_preserve_parameter_domain_strata():
    x, a = sp.symbols("x a", real=True)
    domain = sp.Or(sp.And(a > 0, x >= 0), sp.And(a <= 0, x > 0))
    cases = _case_map(fp.function_zeros(x, x, domain=domain))
    assert cases == {sp.FiniteSet(0): a > 0, sp.EmptySet: a <= 0}


def test_monotonic_decomposition_requires_its_validity_domain():
    x = sp.symbols("x", real=True)
    assert (
        fp.function_monotonicity(x**2, x, domain=x < 0)
        is Monotonicity.STRICTLY_DECREASING
    )
    assert (
        fp.function_monotonicity(x**2, x, domain=x > 0)
        is Monotonicity.STRICTLY_INCREASING
    )


def test_piecewise_monotonicity_checks_interface_direction():
    x = sp.symbols("x", real=True)
    upward = sp.Piecewise((x, x < 0), (x + 1, True))
    downward = sp.Piecewise((x, x < 0), (x - 1, True))

    assert fp.function_monotonicity(upward, x) is Monotonicity.NONDECREASING
    assert fp.function_monotonicity(downward, x) is Monotonicity.NOT_MONOTONE


def test_piecewise_convexity_checks_values_and_slopes_at_interfaces():
    x = sp.symbols("x", real=True)
    absolute_value = sp.Piecewise((-x, x < 0), (x, True))
    discontinuous = sp.Piecewise((x**2, x < 0), (x**2 + 1, True))

    assert fp.function_convexity(absolute_value, x) is Convexity.CONVEX
    assert fp.function_convexity(discontinuous, x) is Convexity.NEITHER


def test_structural_boundedness_uses_composition_closure():
    x = sp.symbols("x", real=True)
    assert fp.function_boundedness(sp.sin(x) + sp.cos(x), x) is Boundedness.BOUNDED


def test_affine_output_injectivity_preserves_scale_strata():
    x, a = sp.symbols("x a", real=True)
    cases = _case_map(fp.function_injective(a * x, x))
    assert cases == {TruthValue.TRUE: sp.Ne(a, 0), TruthValue.FALSE: sp.Eq(a, 0)}


def test_shared_relation_prover_reuses_sign_reasoning():
    x = sp.symbols("x", real=True)
    assert prove_relation(x**2 >= 0, x) is TruthValue.TRUE
    assert prove_relation(x**2 < 0, x) is TruthValue.FALSE


def test_convexity_details_use_one_certificate_type():
    x = sp.symbols("x", real=True)
    result = fp.function_convexity(x**2, x, return_result=True)
    certificate = result.evidence[0]

    assert isinstance(certificate, fp.ConvexityCertificate)
    assert certificate.classification is result.primary
    assert certificate.modulus == 2
    assert certificate.method == "second-derivative-bound"
