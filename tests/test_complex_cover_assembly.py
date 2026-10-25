"""Native contour assembly, adversarial replay and resumable fair search."""

import pickle
import subprocess
from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import analytic_contours as ac
from funcprops import complex_isolation as ci
from funcprops._checkpoints import capture_checkpoints
from funcprops.transcendental import complex_roots as cr

z = sp.Symbol("z")
RECT = (-4 - sp.I, 4 + sp.I)


@pytest.fixture(scope="module")
def sine():
    return fp.certify_complex_isolation(sp.sin(z), z, *RECT)


def test_three_simple_roots_and_separate_completion(sine):
    p = sine.proof
    assert sine.verify() and p.complete
    assert p.coverage_complete and p.isolation_complete and p.accuracy_complete
    assert p.multiplicity_count == p.distinct_root_count == 3
    assert p.individual_multiplicities == (1, 1, 1)
    assert len(p.root_regions) == 3 and not p.clusters and not p.unresolved
    assert p.outer.zero_count == 3 and sine.tested <= 1024
    # pi need not be represented exactly to certify its unique enclosing box.
    for root in (-sp.pi, sp.S.Zero, sp.pi):
        assert (
            sum(
                bool(a < sp.re(root) < c and b < 0 < d)
                for a, b, c, d in (q.rectangle.bounds() for q in p.root_regions)
            )
            == 1
        )


def test_nonreal_exponential_zeros():
    r = fp.complex_zeros(
        sp.exp(z) + 1, z, rectangle=(-1 - 4 * sp.I, 1 + 4 * sp.I), return_result=True
    )
    assert r.verify() and r.complete and r.root_count == r.multiplicity_count == 2
    assert r.algebraic_certificate is None and r.isolation_certificate is r.state.proof
    for q in r.rectangles:
        assert q.root_count == 1 and q.certificate.verify()
        assert q.rectangle.im_min >= 0 or q.rectangle.im_max <= 0


def test_clusters_retained_without_false_distinct_count():
    r = fp.certify_complex_isolation(
        sp.sin(z) ** 2,
        z,
        -1 - sp.I,
        1 + sp.I,
        policy=fp.EnclosurePolicy(max_depth=0),
        use_multiple=False,
    )
    assert r.verify() and r.coverage_complete and not r.complete
    assert r.multiplicity_count == 2 and r.root_count is None
    assert len(r.clusters) == 1 and r.exhaustion == "depth-budget"
    assert not r.isolation_complete and not r.accuracy_complete


def test_unresolved_and_boundary_zero_never_complete():
    seed = fp.certify_complex_isolation(
        sp.sin(z), z, *RECT, policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert seed.verify() and seed.unresolved == (seed.proof.rectangle,)
    assert seed.multiplicity_count is None and not seed.coverage_complete
    r = fp.certify_complex_isolation(
        sp.exp(z) - 1,
        z,
        -sp.I,
        1 + sp.I,
        policy=fp.EnclosurePolicy(max_cells=32, max_depth=1),
        max_boundary_depth=1,
    )
    assert r.verify() and not r.complete and r.multiplicity_count is None
    assert r.proof.outer is None and r.unresolved


def test_partial_cover_is_explicit_not_a_global_count(sine):
    p = sine.proof
    lost = p.root_regions[0]
    partial = ci._assembled(p, roots=p.root_regions[1:], unresolved=(lost.rectangle,))
    assert partial.verify() and not partial.coverage_complete
    assert partial.total_count is None and partial.distinct_root_count is None
    assert partial.unresolved == (lost.rectangle,)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: replace(p, root_regions=p.root_regions[1:]),
        lambda p: replace(p, root_regions=(*p.root_regions, p.root_regions[0])),
        lambda p: replace(p, clusters=(p.outer,)),
        lambda p: replace(
            p,
            root_regions=(
                replace(p.root_regions[0], zero_count=2),
                *p.root_regions[1:],
            ),
        ),
        lambda p: replace(
            p,
            root_regions=(
                replace(p.root_regions[0], rectangle=p.rectangle),
                *p.root_regions[1:],
            ),
        ),
        lambda p: replace(p, multiplicity_count=4),
        lambda p: replace(p, distinct_root_count=2),
        lambda p: replace(p, coverage_complete=False),
        lambda p: replace(p, accuracy_complete=False),
        lambda p: replace(p, source_syntax="altered"),
        lambda p: replace(p, expression=sp.cos(z)),
        lambda p: replace(p, variable=sp.Symbol("w")),
        lambda p: replace(p, outer=None),
        lambda p: replace(p, obligations=("invented",)),
        lambda p: replace(p, exhaustion="wall-budget"),
        lambda p: replace(p, unresolved=(p.root_regions[0].rectangle,)),
        lambda p: replace(p, multiplicity_count=True),
    ],
)
def test_assembly_rejects_omission_duplicate_overlap_and_tampering(sine, mutation):
    assert mutation(sine.proof).check().certified is False


@pytest.mark.parametrize("kind", ["omitted", "duplicated", "overlapping"])
def test_exact_partition_rejects_even_recomputed_summary_fields(sine, kind):
    p = sine.proof
    if kind == "omitted":
        bad = ci._assembled(p, roots=p.root_regions[1:])
    elif kind == "duplicated":
        bad = ci._assembled(p, roots=(*p.root_regions, p.root_regions[0]))
    else:
        bad = ci._assembled(p, clusters=(p.outer,))
    assert not bad.verify()


def test_close_algebraic_pair_is_a_cluster_not_a_guessed_double_root():
    q = fp.certify_complex_isolation(
        (z - sp.Rational(1, 100)) * (z + sp.Rational(1, 100)),
        z,
        -1 - sp.I,
        1 + sp.I,
        policy=fp.EnclosurePolicy(max_depth=0),
    )
    assert q.verify() and q.coverage_complete and not q.isolation_complete
    assert q.multiplicity_count == 2 and q.root_count is None and len(q.clusters) == 1


def test_altered_boundary_witness_rejected(sine):
    p = sine.proof
    c = p.root_regions[0]
    w = replace(c.images[0], bounds=(sp.S.One,) * 4)
    c = replace(c, images=(w, *c.images[1:]))
    assert not replace(p, root_regions=(c, *p.root_regions[1:])).verify()


def test_self_attesting_subclasses_rejected(sine):
    class ForgedContour(ac.AnalyticContourCertificate):
        def verify(self):
            return True

    class ForgedImage(ac.ComplexBoxWitness):
        def verify(self):
            return True

    p = sine.proof
    c = p.root_regions[0]
    for bad in (
        ForgedContour(**c.__dict__),
        replace(c, images=(ForgedImage(**c.images[0].__dict__), *c.images[1:])),
    ):
        assert not replace(p, root_regions=(bad, *p.root_regions[1:])).verify()


def test_replay_with_all_proposing_functions_disabled(sine, monkeypatch):
    r = cr._native_result(sine)

    def disabled(*args, **kwargs):
        raise AssertionError("search invoked during replay")

    for module, names in [
        (
            ci,
            (
                "_run",
                "certify_complex_isolation",
                "resume_complex_isolation",
                "certify_analytic_contour",
            ),
        ),
        (ac, ("certify_analytic_contour", "analytic_complex_coverage")),
        (cr, ("isolate_complex_roots", "argument_principle_count", "_exact_roots")),
    ]:
        for name in names:
            monkeypatch.setattr(module, name, disabled)
    for record in (sine, sine.proof, r, pickle.loads(pickle.dumps(sine))):
        assert record.verify()
        status = fp.replay_status(record, expr=sp.sin(z), var=z)
        assert (
            status.supported
            and status.certified
            and status.complete
            and not status.factory_replay
        )
        assert fp.verify_certificate(record, expr=sp.sin(z), var=z)
        assert fp.replay_status(record, expr=sp.cos(z), var=z).certified is False


def test_public_wrapper_rejects_changed_fields(sine):
    r = cr._native_result(sine)
    for bad in (
        replace(r, total_count=4),
        replace(r, rectangles=r.rectangles[:-1]),
        replace(r, certificates=()),
        replace(r, isolation_complete=False),
        replace(r, roots=(0,)),
        replace(r, method="exact_complex_roots"),
        replace(r, algebraic_certificate=object()),
    ):
        assert not bad.verify()


def test_accuracy_is_independent_and_resume_refines():
    r = fp.certify_complex_isolation(
        sp.exp(z) - 1,
        z,
        -1 - sp.I,
        1 + sp.I,
        max_box_width=sp.Rational(1, 2),
        policy=fp.EnclosurePolicy(max_depth=0),
    )
    assert r.verify() and r.coverage_complete and r.isolation_complete
    assert not r.accuracy_complete and not r.complete and r.root_count == 1
    q = fp.resume_complex_isolation(
        r, policy=fp.EnclosurePolicy(max_depth=8, max_cells=2048)
    )
    assert q.verify() and q.complete and q.accuracy_complete
    assert all(ci._width(box) <= sp.Rational(1, 2) for box in q.isolating_boxes)
    assert q.tested > r.tested and q.generation > r.generation


def test_split_line_zero_does_not_lose_parent_or_roots(sine):
    # The first vertical bisector passes through sin(0)=0.
    r = fp.certify_complex_isolation(
        sp.sin(z), z, *RECT, policy=fp.EnclosurePolicy(max_depth=0)
    )
    assert r.coverage_complete and not r.complete and r.multiplicity_count == 3
    q = fp.resume_complex_isolation(r)
    assert q.verify() and q.complete and q.multiplicity_count == sine.multiplicity_count
    assert any(
        step[1] != sp.Rational(1, 2)
        for task in _captured_tasks(r)
        for step in task.path
    )


def _captured_tasks(state):
    seen = []
    with capture_checkpoints(lambda q: seen.extend(q.pending)):
        fp.resume_complex_isolation(state)
    return seen


def test_fair_queue_rotates_failed_splits(monkeypatch):
    r = fp.certify_complex_isolation(
        sp.sin(z),
        z,
        *RECT,
        max_box_width=sp.Rational(1, 4),
        policy=fp.EnclosurePolicy(max_depth=1),
    )
    assert len(r.pending) == 2 and r.verify()
    calls = []

    def fail(f, x, lo, hi, **kwargs):
        calls.append((lo, hi))
        return replace(ac._seed(f, x, lo, hi, "cell-budget"), tested=1)

    monkeypatch.setattr(ci, "certify_analytic_contour", fail)
    q = fp.resume_complex_isolation(
        r, policy=fp.EnclosurePolicy(max_cells=8, max_depth=3)
    )
    assert q.verify() and q.tested - r.tested == 8
    assert all(task.attempt > 0 for task in q.pending)
    assert len(set(calls)) > 1 and q.proof.regions == r.proof.regions


def test_checkpoint_transactions_and_resume(sine):
    checkpoints = []
    with capture_checkpoints(checkpoints.append):
        r = fp.certify_complex_isolation(sp.sin(z), z, *RECT)
    assert r.complete and len(checkpoints) > 3
    assert all(q.verify() for q in checkpoints)
    middle = next(q for q in checkpoints if q.clusters and q.pending[0].attempt > 0)
    resumed = fp.resume_complex_isolation(pickle.loads(pickle.dumps(middle)))
    assert (
        resumed.verify()
        and resumed.complete
        and resumed.total_count == sine.total_count
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda q: replace(q, pending=()),
        lambda q: replace(q, pending=(*q.pending, q.pending[0])),
        lambda q: replace(
            q, pending=(replace(q.pending[0], path=((0, sp.Rational(1, 2), 0),)),)
        ),
        lambda q: replace(q, pending=(replace(q.pending[0], attempt=-1),)),
        lambda q: replace(q, tested=-1),
        lambda q: replace(q, generation=True),
    ],
)
def test_invalid_checkpoints_are_rejected(mutation):
    q = fp.certify_complex_isolation(
        sp.sin(z), z, *RECT, policy=fp.EnclosurePolicy(max_cells=0)
    )
    q = mutation(q)
    assert not q.verify()
    with pytest.raises(ValueError, match="checkpoint"):
        fp.resume_complex_isolation(q)


@pytest.mark.parametrize("public", [False, True])
def test_tiny_wall_budget_returns_resumable_unknown(public):
    policy = fp.EnclosurePolicy(seconds=0.001)
    r = (
        fp.isolate_complex_roots(sp.sin(z), z, RECT, policy=policy)
        if public
        else fp.certify_complex_isolation(sp.sin(z), z, *RECT, policy=policy)
    )
    assert r.verify() and not r.complete and r.state.exhaustion == "wall-budget"
    assert not r.coverage_complete and r.multiplicity_count is None
    q = fp.resume_complex_isolation(r, policy=fp.EnclosurePolicy(max_cells=256))
    assert q.verify() and q.complete and q.root_count == 3


def test_tiny_resume_wall_preserves_accepted_counts():
    r = fp.certify_complex_isolation(
        sp.sin(z), z, *RECT, policy=fp.EnclosurePolicy(max_depth=0)
    )
    q = fp.resume_complex_isolation(r, policy=fp.EnclosurePolicy(seconds=0.001))
    assert q.verify() and q.proof.regions == r.proof.regions
    assert q.coverage_complete and q.multiplicity_count == 3 and not q.complete
    assert q.exhaustion == "wall-budget"


def test_algebraic_route_retained_and_wall_limited():
    r = fp.isolate_complex_roots(z**2 + 1, z, (-2 - 2 * sp.I, 2 + 2 * sp.I))
    assert r.complete and r.verify() and r.algebraic_certificate and r.state is None
    q = fp.isolate_complex_roots(
        z**2 + 1,
        z,
        (-2 - 2 * sp.I, 2 + 2 * sp.I),
        policy=fp.EnclosurePolicy(seconds=0.001),
    )
    assert not q.complete and q.total_count is None


@pytest.mark.parametrize(
    "f",
    [
        sp.log(z),
        sp.exp(sp.Symbol("a") * z),
    ],
)
def test_unsupported_sources_never_claim_native_completeness(f):
    q = fp.certify_complex_isolation(f, z, *RECT)
    assert not q.complete and not q.verify() and q.multiplicity_count is None


def test_held_quotient_uses_source_preserving_extension():
    f = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    q = fp.certify_complex_isolation(f, z, *RECT)
    assert type(q) is fp.QuotientIsolationState
    assert q.verify() and q.complete and q.multiplicity_count == 0
    assert q.proof.source.guards == (z,)


@pytest.mark.parametrize("width", [0, -1, 0.1, sp.sqrt(2), True])
def test_requested_accuracy_requires_positive_exact_rational(width):
    with pytest.raises(ValueError, match="exact rational"):
        fp.certify_complex_isolation(sp.sin(z), z, *RECT, max_box_width=width)


def test_native_manifest_entries():
    names = {q["type"]: q for q in fp.proof_api_manifest()["records"]}
    for name in ("ComplexIsolationProof", "ComplexIsolationState"):
        q = next(value for key, value in names.items() if key.endswith("." + name))
        assert q["replay_supported"] and q["contract"] == "witness-kernel"


def test_reordered_pending_queue_preserves_the_proof():
    r = fp.certify_complex_isolation(
        sp.sin(z),
        z,
        *RECT,
        max_box_width=sp.Rational(1, 2),
        policy=fp.EnclosurePolicy(max_depth=1),
    )
    reversed_state = replace(r, pending=tuple(reversed(r.pending)))
    assert reversed_state.verify()
    p = fp.resume_complex_isolation(
        reversed_state, policy=fp.EnclosurePolicy(max_depth=16, max_cells=4096)
    )
    assert p.complete and p.verify() and p.root_count == p.total_count == 3


def test_series_precision_exhaustion_keeps_unknown_regions():
    r = fp.certify_complex_isolation(
        sp.exp(100 * z) + 1,
        z,
        *RECT,
        policy=fp.EnclosurePolicy(
            precision=2,
            max_precision=2,
            max_refinements=0,
            max_series_terms=1,
            max_cells=9,
        ),
        max_boundary_depth=0,
    )
    assert r.verify() and not r.complete and r.tested <= 9
    assert r.unresolved and r.total_count is None


def test_worker_recovers_last_complete_checkpoint_frame(monkeypatch):
    from funcprops import work_budget as wb

    state = fp.certify_complex_isolation(
        sp.sin(z), z, *RECT, policy=fp.EnclosurePolicy(max_depth=0)
    )
    output = (
        pickle.dumps(("checkpoint", state)) + pickle.dumps(("checkpoint", state))[:15]
    )

    class InterruptedWorker:
        pid = 123456789

        def communicate(self, *args, **kwargs):
            if kwargs.get("timeout") is not None:
                raise subprocess.TimeoutExpired("test worker", kwargs["timeout"])
            return output, b""

    monkeypatch.setattr(wb.subprocess, "Popen", lambda *a, **k: InterruptedWorker())
    monkeypatch.setattr(wb.os, "killpg", lambda *args: None)
    r = wb.bounded_query("certify_complex_isolation", sp.sin(z), (z, *RECT), {}, 0.001)
    assert r.verify() and r.proof.regions == state.proof.regions
    assert r.coverage_complete and not r.complete and r.total_count == 3
    assert r.exhaustion == "wall-budget"


def test_native_record_subclasses_cannot_self_attest(sine):
    class ForgedState(fp.ComplexIsolationState):
        def verify(self):
            return True

        def check(self):
            return sine.check()

    fake = ForgedState(sine.proof)
    assert fp.verify_certificate(fake) is False
    assert fp.replay_status(fake).certified is False
    assert not replace(cr._native_result(sine), isolation_state=fake).verify()


def test_malformed_nested_public_state_is_rejected(sine):
    bad = replace(sine, proof=object())
    assert not replace(cr._native_result(sine), isolation_state=bad).verify()
