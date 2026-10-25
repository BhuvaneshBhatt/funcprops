"""Bounded held trees retain source holes through transport and recovery."""

import pickle
from dataclasses import replace

import pytest
import sympy as sp
from hypothesis import given
from hypothesis import strategies as st

import funcprops as fp
from funcprops._source_transport import _dumps
from funcprops.work_budget import _messages

x = sp.Symbol("x", real=True)


@st.composite
def held_sources(draw):
    hole = draw(st.integers(-2, 2))
    base = x - hole
    raw = sp.Mul(base, sp.Pow(base, -1, evaluate=False), evaluate=False)
    for choice in draw(
        st.lists(st.sampled_from(["exp", "sin", "zero", "sum"]), max_size=3)
    ):
        if choice == "exp":
            raw = sp.exp(raw, evaluate=False)
        elif choice == "sin":
            raw = sp.sin(raw, evaluate=False)
        elif choice == "zero":
            raw = sp.Mul(0, raw, evaluate=False)
        else:
            raw = sp.Add(raw, x, evaluate=False)
    return raw, hole


@given(held_sources())
def test_held_tree_roundtrip(data):
    raw, hole = data
    restored = pickle.loads(_dumps((raw, sp.Gt(raw, 0, evaluate=False))))
    assert sp.srepr(restored[0]) == sp.srepr(raw)
    assert sp.srepr(restored[1]) == sp.srepr(sp.Gt(raw, 0, evaluate=False))
    assert sp.simplify(fp.domain(restored[0], x).subs(x, hole)) is sp.S.false


@pytest.mark.parametrize("hole", [-1, 0, 1])
def test_worker_matches_direct(hole):
    base = x - hole
    source = sp.exp(
        sp.Mul(base, sp.Pow(base, -1, evaluate=False), evaluate=False), evaluate=False
    )
    direct = fp.domain(source, x)
    assert direct == sp.Ne(x, hole)
    assert fp.domain(source, x, work_budget=30) == direct


def test_partial_checkpoint_frame():
    raw = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    proof = fp.certify_finite_lipschitz(raw, x, sp.FiniteSet(0, 1))
    frames = _dumps(("checkpoint", proof)) + _dumps(("ok", proof))[:-10]
    messages = _messages(frames)
    assert len(messages) == 1 and messages[0][0] == "checkpoint"
    restored = messages[0][1]
    assert (
        restored.expression == raw
        and restored.effective == sp.FiniteSet(1)
        and restored.verify()
    )
    assert not replace(restored, effective=sp.FiniteSet(0, 1)).verify()


def test_nested_proof_records():
    proof = fp.certify_finite_lipschitz(x * x, x, sp.FiniteSet(0, 1, 2))
    result = pickle.loads(_dumps({"proofs": (proof, [proof])}))
    assert result["proofs"][0].constant == 3 and result["proofs"][1][0].verify()
