"""Guard partitions, source definition guards, and proof/completeness status."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import Periodicity, Symmetry, TruthValue
from funcprops.results import DetailedPropertyResult, PropertyResult

x, y, a, b = sp.symbols("x y a b", real=True)
u, v = sp.symbols("u v")


@pytest.mark.parametrize(
    "av,bv,expected",
    [
        (0, 0, Symmetry.BOTH),
        (0, 1, Symmetry.EVEN),
        (1, 0, Symmetry.ODD),
        (1, 1, Symmetry.NEITHER),
    ],
)
def test_exhaustive_polynomial_parity_cases(av, bv, expected):
    expr = a * x + b * x * x
    result = fp.symmetry(expr, x, return_result=True)
    selected = [
        c.value for c in result.cases if c.condition.subs({a: av, b: bv}) is sp.S.true
    ]
    assert selected == [expected]
    assert result.complete and result.certified
    assert fp.symmetry(expr, x, assumptions=sp.Eq(a, av) & sp.Eq(b, bv)) is expected
    assert fp.verify_certificate(result, expr=expr, var=x)


def test_guarded_symmetry_replays_parameter_assumptions():
    expr = a * x + x * x
    result = fp.symmetry(expr, x, assumptions=sp.Ne(a, 0), return_result=True)
    assert result.classification is Symmetry.NEITHER
    assert fp.verify_certificate(result, expr=expr, var=x)
    assert not fp.verify_certificate(replace(result, cases=()), expr=expr, var=x)
    assert not fp.verify_certificate(
        replace(result, cases=result.cases[:1]), expr=expr, var=x
    )


def test_polynomial_periodicity_partition_and_projection():
    expr = a * x + b
    result = fp.periodicity(expr, x, return_result=True)
    assert result.classification is Periodicity.UNKNOWN
    assert result.complete and result.certified
    assert {c.value for c in result.cases} == {
        Periodicity.CONSTANT,
        Periodicity.APERIODIC,
    }
    assert fp.verify_certificate(result, expr=expr, var=x)
    detail = fp.as_detailed_result(result)
    assert (
        detail.complete is True and detail.certified is True and detail.has_certificate
    )
    assert detail.cases == result.cases
    assert not fp.verify_certificate(
        replace(result, cases=result.cases[:1]), expr=expr, var=x
    )


def test_conditional_frequency_status_and_projection():
    result = fp.periodicity(sp.sin(u * x), x, return_result=True)
    assert result.certified is True and result.complete is False
    assert {c.value for c in result.cases} == {
        Periodicity.PERIODIC,
        Periodicity.UNKNOWN,
    }
    assert fp.verify_certificate(result, expr=sp.sin(u * x), var=x)
    assert fp.as_detailed_result(result).complete is False


@pytest.mark.parametrize("query", [fp.injective, fp.surjective, fp.bijective])
def test_affine_reality_rank_cases_and_assumptions(query):
    result = query((u * x + v, y), (x, y), return_result=True)
    assert isinstance(result, PropertyResult)
    assert result.complete is False and result.certified is True
    for c in result.cases:
        if c.value is not TruthValue.UNKNOWN:
            assert c.condition.has(sp.Q.real(u)) and c.condition.has(sp.Q.real(v))
    assume = sp.Q.real(u) & sp.Q.real(v) & sp.Ne(u, 0)
    assert query((u * x + v, y), (x, y), assumptions=assume) is TruthValue.TRUE
    detail = query((u * x + v, y), (x, y), assumptions=assume, return_result=True)
    assert (
        detail.primary is TruthValue.TRUE
        and detail.complete is True
        and detail.certified is True
    )


def test_partial_real_rank_cases_become_complete_under_reality_only():
    result = fp.surjective(
        (u * x, y), (x, y), assumptions=sp.Q.real(u), return_result=True
    )
    assert result.complete is True and result.certified is True
    assert {c.value for c in result.cases} == {TruthValue.TRUE, TruthValue.FALSE}


@pytest.mark.parametrize("kind", ["division", "log", "gamma"])
def test_source_parameter_poles_survive_affine_extraction(kind):
    if kind == "division":
        expr = sp.Mul(x, a, sp.Pow(a, -1, evaluate=False), evaluate=False)
    else:
        term = sp.log(a) if kind == "log" else sp.gamma(a)
        expr = sp.Add(x, term, -term, evaluate=False)
    result = fp.bijective((expr, y), (x, y), return_result=True)
    assert isinstance(result, PropertyResult)
    # A guarded true branch cannot cover an explicitly undefined source.
    for c in result.cases:
        if c.value is TruthValue.TRUE:
            assert c.condition is not sp.S.true
    assert (
        fp.bijective((expr, y), (x, y), assumptions=sp.Eq(a, 0)) is not TruthValue.TRUE
    )


def test_coordinate_holes_cannot_be_parameter_guards():
    expr = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    assert fp.surjective((expr, y), (x, y)) is TruthValue.UNKNOWN


@pytest.mark.parametrize(
    "query,expected",
    [(fp.periodicity, Periodicity.UNKNOWN), (fp.symmetry, Symmetry.UNKNOWN)],
)
def test_cancelled_log_definition_survives_polynomial_cases(query, expected):
    expr = sp.Add(x, sp.log(a), -sp.log(a), evaluate=False)
    result = query(expr, x, assumptions=sp.Eq(a, 0), return_result=True)
    assert result.classification is expected
    assert result.complete is False and result.certified is False
    assert fp.verify_certificate(result, expr=expr, var=x)


@pytest.mark.parametrize(
    "query,expected",
    [(fp.periodicity, Periodicity.UNKNOWN), (fp.symmetry, Symmetry.UNKNOWN)],
)
def test_polynomial_parameter_denominator_is_not_defined_at_zero(query, expected):
    result = query(x / a, x, assumptions=sp.Eq(a, 0), return_result=True)
    assert result.classification is expected
    assert result.complete is False and result.certified is False


def test_local_root_certification():
    result = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    assert result.complete and result.certified and result.has_certificate
    partial = replace(result, complete=False)
    assert partial.complete is False and partial.certified is True
    detail = fp.as_detailed_result(partial)
    assert (
        detail.complete is False and detail.certified is True and detail.has_certificate
    )
    fabricated = replace(result, certificates=(), isolated_intervals=())
    assert (
        fabricated.complete is True
        and fabricated.certified is False
        and not fabricated.has_certificate
    )


def test_detailed_certificate_presence_is_not_verification():
    record = DetailedPropertyResult(
        TruthValue.UNKNOWN, complete=False, certificate=object(), certified=None
    )
    assert (
        record.has_certificate and record.certified is None and record.complete is False
    )
    html = record._repr_html_()
    assert "Certificate" in html and "recorded" in html
    assert "Certified" not in html


def test_status_fields_survive_general_projection_and_budget_expiry():
    record = PropertyResult(TruthValue.UNKNOWN, complete=False, certified=False)
    detail = fp.as_detailed_result(record)
    assert detail.complete is False and detail.certified is False
    result = fp.range(sp.exp(x), x, y, work_budget=0.001, return_result=True)
    assert result.complete is False and result.certified is False
    detail = fp.as_detailed_result(result)
    assert detail.complete is False and detail.certified is False


def test_missing_guarded_cases():
    for query, expr in ((fp.periodicity, a * x), (fp.symmetry, a * x + b * x * x)):
        c = query(expr, x, return_result=True)
        assert c.complete and c.certified
        assert not fp.verify_certificate(replace(c, cases=()), expr=expr, var=x)
        assert not fp.verify_certificate(replace(c, complete=False), expr=expr, var=x)


def test_fabricated_root_count():
    r = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    cert = replace(r.certificates[0], root_count=100)
    fabricated = replace(r, certificates=(cert,))
    assert (
        fabricated.complete and fabricated.has_certificate and not fabricated.certified
    )


def test_verified_root_count_does_not_certify_corrupted_root_values():
    r = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    assert r.evidence_certified and r.certified
    corrupted = replace(r, roots=(sp.Integer(99),))
    assert corrupted.evidence_certified and not corrupted.certified
    partial = replace(r, roots=r.roots[:1], complete=False)
    assert partial.evidence_certified and partial.certified and not partial.complete


def test_local_evidence_projection():
    from funcprops.transcendental.roots import (
        CertifiedRootInterval,
        RootCertificate,
        RootIsolationResult,
    )

    item = CertifiedRootInterval(
        sp.Interval(0, 1), RootCertificate(sp.Interval(0, 1), 1, "unbound-example")
    )
    record = RootIsolationResult(isolated_intervals=(item,), complete=False)
    assert (
        record.has_certificate
        and record.has_local_certificates
        and not record.certified
    )
    detail = fp.as_detailed_result(record)
    assert (
        detail.has_certificate
        and detail.certified is False
        and detail.complete is False
    )
