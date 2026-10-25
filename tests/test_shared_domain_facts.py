"""Shared source domains support endpoint, guard and held-log consumers."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.proof_cache import cached_domain_record, property_proof_context

x = sp.Symbol("x", real=True)


@pytest.mark.parametrize("exponent", [sp.sqrt(2), sp.pi, sp.E, -sp.sqrt(2), -sp.pi])
@pytest.mark.parametrize(
    "support",
    [
        sp.Interval(-1, 2),
        sp.Interval.open(0, 2),
        sp.FiniteSet(-1, 0, 1),
        sp.Union(sp.Interval(-3, -2), sp.Interval(0, 2)),
    ],
)
def test_principal_power_endpoints(exponent, support):
    expression = x**exponent
    natural = sp.Interval(0, sp.oo) if exponent > 0 else sp.Interval.open(0, sp.oo)
    record = fp.track_domain(expression, x, support)
    assert record.complete and record.natural_complete and record.verify()
    assert record.natural == natural
    assert record.effective == sp.Intersection(support, natural)
    assert not replace(record, effective=sp.FiniteSet(-1)).verify()


def test_power_retains_canceled_hole():
    canceled = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    expression = sp.Mul(canceled, x ** sp.sqrt(2), evaluate=False)
    record = fp.track_domain(expression, x, sp.Interval(0, 2))
    assert record.complete and record.verify()
    assert record.effective == sp.Interval.Lopen(0, 2)


@pytest.mark.parametrize(
    "expression,expected",
    [
        (sp.Piecewise((1, sp.log(x) > 0), (0, True)), sp.Interval.Lopen(0, 2)),
        (sp.Piecewise((1, x <= 0), (2, sp.log(x) > 0), (3, True)), sp.Interval(-2, 2)),
        (sp.Piecewise((1 / x, sp.log(x) > 0), (0, True)), sp.Interval.Lopen(0, 2)),
        (sp.Piecewise((x ** sp.sqrt(2), x >= 0), (-x, True)), sp.Interval(-2, 2)),
        (sp.Piecewise((1, sp.log(x, 0, evaluate=False) > 0), (0, True)), sp.S.EmptySet),
    ],
)
def test_piecewise_guard_coverage(expression, expected):
    record = fp.track_domain(expression, x, sp.Interval(-2, 2))
    assert record.complete and record.verify()
    assert record.effective == expected
    if expected is sp.S.EmptySet:
        assert record.natural_complete and record.natural is sp.S.EmptySet
    else:
        assert not record.natural_complete and record.natural is None


def test_unsupported_guards_stay_unresolved():
    guard = sp.Contains(sp.Function("unknown")(x), sp.S.Reals, evaluate=False)
    expression = sp.Piecewise((x, guard), (0, True))
    assert not fp.track_domain(expression, x, sp.Interval(-1, 1)).complete


@pytest.mark.parametrize("base", [2, sp.Rational(1, 2)])
def test_held_log_regularity(base):
    expression = sp.log(x, base, evaluate=False)
    support = sp.Interval(2, 4)
    continuity = fp.continuous(expression, x, domain=support, return_result=True)
    assert continuity.primary is fp.Continuity.CONTINUOUS
    assert continuity.domain_record.expression == expression
    assert continuity.domain_record.effective == support
    assert continuity.domain_record.verify()
    assert fp.lipschitz(expression, x, domain=support) == 1 / (2 * sp.log(2))
    assert fp.uniformly_continuous(expression, x, domain=support) is fp.TruthValue.TRUE


def test_normalized_constant_keeps_source_domain():
    expression = sp.log(x, x, evaluate=False)
    result = fp.continuous(expression, x, domain=sp.Interval(2, 3), return_result=True)
    assert result.primary is fp.Continuity.CONTINUOUS
    assert result.domain_record.expression == expression
    assert result.domain_record.verify()
    assert (
        fp.continuous(sp.log(x, 0, evaluate=False), x, domain=sp.Interval(2, 3))
        is not fp.Continuity.CONTINUOUS
    )


def test_domain_cache_is_premise_sensitive():
    fp.clear_caches()
    expression = x ** sp.sqrt(2)
    support = sp.Interval(0, 1)
    first = cached_domain_record(expression, x, support)
    context = property_proof_context(expression, x, domain=support)
    shared = context.domain_record()
    assert context.domain_record() is shared
    assert shared.requested == sp.Contains(x, support)
    assert shared.effective == first.effective and shared.expression == first.expression
    assert cached_domain_record(expression, x, sp.Interval(-1, 1)).effective == support
    held = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    assert cached_domain_record(held, x, support).effective == sp.Interval.Lopen(0, 1)
    assert fp.cache_info()["domain_record"].hits >= 1
    fp.clear_caches()
    assert fp.cache_info()["domain_record"].currsize == 0


def test_positive_parameter_power_endpoint():
    exponent = sp.Symbol("q", positive=True)
    result = fp.track_domain(x**exponent, x, sp.Interval(0, 1))
    assert result.complete and result.verify()
    assert result.effective == sp.Interval(0, 1)
    assert result.natural is None and result.natural_complete is False
    unknown = sp.Symbol("r", real=True)
    assert not fp.track_domain(x**unknown, x, sp.Interval(0, 1)).complete


def test_canceled_guard_keeps_its_hole():
    unit = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    expression = sp.Piecewise(
        (x, sp.Eq(unit, 1, evaluate=False)), (1, True), evaluate=False
    )
    result = fp.track_domain(expression, x, sp.Interval(-1, 1))
    assert result.complete and result.verify()
    assert result.effective == sp.Interval(-1, 1) - sp.FiniteSet(0)
    assert not replace(result, effective=sp.Interval(-1, 1)).verify()


def test_cached_request_types_remain_bound():
    implicit = cached_domain_record(x, x, None)
    explicit = cached_domain_record(x, x, True)
    assert implicit.requested is None and explicit.requested is True
    assert implicit.effective == explicit.effective == sp.S.Reals


@pytest.mark.parametrize(
    "terms,natural",
    [
        ((1, 1), sp.S.Reals),
        ((-1, -1), sp.S.Reals - sp.FiniteSet(0)),
        ((1, -1), sp.S.Reals),
    ],
)
def test_compound_integer_exponents(terms, natural):
    exponent = sp.Add(*terms, evaluate=False)
    expression = sp.Pow(x, exponent, evaluate=False)
    record = fp.track_domain(expression, x)
    assert record.complete and record.verify()
    assert record.natural == record.effective == natural
    condition = fp.domain(expression, x)
    from funcprops.real_analysis.common import condition_to_set

    assert condition_to_set(condition, x) == natural


def test_unclassified_exponent_has_no_false_global_domain():
    exponent = sp.log(4) / sp.log(2)
    expression = sp.Pow(x, exponent, evaluate=False)
    result = fp.track_domain(expression, x)
    if result.complete:
        assert result.effective == sp.S.Reals
    else:
        assert result.natural is None and result.effective is None
    local = fp.track_domain(expression, x, sp.Interval(0, 1))
    assert local.complete and local.effective == sp.Interval(0, 1) and local.verify()
