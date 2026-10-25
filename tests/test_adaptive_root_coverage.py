from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import adaptive_roots as engine
from funcprops._checkpoints import capture_checkpoints
from funcprops.coverage_search import coverage_context

x = sp.Symbol("x", real=True)
POLICY = fp.EnclosurePolicy(
    precision=20, max_precision=80, max_refinements=2, max_depth=9, max_cells=400
)


@pytest.mark.parametrize(
    "f,D,count",
    [
        (sp.exp(x) - 2, sp.Interval(0, 1), 1),
        (sp.sin(x) - x / 2, sp.Interval(sp.Rational(3, 2), 2), 1),
        (sp.erf(x) - sp.Rational(1, 2), sp.Interval(0, 1), 1),
        (sp.Rational(1, 10) ** 80 * (sp.exp(x) - 2), sp.Interval(0, 1), 1),
        (sp.exp(x) - 1, sp.Interval(0, 1), 1),
        (sp.exp(x) - 1, sp.Interval.open(0, 1), 0),
        (sp.exp(x) - 1, sp.Interval.Lopen(0, 1), 0),
        (sp.exp(x) - 1, sp.Interval.Ropen(0, 1), 1),
        (
            sp.exp(x) - 2,
            sp.Union(sp.Interval(0, sp.Rational(1, 2)), sp.Interval(1, 2)),
            0,
        ),
        (sp.exp(x) - 2, sp.FiniteSet(0, 1), 0),
        (sp.exp(x) - 2, sp.S.EmptySet, 0),
    ],
)
def test_compact_examples_and_owned_boundaries(f, D, count):
    result = fp.adaptive_root_coverage(f, x, D, policy=POLICY)
    assert result.complete and result.root_count == count
    assert result.verify() and fp.verify_certificate(result)
    assert fp.replay_status(result).factory_replay is False
    assert fp.replay_status(result).outcome == "complete-coverage"


def test_contraction_retains_both_excluded_complements():
    result = fp.adaptive_root_coverage(
        sp.exp(x) - 2, x, sp.Interval(0, 1), policy=POLICY
    )
    leaves = result.proof.leaves
    assert len(leaves) == 3
    assert sum(a.root_count for a in leaves) == 1
    assert sp.Union(*(a.region for a in leaves)) == sp.Interval(0, 1)
    assert any(a.theorem == "located-subset" for a in leaves)
    assert not replace(result.proof, leaves=leaves[1:]).verify()
    assert not replace(result.proof, leaves=leaves + leaves[:1]).verify()


def test_midpoint_root_needs_no_exact_zero_oracle(monkeypatch):
    # Force a pre-existing seam through a transcendental root. The search must
    # certify a window across it, rather than decide exact equality at the seam.
    f = sp.sin(x)
    context = coverage_context(f, x, sp.Interval(-1, 1))
    state = fp.CoverageState(
        context,
        pending=(
            fp.CoverageTask(sp.Interval.Ropen(-1, 0), sp.Interval(-1, 1), 1),
            fp.CoverageTask(sp.Interval(0, 1), sp.Interval(-1, 1), 1),
        ),
    )
    original = engine._proposal

    def interior_only(context, region, policy):
        if region.start == 0 or region.end == 0:
            return None
        return original(context, region, policy)

    monkeypatch.setattr(engine, "_proposal", interior_only)
    result = fp.resume_root_coverage(state, policy=POLICY)
    assert result.complete and result.root_count == 1 and result.verify()
    assert any(
        a.root_count == 1 and a.region.start < 0 < a.region.end
        for a in result.proof.leaves
    )


def test_resumption_and_frontier_mutations():
    small = replace(POLICY, max_cells=0)
    first = fp.adaptive_root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 1), policy=small)
    assert not first.complete and first.unresolved == sp.Interval(0, 1)
    assert first.verify() and first.state.exhaustion == "cell-budget"
    assert not replace(first.state, pending=()).verify()
    assert not replace(first.state, pending=first.state.pending * 2).verify()
    assert not replace(first.state, tested=True).verify()
    with pytest.raises(ValueError):
        fp.resume_root_coverage(replace(first.state, pending=()))
    resumed = fp.resume_root_coverage(first, policy=POLICY)
    assert resumed.complete and resumed.root_count == 1 and resumed.verify()


def test_checkpoint_is_a_replayable_partition():
    checkpoints = []

    def capture(state):
        checkpoints.append(state)
        if state.leaves:
            raise InterruptedError

    D = sp.Union(sp.Interval(-2, -1), sp.Interval(0, 1))
    with capture_checkpoints(capture), pytest.raises(InterruptedError):
        fp.adaptive_root_coverage(sp.exp(x) - 2, x, D, policy=POLICY)
    saved = checkpoints[-1]
    assert saved.leaves and saved.pending and saved.verify()
    result = fp.resume_root_coverage(saved, policy=POLICY)
    assert result.complete and result.root_count == 1 and result.verify()
    assert all(a in result.proof.leaves for a in saved.leaves)


def test_hard_wall_timeout_keeps_query_and_can_resume():
    result = fp.adaptive_root_coverage(
        sp.exp(x) - 2, x, sp.Interval(0, 1), policy=replace(POLICY, seconds=0.001)
    )
    assert not result.complete and result.state.exhaustion == "wall-budget"
    assert result.unresolved == sp.Interval(0, 1)
    assert result.expression == sp.exp(x) - 2
    assert fp.resume_root_coverage(result, policy=POLICY).root_count == 1


@pytest.mark.parametrize("f", [sp.gamma(x), sp.sin(x) ** 2 + sp.Rational(1, 10)])
def test_unresolved_is_not_completed_by_exhaustion(f):
    result = fp.adaptive_root_coverage(
        f, x, sp.Interval(1, 2), policy=replace(POLICY, max_cells=0)
    )
    assert not result.complete and result.root_count is None


def test_stage_caps_are_cofinal():
    a, b = (fp.coverage_policy_stage(k, base=POLICY) for k in (0, 3))
    for name in (
        "precision",
        "max_precision",
        "max_refinements",
        "max_depth",
        "max_cells",
        "max_taylor_order",
        "max_series_terms",
    ):
        assert getattr(b, name) > getattr(a, name)
    with pytest.raises(ValueError):
        fp.coverage_policy_stage(True)


def test_piecewise_corner_has_count_but_no_global_multiplicity():
    f = sp.Piecewise((-x, x < 0), (2 * x, True))
    for producer in (fp.prove_root_coverage, fp.adaptive_root_coverage):
        result = producer(f, x, sp.Interval(-1, 1), policy=POLICY)
        assert result.complete and result.root_count == 1
        assert result.multiplicity_count is None and result.verify()


def test_original_hole_is_not_reintroduced():
    f = sp.Mul(sp.exp(x) - 2, x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    result = fp.adaptive_root_coverage(f, x, sp.Interval(0, 1), policy=POLICY)
    assert result.complete and result.root_count == 1 and result.verify()
    assert result.proof.context.effective == sp.Interval.Lopen(0, 1)


def test_checker_replay_does_not_call_proposers(monkeypatch):
    result = fp.adaptive_root_coverage(
        sp.exp(x) - 2, x, sp.Interval(0, 1), policy=POLICY
    )

    def disabled(*args, **kwargs):
        raise AssertionError("search called during independent replay")

    monkeypatch.setattr(engine, "_proposal", disabled)
    monkeypatch.setattr("funcprops.coverage_search.propose_leaf", disabled)
    assert result.verify()
    leaf = next(a for a in result.proof.leaves if a.root_count)
    assert not replace(leaf, root_count=2).verify()
    assert not replace(
        leaf, witness=replace(leaf.witness, locator=sp.FiniteSet(0))
    ).verify()
