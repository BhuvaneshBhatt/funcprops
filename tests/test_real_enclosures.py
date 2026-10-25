from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops.coverage_checker import regular_on_cell
from funcprops.enclosures import _enclosure_leaf

x = s.Symbol("x", real=True)
D = s.Interval(0, 1)


@pytest.mark.parametrize(
    "f,region",
    [
        (s.exp(x), D),
        (s.sin(x), s.Interval(-2, 2)),
        (s.cos(x), s.Interval(-2, 2)),
        (s.log(x), s.Interval(1, 2)),
        (x**s.pi, s.Interval(1, 2)),
        (x ** s.sqrt(2), s.Interval(1, 2)),
        (s.Abs(x), s.Interval(-1, 1)),
        (s.sinh(x), D),
        (s.cosh(x), D),
        (s.tanh(x), D),
        (s.erf(x), s.Interval(-2, 2)),
        (s.erfc(x), s.Interval(-2, 2)),
        (s.exp(s.erf(x)), D),
        (s.erf(s.log(x)), s.Interval(1, 2)),
        (s.sqrt(x), D),
        ((1 + x) / (2 + x * x), D),
    ],
)
def test_nested_primitive_enclosures(f, region):
    coarse = fp.enclose_expression(
        f, x, region, policy=fp.EnclosurePolicy(precision=12, max_precision=12)
    )
    refined = fp.enclose_expression(
        f,
        x,
        region,
        policy=fp.EnclosurePolicy(precision=12, max_precision=48, max_refinements=2),
    )
    assert coarse.verify() is True and refined.verify() is True
    assert fp.replay_status(refined).certified is True
    assert fp.replay_status(refined.witnesses[0]).certified is True
    assert coarse.lower <= refined.lower <= refined.upper <= coarse.upper
    # Sampling is a numerical cross-check, not the certificate's proof premise.
    for point in (region.start, (region.start + region.end) / 2, region.end):
        value = f.subs(x, point).evalf(80)
        assert (value - s.N(refined.lower, 80)).is_nonnegative is True
        assert (s.N(refined.upper, 80) - value).is_nonnegative is True


@pytest.mark.parametrize("point", [s.Rational(-5, 2), -1, 0, s.Rational(1, 3), 1, 3])
def test_erf_erfc_exact_remainder_enclosures(point):
    region = s.FiniteSet(point)
    erf = fp.enclose_expression(
        s.erf(x),
        x,
        region,
        policy=fp.EnclosurePolicy(precision=25, max_precision=50, max_refinements=1),
    )
    erfc = fp.enclose_expression(
        s.erfc(x),
        x,
        region,
        policy=fp.EnclosurePolicy(precision=25, max_precision=50, max_refinements=1),
    )
    assert erf.verify() and erfc.verify()
    assert erf.upper - erf.lower < s.Rational(1, 10**45)
    assert erfc.lower <= 1 - erf.upper <= 1 - erf.lower <= erfc.upper


def test_series_budget_exhaustion():
    r = fp.enclose_expression(
        s.erf(x), x, D, policy=fp.EnclosurePolicy(max_series_terms=0)
    )
    assert not r.certified and r.witnesses == () and r.obligations
    r = fp.enclose_expression(s.erfi(x), x, D)
    assert not r.certified and "unsupported-primitive:erfi" in r.obligations
    assert fp.replay_status(r).certified is None


@pytest.mark.parametrize(
    "f,region",
    [
        (s.log(x), s.Interval(-1, 1)),
        (x**s.pi, s.Interval(-2, -1)),
        (s.sqrt(x), s.Interval(-1, 1)),
        (1 / x, s.Interval(-1, 1)),
        (s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False), s.Interval(-1, 1)),
    ],
)
def test_source_hole_enclosures(f, region):
    r = fp.enclose_expression(f, x, region)
    assert not r.certified and r.obligations


def test_source_holes_and_log_boundary_split_effective_domain():
    raw = s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)
    p = fp.prove_root_coverage(raw, x, s.Interval(-1, 1))
    assert p.verify() and p.root_count == 0 and p.complete
    assert p.context.effective == s.Union(
        s.Interval.Ropen(-1, 0), s.Interval.Lopen(0, 1)
    )
    assert not p.context.effective.contains(0)
    q = fp.prove_root_coverage(
        s.log(x),
        x,
        s.Interval(-1, 1),
        policy=fp.EnclosurePolicy(max_depth=1, max_cells=8),
    )
    assert q.verify() and q.context.effective == s.Interval.Lopen(0, 1)
    assert not q.complete and q.unresolved.contains(0) is s.S.false


def test_owned_piecewise_singleton_is_a_separate_cell():
    f = s.Piecewise((s.exp(x), x < 0), (0, s.Eq(x, 0)), (x * x + 1, True))
    p = fp.prove_root_coverage(f, x, s.Interval(-1, 1))
    assert p.verify() and p.complete and p.root_count == 1
    assert any(a.region == s.FiniteSet(0) and a.root_count == 1 for a in p.leaves)
    assert not replace(
        p, leaves=tuple(a for a in p.leaves if a.region != s.FiniteSet(0))
    ).verify()


def test_piecewise_hole_ownership():
    raw = s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)
    f = s.Piecewise((raw, x <= 0), (s.exp(x), True), evaluate=False)
    p = fp.prove_root_coverage(f, x, s.Interval(-1, 1))
    assert p.verify() and p.complete and p.root_count == 0
    assert p.context.effective == s.Interval(-1, 1) - s.FiniteSet(0)
    g = s.Piecewise((raw, x < 0), (x, True), evaluate=False)
    q = fp.prove_root_coverage(g, x, s.Interval(-1, 1))
    assert (
        q.verify()
        and q.complete
        and q.root_count == 1
        and q.context.effective == s.Interval(-1, 1)
    )


def test_grammar_reports_float_parameters_and_unsupported_primitives():
    for f in [s.Float(".1") * x, s.besselj(0, x), x**x, s.Symbol("a") + x]:
        r = fp.enclose_expression(f, x, D)
        assert not r.certified and r.obligations


def test_cache_premise_keys():
    fp.clear_caches()
    a = fp.enclose_expression(
        s.erf(x), x, D, policy=fp.EnclosurePolicy(max_precision=30)
    )
    b = fp.enclose_expression(
        s.erf(x), x, D, policy=fp.EnclosurePolicy(max_precision=30, max_series_terms=0)
    )
    assert a.certified and not b.certified
    before = _enclosure_leaf.cache_info()
    c = fp.enclose_expression(
        s.erf(x), x, D, policy=fp.EnclosurePolicy(max_precision=30)
    )
    assert c == a and _enclosure_leaf.cache_info().hits > before.hits
    positive = s.Symbol("x", positive=True)
    assert not fp.enclose_expression(positive, positive, s.Interval(-1, 1)).certified


@pytest.mark.parametrize(
    "kwargs",
    [
        {"precision": True},
        {"precision": 1},
        {"max_cells": -1},
        {"max_depth": True},
        {"max_series_terms": -1},
        {"seconds": 0},
        {"seconds": float("inf")},
    ],
)
def test_invalid_effort_policy_is_rejected(kwargs):
    with pytest.raises(ValueError):
        fp.EnclosurePolicy(**kwargs)


def test_wall_budget_query_context():
    for operation in (fp.prove_root_coverage, fp.enclose_expression):
        result = operation(s.erf(x), x, D, policy=fp.EnclosurePolicy(seconds=0.001))
        assert result.complete is False and result.certified is False
        assert result.source == "work-budget-exhausted" and result.query
        assert fp.replay_status(result).outcome == "resource-exhaustion"


def test_erf_derivative_enclosure():
    assert regular_on_cell(s.erf(x), x, D, 3)
    derivative = s.diff(s.erf(x), x)
    r = fp.enclose_expression(derivative, x, D)
    assert r.verify() and r.lower > 0
    bad = s.erf(1 / x)
    assert not regular_on_cell(bad, x, s.Interval(-1, 1), 1)


@pytest.mark.parametrize(
    "f,region,expected",
    [
        (s.erf(x), D, 2 * s.exp(-x * x) / s.sqrt(s.pi)),
        (x**s.pi, s.Interval(1, 2), s.pi * x ** (s.pi - 1)),
        (s.Abs(x), s.Interval(1, 2), s.S.One),
        (s.Abs(x), s.Interval(-2, -1), -s.S.One),
    ],
)
def test_source_bound_derivative_enclosures(f, region, expected):
    result = fp.enclose_derivative(f, x, region)
    assert result.verify() is True and s.simplify(result.derivative - expected) == 0
    assert fp.replay_status(result).certified is True
    assert fp.replay_status(result).schema_version == 1
    assert not replace(result, expression=f + 1, source_syntax=s.srepr(f)).verify()
    assert not replace(result, derivative=s.S.Zero).verify()


@pytest.mark.parametrize(
    "f", [s.Abs(x), s.sqrt(x), s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)]
)
def test_derivative_sources_cannot_lose_corners_or_holes(f):
    result = fp.enclose_derivative(f, x, s.Interval(-1, 1))
    assert not result.verify() and result.obligations
    assert fp.replay_status(result).outcome == "unsupported-replay"


def test_composed_log_erf_branch_uses_checked_local_domain_evidence():
    f = s.log(s.erf(x)) - s.log(s.Rational(9, 10))
    region = s.Interval(1, 2)
    p = fp.prove_root_coverage(f, x, region)
    assert p.verify() and p.complete and p.root_count == 1
    record = p.context.domain_record
    assert isinstance(record, fp.CellDomainWitness) and record.verify()
    assert not replace(record, cells=()).verify()
    assert not replace(record, requested=s.Interval(0, 2)).verify()
    assert fp.replay_status(replace(record, schema_version=2)).certified is None
    bad = fp.prove_root_coverage(f, x, s.Interval(-1, 1))
    assert not bad.complete and bad.check().certified is not True


@pytest.mark.parametrize(
    "f", [s.exp(x) - 2, s.erf(x) - s.Rational(1, 2), s.erfc(x) - s.Rational(1, 2)]
)
def test_compact_acceptance_examples_have_checked_counts(f):
    p = fp.prove_root_coverage(f, x, D)
    assert p.verify() and p.complete and p.root_count == 1
