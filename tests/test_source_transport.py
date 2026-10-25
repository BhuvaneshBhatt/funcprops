"""Held source semantics survive worker inputs, outputs and checkpoints."""

import pickle

import pytest
import sympy as sp

import funcprops as fp
from funcprops._source_transport import _dumps
from funcprops.work_budget import _messages

x, y, a = sp.symbols("x y a", real=True)


def held_quotient():
    return sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)


@pytest.mark.parametrize(
    "source",
    [
        held_quotient(),
        sp.Add(x, -x, evaluate=False),
        sp.log(x, 2, evaluate=False),
        sp.exp(sp.log(0, evaluate=False), evaluate=False),
        sp.Mul(0, sp.Pow(x - 1, -1, evaluate=False), evaluate=False),
        sp.Eq(held_quotient(), 1, evaluate=False),
        sp.Piecewise((held_quotient(), x < 1), (x, True), evaluate=False),
        sp.Derivative(sp.sin(x), x, evaluate=False),
        sp.Contains(x, sp.S.Reals, evaluate=False),
    ],
)
def test_source_roundtrip(source):
    restored = pickle.loads(_dumps(source))
    assert type(restored) is type(source) and sp.srepr(restored) == sp.srepr(source)


def test_worker_domain_hole():
    assert fp.domain(held_quotient(), x, work_budget=20) == sp.Ne(x, 0)
    assert (
        fp.range(held_quotient(), x, y, constraints=sp.Eq(x, 0), work_budget=20)
        is sp.S.false
    )


def test_worker_finite_proof():
    result = fp.lipschitz(
        held_quotient(),
        x,
        domain=sp.FiniteSet(0, 1),
        return_result=True,
        work_budget=20,
    )
    assert result.constant == 0 and result.domain == sp.FiniteSet(1)
    assert result.expression == held_quotient() and result.verify()
    assert result.proof.requested == sp.FiniteSet(0, 1)


def test_worker_domain_record():
    record = fp.track_domain(held_quotient(), x, sp.Interval(0, 1), work_budget=20)
    assert record.expression == held_quotient() and record.verify()
    assert record.effective == sp.Interval.Lopen(0, 1)


def test_worker_guarded_family_hole():
    raw = sp.Add(
        x * x,
        sp.Mul(0, sp.Pow(x - a, -1, evaluate=False), evaluate=False),
        evaluate=False,
    )
    with pytest.raises(ValueError):
        fp.certify_parameter_geometry(raw, x, (a,), work_budget=20)


def test_checkpoint_source_roundtrip():
    proof = fp.certify_finite_lipschitz(held_quotient(), x, sp.FiniteSet(0, 1))
    messages = _messages(_dumps(("checkpoint", proof)) + _dumps(("ok", proof)))
    assert [kind for kind, _ in messages] == ["checkpoint", "ok"]
    for _, restored in messages:
        assert (
            restored.expression == held_quotient()
            and restored.effective == sp.FiniteSet(1)
        )
        assert restored.verify()


def test_specialized_containers():
    source = sp.Poly(x * x - sp.sqrt(2), x, extension=sp.sqrt(2))
    restored = pickle.loads(_dumps(source))
    assert restored == source and restored.domain == source.domain
