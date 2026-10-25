from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.parameter_cells import refine_parameter_cells
from funcprops.results import ConditionalExpression, PropertyResult, TruthValue

x, a = sp.symbols("x a", real=True)


def test_m2_m3_wrappers_expose_consistent_certified_fields():
    r = fp.adaptive_root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 1))
    z = sp.Symbol("z")
    c = fp.certify_complex_cluster(sp.exp(z) - 1, z, 0, sp.Rational(1, 2))
    assert r.certified and r.state.certified and c.certified


def test_unsupported_branch_state_cannot_be_resumed_as_complete():
    r = fp.adaptive_root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 1))
    bad = replace(
        r.state,
        context=replace(r.state.context, branch_context=object()),
        pending=(),
        leaves=(),
    )
    with pytest.raises(ValueError):
        fp.resume_root_coverage(bad)


def test_m3_mutable_witness_payloads_do_not_pass_frozen_contract():
    c = fp.deflate_real_root(sp.exp(x) - 1 - x, x, sp.Interval(-1, 1), 0, 2)
    assert c.verify()
    assert not replace(
        c, witness=replace(c.witness, jets=list(c.witness.jets))
    ).verify()
    z = sp.Symbol("z")
    p = fp.certify_complex_cluster(sp.exp(z) - 1, z, 0, sp.Rational(1, 2))
    assert not replace(p, coefficient_bounds=list(p.coefficient_bounds)).verify()


@pytest.mark.parametrize("function", [sp.asin, sp.acos])
def test_inverse_phase_bounds_keep_endpoint_regularities_distinct(function):
    c = fp.enclose_derivative(function(x), x, sp.Interval(-1, 1), order=0)
    assert c.verify()
    assert not fp.enclose_derivative(function(x), x, sp.Interval(-1, 1)).verify()
    assert fp.enclose_derivative(
        function(x), x, sp.Interval(-sp.Rational(1, 2), sp.Rational(1, 2))
    ).verify()
    assert not fp.enclose_expression(function(x), x, sp.Interval(1, 2)).verify()


def test_factory_quadratic_helper_retains_linear_degree_drop():
    p = fp.quadratic_discriminant_cells(a * x * x + x + 1, x, a)
    selected = [c.value for c in p.cases if c.condition.subs(a, 0) is sp.S.true]
    assert selected == [1]
    q = fp.quadratic_discriminant_cells(a * x * x + a * x + a, x, a)
    selected = [c.value for c in q.cases if c.condition.subs(a, 0) is sp.S.true]
    assert selected == [sp.oo]


@pytest.mark.parametrize("cap", [0, 1, 2])
def test_factory_refinement_budget_preserves_original_parameter_space(cap):
    p = PropertyResult(
        None,
        (
            ConditionalExpression(TruthValue.TRUE, a >= 0),
            ConditionalExpression(TruthValue.FALSE, a < 0),
        ),
    )
    q = refine_parameter_cells(p, (a,), split_sign=True, max_cells=cap)
    for value, expected in (
        (-1, TruthValue.FALSE),
        (0, TruthValue.TRUE),
        (1, TruthValue.TRUE),
    ):
        selected = [c.value for c in q.cases if c.condition.subs(a, value) is sp.S.true]
        assert selected == [expected]


def test_parameter_source_binding():
    raw = sp.Add(
        sp.exp(x),
        a,
        sp.Mul(0, sp.Pow(a, -1, evaluate=False), evaluate=False),
        evaluate=False,
    )
    assert fp.exponential_affine_transition_cells(raw, x, a) is None
    assert fp.exponential_affine_transition_cells(sp.exp(x) + x, x, x) is None
    assert fp.quadratic_discriminant_cells(x * x + x, x, x) is None


def test_transition_locus_binding():
    from funcprops.parameter_discriminants import polynomial_transition_locus

    assert polynomial_transition_locus(x * x + x / a + 1, x) is None
    c = polynomial_transition_locus(x * x - a, x)
    assert c.verify() and not replace(c, parameters=()).verify()
    assert polynomial_transition_locus(x * x - a, x, parameters=(x,)) is None


def test_exp_linear_strata_check_real_coefficients_and_zero_slope():
    from funcprops.parameter_discriminants import exp_linear_root_strata

    assert exp_linear_root_strata(sp.exp(x) + sp.I * x + 1, x, sp.I, 1) is None
    cases = exp_linear_root_strata(sp.exp(x) - 1, x, 0, -1)
    assert [count for count, guard in cases if guard is sp.S.true] == [1]


def test_nonreal_quadratic_coefficients():
    c = sp.Symbol("c", real=False)
    assert fp.quadratic_discriminant_cells(c * x * x + x + 1, x, c) is None


def test_nonrational_polynomial_fallback():
    for query, D in (
        (fp.prove_root_coverage, sp.Interval(2, 3)),
        (fp.adaptive_root_coverage, sp.Interval(2, 3)),
        (fp.infinite_root_coverage, sp.S.Reals),
    ):
        r = query(x - sp.E, x, D)
        assert r.complete and r.root_count == 1 and r.verify()
