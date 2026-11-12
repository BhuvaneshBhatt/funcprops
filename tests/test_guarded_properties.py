"""Guarded analytic/relation results and exact affine metric metadata."""

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.sign import prove_relation

x, a = sp.symbols("x a", real=True)


def test_guarded_analyticity():
    result = fp.analytic(sp.log(x), x, domain=(a > 0) & (x > 0), return_result=True)
    assert isinstance(result, fp.PropertyResult)
    active = [
        case.value
        for case in result.cases
        if sp.simplify(case.condition.subs(a, 1)) is sp.S.true
    ]
    assert active == [fp.Analyticity.ANALYTIC]
    assert (
        fp.analytic(sp.log(x), x, domain=(a > 0) & (x > 0), assumptions=a > 0)
        is fp.Analyticity.ANALYTIC
    )


@pytest.mark.parametrize(
    "relation,expected",
    [
        (
            sp.Gt(a, 0),
            {1: fp.TruthValue.TRUE, 0: fp.TruthValue.FALSE, -1: fp.TruthValue.FALSE},
        ),
        (
            sp.Eq(a, 0),
            {1: fp.TruthValue.FALSE, 0: fp.TruthValue.TRUE, -1: fp.TruthValue.FALSE},
        ),
    ],
)
def test_guarded_relation(relation, expected):
    result = prove_relation(relation, x)
    assert (
        isinstance(result, fp.PropertyResult) and result.source == "relation-from-sign"
    )
    for value, truth in expected.items():
        active = [
            case.value
            for case in result.cases
            if sp.simplify(case.condition.subs(a, value)) is sp.S.true
        ]
        assert active == [truth]


@pytest.mark.parametrize(
    "support", [sp.S.Reals, sp.Interval.open(0, 1), sp.Interval(0, sp.oo)]
)
@pytest.mark.parametrize("slope", [-3, sp.sqrt(2)])
def test_affine_optimality(support, slope):
    result = fp.lipschitz(slope * x + 2, x, domain=support, return_result=True)
    assert result.constant == abs(slope) and result.optimal is fp.TruthValue.TRUE
    assert result.verify() is False


def test_singleton_constant():
    result = fp.lipschitz(3 * x + 2, x, domain=sp.FiniteSet(1), return_result=True)
    assert (
        result.constant == 0
        and result.optimal is fp.TruthValue.TRUE
        and result.verify()
    )


@pytest.mark.parametrize("known_width", [False, True])
def test_affine_interval_width(known_width):
    b = a + 1 if known_width else sp.Symbol("b", real=True)
    result = fp.lipschitz(3 * x + 2, x, domain=sp.Interval(a, b), return_result=True)
    assert result.constant == 3 and result.value is fp.TruthValue.TRUE
    expected = fp.TruthValue.TRUE if known_width else fp.TruthValue.UNKNOWN
    assert result.optimal is expected


def test_relation_source_hole():
    raw = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    relation = sp.Eq(raw, 1, evaluate=False)
    assert prove_relation(relation, x, domain=sp.FiniteSet(0)) is fp.TruthValue.UNKNOWN
    assert prove_relation(relation, x, domain=sp.FiniteSet(1)) is fp.TruthValue.TRUE


@pytest.mark.parametrize("factor", [-2, -1, 1, sp.sqrt(2)])
def test_held_zero_reality(factor):
    from funcprops.certified_inequalities import certify_inequality
    from funcprops.domain_tracking import track_domain

    zero = sp.Mul(factor, sp.S.Zero, evaluate=False)
    raw = sp.Add(x**2, zero, evaluate=False)
    support = sp.Interval(-1, 1)
    record = track_domain(raw, x, support)
    assert record.complete and record.effective == support and record.verify()
    proof = certify_inequality(raw, 0, x, support, relation=">=", max_depth=0)
    assert proof.classification is fp.TruthValue.TRUE and proof.verify()


def test_zero_product_hole():
    from funcprops.domain_tracking import track_domain

    raw = sp.Mul(sp.S.Zero, sp.Pow(x, -1, evaluate=False), evaluate=False)
    support = sp.Interval(-1, 1)
    record = track_domain(raw, x, support)
    assert record.complete and record.effective == support - sp.FiniteSet(0)
    assert record.verify()
