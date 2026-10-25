from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
P = fp.EnclosurePolicy(precision=20, max_precision=80, max_refinements=2, max_cells=500)


@pytest.mark.parametrize(
    "f,count",
    [
        (sp.exp(x) - x * x, 1),
        (sp.exp(x) - 4 * x * x, 3),
        (sp.exp(-x) - x * x, 1),
        (sp.exp(x) + sp.exp(-x) - 3, 2),
        (2 * sp.exp(x) - sp.exp(x / 2) - 3, 1),
        (sp.exp(x) - sp.exp(x / 2) + 1, 0),
    ],
)
def test_full_core_and_both_tail_covers(f, count):
    r = fp.infinite_root_coverage(f, x, policy=P)
    assert r.complete and r.root_count == count and r.verify() and r.certified
    tails = [a for a in r.proof.leaves if a.theorem == "exponential-tail"]
    assert {a.witness.direction for a in tails} == {-1, 1}
    assert sp.Union(*(a.region for a in r.proof.leaves)) == sp.S.Reals
    assert fp.replay_status(r).outcome == "complete-coverage"


def test_unproved_tail_and_core_are_retained_and_resumable():
    r = fp.infinite_root_coverage(
        sp.exp(x) - 4 * x * x, x, policy=replace(P, max_depth=0, max_cells=4)
    )
    assert not r.complete and r.root_count is None and r.verify()
    assert r.unresolved is not sp.S.EmptySet
    again = fp.resume_root_coverage(r, policy=P)
    assert again.complete and again.root_count == 3 and again.verify()
    assert all(a in again.proof.leaves for a in r.proof.leaves)


def test_tail_witness_mutations_and_independent_replay(monkeypatch):
    r = fp.infinite_root_coverage(sp.exp(x) - x * x, x, policy=P)
    leaf = next(a for a in r.proof.leaves if a.theorem == "exponential-tail")
    w = leaf.witness
    for altered in (
        replace(w, direction=-w.direction),
        replace(w, sign=-w.sign),
        replace(w, threshold=0),
        replace(w, constant_lower=10**20),
        replace(w, remainder_upper=0),
        replace(w, groups=()),
    ):
        assert not replace(leaf, witness=altered).verify()
    assert not replace(
        r.proof, leaves=tuple(a for a in r.proof.leaves if a != leaf)
    ).verify()

    def disabled(*args, **kwargs):
        raise AssertionError("tail proposal called during replay")

    monkeypatch.setattr("funcprops.infinite_roots.propose_tail", disabled)
    monkeypatch.setattr("funcprops.adaptive_roots._proposal", disabled)
    assert r.verify()


@pytest.mark.parametrize("cap", [0, 1, 2])
def test_insufficient_work_does_not_complete_infinite_domain(cap):
    r = fp.infinite_root_coverage(
        sp.exp(x) - 4 * x * x, x, policy=replace(P, max_cells=cap)
    )
    assert not r.complete and r.root_count is None and r.verify()
    assert r.state.exhaustion == "cell-budget"


def test_unsupported_tail_grammar_stays_unresolved():
    r = fp.infinite_root_coverage(
        sp.exp(sp.sin(x)) - x, x, policy=replace(P, max_cells=8)
    )
    assert not r.complete and r.unresolved == sp.S.Reals and r.root_count is None


def test_half_line_and_raw_cancelled_hole():
    for D, count in ((sp.Interval(0, sp.oo), 0), (sp.Interval(-sp.oo, 0), 1)):
        r = fp.infinite_root_coverage(sp.exp(x) - x * x, x, D, policy=P)
        assert r.complete and r.root_count == count and r.verify()
    held = sp.Mul(sp.exp(x) - x * x, x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    r = fp.infinite_root_coverage(held, x, policy=P)
    assert r.complete and r.root_count == 1 and r.verify()
    assert r.proof.context.effective.contains(0) is sp.S.false


def test_hard_timeout_has_full_pending_domain():
    r = fp.infinite_root_coverage(
        sp.exp(x) - 4 * x * x, x, policy=replace(P, seconds=0.001)
    )
    assert not r.complete and r.unresolved == sp.S.Reals
    assert r.state.exhaustion == "wall-budget"
    assert fp.resume_root_coverage(r, policy=P).root_count == 3
