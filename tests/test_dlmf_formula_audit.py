import sympy as sp

from funcprops import (
    Analyticity,
    dlmf_audit_report,
    dlmf_facts,
    function_analytic,
    function_branchcuts,
    function_domain,
    transcendental_roots,
)
from funcprops.conditions import AIntegerQ, parse_catalogue_expression


def test_formula_audit_promotes_all_remaining_or_corrects_mapping():
    summary = dlmf_audit_report()["summary"]
    assert summary["formula_verified_core"] == 26
    assert summary["formula_verified_derived"] == 22
    assert summary["needs_formula_review"] == 0
    assert summary["dlmf_mapping_corrections"] == 1


def test_formula_audit_has_exact_equation_reference_for_jacobi_and_helper():
    jac = dlmf_audit_report("jacobi")
    assert jac["status"] == "formula-verified-core"
    assert "18.16.E1" in jac["formula_refs"]
    helper = dlmf_audit_report("HyperRep_asin1")
    assert helper["status"] == "formula-verified-derived"
    assert helper["formula_refs"] == ["15.4.E4"]


def test_marcumq_mapping_is_corrected_not_falsely_formula_verified():
    row = dlmf_audit_report("marcumq")
    assert row["status"] == "dlmf-related-not-native"
    assert row["formula_refs"] == []


def test_dlmf_facts_exposes_formula_level_runtime_provenance():
    refs = {f.section for f in dlmf_facts("jacobi")}
    assert "18.16.1" in refs or "18.16.E1" in refs
    refs = {f.section for f in dlmf_facts("multigamma")}
    assert "35.3.E1" in refs
    assert "35.3.E4" in refs


def test_catalogue_parser_roundtrips_semantic_predicates():
    x, y = sp.symbols("x y")
    expected = sp.And(AIntegerQ(x), AIntegerQ(y / 2))
    got = parse_catalogue_expression(sp.srepr(expected))
    assert got == expected


def test_catalogue_parser_roundtrips_boolean_relations():
    x = sp.symbols("x", real=True)
    expected = sp.And(-1 < x, x <= 1)
    got = parse_catalogue_expression(sp.srepr(expected))
    assert got == expected


def test_assoc_legendre_domain_catalogue_condition_no_longer_crashes():
    x = sp.symbols("x", real=True)
    n = sp.symbols("n", integer=True, nonnegative=True)
    dom = function_domain(sp.assoc_legendre(n, 1, x), x)
    # The exact catalogue rule is parameter-aware; the important regression is
    # that mixed parameter membership is preserved as a Boolean condition.
    assert dom is not None
    assert sp.simplify(dom.subs(x, 0)) is sp.S.true


def test_generalized_hypergeometric_entire_case_is_analytic_on_natural_complex_domain():
    z, a = sp.symbols("z a")
    expr = sp.hyper([a], [sp.Rational(3, 2)], z)  # p=q
    assert function_analytic(expr, z, domain=sp.S.Complexes) is Analyticity.ANALYTIC


def test_generalized_hypergeometric_terminating_case_suppresses_principal_cut():
    z, b, c = sp.symbols("z b c")
    expr = sp.hyper([-2, b], [c], z)  # p=q+1 but terminating polynomial
    records = function_branchcuts(expr, z, mode="records")
    assert not any(r.source == "DLMF 16.2(iii)" for r in records)


def test_associated_legendre_integer_zero_count_on_ferrers_interval():
    x = sp.symbols("x", real=True)
    n = sp.symbols("n", integer=True, positive=True)
    result = transcendental_roots(
        sp.assoc_legendre(n, 1, x),
        x,
        domain=sp.Interval.open(-1, 1),
        allow_numerical=False,
    )
    assert result.complete
    fam = result.parametric_families[0]
    assert sp.simplify(fam.count - (n - 1)) == 0
    assert fam.support == sp.Interval.open(-1, 1)


def test_associated_legendre_zero_count_is_not_claimed_complete_on_all_reals():
    x = sp.symbols("x", real=True)
    n = sp.symbols("n", integer=True, positive=True)
    result = transcendental_roots(
        sp.assoc_legendre(n, 1, x),
        x,
        domain=sp.S.Reals,
        allow_numerical=False,
    )
    assert not result.complete
    assert result.parametric_families


def test_spherical_bessel_positive_zero_family_is_certified_and_interlacing():
    x = sp.symbols("x", real=True)
    result = transcendental_roots(
        sp.jn(2, x),
        x,
        domain=sp.Interval.open(0, sp.oo),
        allow_numerical=False,
    )
    assert result.complete
    fam = result.parametric_families[0]
    assert fam.count is sp.oo
    assert fam.simple is True
    assert fam.interlaces_prev_degree is True


def test_jacobi_zero_family_carries_parameter_guard_and_interlacing():
    x = sp.symbols("x", real=True)
    n = sp.symbols("n", integer=True, positive=True)
    a, b = sp.symbols("a b", real=True)
    result = transcendental_roots(
        sp.jacobi(n, a, b, x),
        x,
        domain=sp.Interval.open(-1, 1),
        allow_numerical=False,
    )
    assert result.parametric_families
    fam = result.parametric_families[0]
    assert fam.count == n
    assert fam.simple is True
    assert fam.interlaces_prev_degree is True
    assert fam.support == sp.Interval.open(-1, 1)


def test_symbolic_chebyshev_zeros_use_exact_dlmf_indexed_formula():
    x = sp.symbols("x", real=True)
    n = sp.symbols("n", integer=True, positive=True)
    result = transcendental_roots(
        sp.chebyshevt(n, x),
        x,
        domain=sp.S.Reals,
        allow_numerical=False,
    )
    assert result.complete
    assert result.method == "dlmf_indexed_zeros"
    assert isinstance(result.evidence[0], sp.Set)


def test_incomplete_elliptic_f_parameter_branch_condition_is_recorded():
    phi = sp.symbols("phi", real=True)
    m = sp.symbols("m")
    records = function_branchcuts(sp.elliptic_f(phi, m), m, mode="records")
    assert any(r.source == "DLMF 19.2.4-19.2.5" for r in records)


def test_elliptic_pi_characteristic_does_not_get_endpoint_only_fake_cut():
    n, phi = sp.symbols("n phi", real=True)
    expr = sp.elliptic_pi(n, phi, sp.Rational(1, 2))
    records = function_branchcuts(expr, n, mode="records")
    assert not any("19.2.7 pole locus" in r.source for r in records)
