"""Implicit shared orders, cofinal scheduling and joint Newton replay."""

import pickle
from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops import analytic_contours as ac
from funcprops import quotient_cofinal as qc
from funcprops import quotient_isolation as qi
from funcprops import quotient_refinement as qr
from funcprops import shared_zeros as sz
from funcprops._checkpoints import capture_checkpoints

z = s.Symbol("z")
g = s.exp(z) - 2
RECT = (-1 - s.I, 1 + s.I)
SMALL = (s.Rational(1, 2) - s.I / 4, 1 + s.I / 4)
POLICY = fp.EnclosurePolicy(max_cells=8192, max_depth=24, max_taylor_order=5)


def solve(f, rect=RECT, **kwargs):
    return fp.certify_quotient_isolation(f, z, *rect, policy=POLICY, **kwargs)


@pytest.mark.parametrize("power", [1, 2, 3, 4])
@pytest.mark.parametrize("unit", [s.S.One, s.exp(z)])
def test_shared_factor_excludes_every_multiplicity_of_a_source_hole(power, unit):
    f = s.Mul(unit * g**power, g, s.Pow(g, -1, evaluate=False), evaluate=False)
    q = solve(f)
    assert q.verify() and q.complete
    assert q.root_count == q.total_count == q.pole_multiplicity_count == 0
    assert q.proof.extension_zero_count == q.proof.excluded_zero_multiplicity == power
    assert q.proof.source.guards == (g,)
    assert any(c.guard_zero.verify() for c in q.proof.cells if c.guard_zero)
    c = next(c for c in q.proof.cells if c.guard_zero is not None)
    assert c.guard_zero.verify() and fp.verify_certificate(c.guard_zero)
    assert s.log(2).is_Rational is False


@pytest.mark.parametrize("n,d", [(1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 2)])
def test_composition_orders_resolve_a_nonrational_common_root(n, d):
    q = solve(g**n / s.sin(g) ** d)
    assert q.verify() and q.complete and q.total_count == q.root_count == 0
    assert q.pole_multiplicity_count == max(d - n, 0)
    assert q.distinct_pole_count == int(d > n)
    assert q.proof.extension_zero_count == max(n - d, 0)
    assert q.proof.winding_count == n - d
    c = next(c for c in q.proof.cells if c.numerator.zero_count)
    assert type(c.denominator) is fp.SharedZeroOrderProof
    assert c.denominator.implication.method == "composition"
    for r in (c.numerator, c.denominator):
        assert r.verify() and fp.verify_certificate(r)
        assert r.base_region.expression == g


@pytest.fixture(scope="module")
def shared_pole():
    return solve(g / s.sin(g) ** 2)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda w: replace(w, minimum_order=0),
        lambda w: replace(w, minimum_order=True),
        lambda w: replace(w, minimum_order=w.minimum_order + 1),
        lambda w: replace(w, jets=(s.S.One,) * w.minimum_order),
        lambda w: replace(
            w, outer=s.sin(w.outer_variable + s.Rational(1, 10**20)) ** 2
        ),
        lambda w: replace(w, outer=s.sin(w.outer_variable) ** 2 + s.Float("1e-20")),
        lambda w: replace(w, outer_variable=z),
        lambda w: replace(w, outer_variable=s.Symbol("u", positive=True)),
        lambda w: replace(w, method="factor", cofactor=s.S.One),
        lambda w: replace(w, expression=w.expression + 1),
        lambda w: replace(w, schema_version=True),
    ],
)
def test_composition_zero_jets(shared_pole, mutate):
    c = shared_pole.proof.cells[0]
    r = c.denominator
    w = mutate(r.implication)
    assert not w.verify() and not fp.verify_certificate(w)
    bad = replace(r, implication=w)
    assert not bad.verify()
    assert not replace(shared_pole.proof, cells=(replace(c, denominator=bad),)).verify()


def test_factor_implication_and_source_guard_must_match():
    f = s.Mul(g**2, g, s.Pow(g, -1, evaluate=False), evaluate=False)
    q = solve(f)
    c = q.proof.cells[0]
    assert not replace(c.guard_zero, cofactor=s.Integer(2)).verify()
    assert not replace(
        q.proof, cells=(replace(c, guard_zero=replace(c.guard_zero, expression=g**2)),)
    ).verify()
    wrong = fp.certify_analytic_contour(s.exp(z) - 1, z, *RECT)
    assert wrong.verify() and wrong.zero_count == 1
    assert not replace(c.guard_zero, base_region=wrong).verify()


def test_component_count_must_exclude_additional_outer_function_zeros():
    base = fp.certify_analytic_contour(4 * z, z, *RECT)
    parent = fp.certify_analytic_contour(s.sin(4 * z), z, *RECT)
    assert base.zero_count == 1 and parent.zero_count == 3
    u = s.Symbol("u")
    w = fp.SharedZeroImplication(
        s.sin(4 * z),
        z,
        base,
        1,
        "composition",
        outer_variable=u,
        outer=s.sin(u),
        jets=(s.S.Zero,),
    )
    assert w.verify()
    assert not fp.SharedZeroOrderProof(parent, w).verify()
    q = solve(4 * z / s.sin(4 * z))
    assert q.complete and q.verify() and q.total_count == 0
    assert q.pole_multiplicity_count == q.distinct_pole_count == 2


@pytest.mark.parametrize(
    "epsilon", [s.Rational(1, 100), s.Rational(1, 10**12), -s.Rational(1, 10**12)]
)
def test_nearby_roots_do_not_become_an_exact_shared_zero(epsilon):
    q = fp.certify_quotient_isolation(
        g / s.sin(g + epsilon), z, *RECT, policy=replace(POLICY, max_depth=0)
    )
    assert q.verify() and not q.coverage_complete and not q.complete
    assert q.total_count is None and q.pole_multiplicity_count is None
    c = q.proof.cells[0]
    assert sz._propose_implication(c.denominator.expression, c.numerator, 1) is None


@pytest.fixture(scope="module")
def refinement():
    p = solve(g / s.sin(g) ** 2, SMALL)
    r = fp.certify_quotient_refinement(p)
    assert r.verify() and fp.verify_certificate(r)
    return r


def test_joint_newton_keeps_both_divisor_totals_and_complement_strips(refinement):
    r = refinement
    assert len(r.cells) == 5
    assert (
        sum(c.numerator.zero_count for c in r.cells)
        == r.parent.numerator.zero_count
        == 1
    )
    assert (
        sum(c.denominator.zero_count for c in r.cells)
        == r.parent.denominator.zero_count
        == 2
    )
    assert all(
        c.numerator.zero_count == c.denominator.zero_count == 0 for c in r.cells[1:]
    )
    assert r.cells[0].denominator.zero_count == 2
    assert all(c.denominator.verify() for c in r.cells)
    assert qi._cell_data(r.source, r.cells[0]) == (0, 1, 0, 0, 1)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: replace(r, cells=r.cells[:-1]),
        lambda r: replace(r, cells=(r.cells[0],) * 5),
        lambda r: replace(r, cells=tuple(reversed(r.cells))),
        lambda r: replace(r, guard_contours=()),
        lambda r: replace(
            r, guard_contours=(replace(r.guard_contours[0], zero_count=None),)
        ),
        lambda r: replace(r, source=replace(r.source, guards=())),
        lambda r: replace(r, refinement=replace(r.refinement, inverse=s.S.Zero)),
        lambda r: replace(r, refinement=replace(r.refinement, contraction=s.S.Zero)),
        lambda r: replace(
            r,
            refinement=replace(
                r.refinement, child_rectangle=fp.CoverageRectangle(*SMALL)
            ),
        ),
        lambda r: replace(r, tested=True),
        lambda r: replace(r, schema_version=True),
    ],
)
def test_joint_refinement_rejects_missing_or_altered_evidence(refinement, mutate):
    bad = mutate(refinement)
    assert not bad.verify() and not fp.verify_certificate(bad)


def test_shared_order_parent_binding(
    refinement,
):
    r = refinement
    positive = r.cells[0].denominator
    assert type(positive) is fp.SharedZeroRegion
    assert not replace(
        positive,
        base_region=refinement.cells[1].denominator.base_region,
        order_proof=replace(
            positive.order_proof,
            implication=replace(positive.order_proof.implication, minimum_order=1),
        ),
    ).verify()
    empty = fp.certify_analytic_contour(s.exp(z), z, *RECT)
    outside = fp.CoverageRectangle(2 - s.I, 3 + s.I)
    assert not fp.ComplexZeroSubsetProof(empty, outside).verify()
    assert not fp.ComplexZeroSubsetProof(
        refinement.parent.numerator, refinement.child_rectangle
    ).verify()
    assert fp.ComplexZeroSubsetProof(empty, fp.CoverageRectangle(*SMALL)).verify()


def test_refined_extension_source_hole():
    f = s.Mul(g**2, g, s.Pow(g, -1, evaluate=False), evaluate=False)
    q = solve(f, SMALL)
    r = fp.certify_quotient_refinement(q)
    assert r.verify()
    data = [qi._cell_data(r.source, c) for c in r.cells]
    assert sum(c[0] for c in data) == sum(c[1] for c in data) == 0
    assert sum(c[2] for c in data) == 2
    assert r.cells[0].guard_zero.verify()
    assert r.cells[0].guard_zero.expression == g
    missing = replace(r, cells=(replace(r.cells[0], guard_zero=None), *r.cells[1:]))
    assert not missing.verify() and not fp.verify_certificate(missing)


@pytest.mark.parametrize("f", [1 / g, 1 / g**3, g / s.sin(g) ** 2, g / (s.exp(z) - 1)])
def test_refinement_divisor_counts(f):
    records = []
    for mode in (True, False):
        q = solve(f, max_box_width=s.Rational(1, 100), use_newton=mode)
        assert q.verify() and q.complete
        records.append(q)
    a, b = records
    assert (
        a.root_count,
        a.total_count,
        a.pole_multiplicity_count,
        a.distinct_pole_count,
    ) == (b.root_count, b.total_count, b.pole_multiplicity_count, b.distinct_pole_count)
    assert a.refinements and not b.refinements
    assert all(r.verify() for r in a.refinements)
    for c in (*a.proof.root_regions, *a.proof.pole_regions):
        assert qi._accurate(c, s.Rational(1, 100))


def test_resumed_cofinal_completion():
    f = g / (s.exp(z) - 1)
    policy = replace(POLICY, max_cells=128, max_depth=0, max_refinements=0)
    run = fp.adaptive_complex_isolation(
        f, z, *RECT, stages=0, policy=policy, use_newton=False
    )
    assert type(run) is fp.QuotientIsolationRun and run.verify() and not run.complete
    contract = run.termination_contract
    assert contract.verify() and contract.conditional and not contract.complete
    assert contract.applicable is None
    previous = run.tested
    for _ in range(8):
        if run.complete:
            break
        cap = fp.complex_isolation_policy_stage(run.next_stage, base=policy).max_cells
        run = fp.resume_adaptive_complex_isolation(
            pickle.loads(pickle.dumps(run)), stages=1
        )
        assert run.verify() and run.tested - previous <= cap
        previous = run.tested
    assert run.complete and run.root_count == run.distinct_pole_count == 1
    assert run.coverage_complete and run.isolation_complete and run.accuracy_complete
    assert run.termination_contract.applicable is True
    assert run.termination_contract.unproved_hypotheses == (
        "unbounded-completed-cofinal-stages",
    )
    assert fp.verify_certificate(run) and fp.verify_certificate(
        run.termination_contract
    )


def test_split_precision_fairness(
    monkeypatch,
):
    original = qi.certify_analytic_contour
    calls = []
    outer = fp.CoverageRectangle(*RECT)

    def restricted(f, x, lo, hi, *, policy):
        r = fp.CoverageRectangle(lo, hi)
        if r != outer:
            allowed = policy.max_cells >= 256 and 40 in policy.precisions
            calls.append((r, policy.max_cells, policy.precisions, allowed))
            if not allowed:
                policy = replace(policy, max_cells=0)
        return original(f, x, lo, hi, policy=policy)

    monkeypatch.setattr(qi, "certify_analytic_contour", restricted)
    run = fp.adaptive_quotient_isolation(
        g / (s.exp(z) - 1),
        z,
        *RECT,
        stages=9,
        policy=fp.EnclosurePolicy(
            precision=10,
            max_precision=10,
            max_refinements=0,
            max_cells=128,
            max_depth=0,
        ),
        use_newton=False,
        use_multiple=False,
    )
    assert run.verify() and run.complete
    refused = {r for r, _, _, ok in calls if not ok}
    assert any(r in refused and ok for r, _, _, ok in calls)
    assert any(40 in p for _, _, p, ok in calls if ok)


@pytest.mark.parametrize(
    "f", [1 / (s.exp(z) - 1), s.Mul(z, s.Pow(z, -1, evaluate=False), evaluate=False)]
)
def test_cofinal_boundary_obstructions(f):
    run = fp.adaptive_quotient_isolation(
        f,
        z,
        -s.I,
        1 + s.I,
        stages=3,
        policy=replace(POLICY, max_cells=16, max_depth=0),
        max_boundary_depth=0,
    )
    assert run.verify() and not run.complete and run.total_count is None
    assert run.proof.unresolved == (run.proof.rectangle,)
    assert (
        run.termination_contract.verify()
        and run.termination_contract.applicable is None
    )


def test_cofinal_divisor_premises():
    for f in (1 / g**2, g / s.sin(g)):
        expected = f == g / s.sin(g)
        run = fp.adaptive_quotient_isolation(f, z, *RECT, stages=1, policy=POLICY)
        assert run.verify() and run.complete
        assert (
            run.termination_contract.verify()
            and run.termination_contract.applicable is expected
        )
        assert not run.termination_contract.complete


@pytest.mark.parametrize(
    "entry", ["adaptive_quotient_isolation", "adaptive_complex_isolation"]
)
def test_cofinal_wall_budget_returns_checked_resumable_state(entry):
    run = getattr(fp, entry)(
        1 / g, z, *RECT, stages=8, policy=replace(POLICY, seconds=0.001)
    )
    assert run.verify() and not run.complete and run.exhaustion == "wall-budget"
    run = fp.resume_adaptive_quotient_isolation(run, stages=2)
    assert run.verify() and run.complete and run.distinct_pole_count == 1


def test_atomic_cofinal_checkpoints_and_forged_run_fields():
    saved = []
    with capture_checkpoints(saved.append):
        run = fp.adaptive_quotient_isolation(
            1 / g, z, *SMALL, stages=2, max_box_width=s.Rational(1, 100), policy=POLICY
        )
    assert saved and run.complete and all(q.verify() for q in saved)
    for bad in (
        replace(run, next_stage=True),
        replace(run, protocol="depth-only"),
        replace(run, use_newton=1),
        replace(run, base_policy=replace(POLICY, seconds=1)),
        replace(run, state=replace(run.state, tested=True)),
    ):
        if bad == run:
            continue
        assert not bad.verify()
        with pytest.raises(ValueError):
            fp.resume_adaptive_quotient_isolation(bad)
    assert not replace(run.termination_contract, theorem="unconditional").verify()


def test_certificates_replay_with_all_proposing_code_disabled(
    monkeypatch, refinement, shared_pole
):
    run = fp.adaptive_quotient_isolation(1 / g, z, *SMALL, stages=1, policy=POLICY)
    c = shared_pole.proof.cells[0]

    def forbidden(*args, **kwargs):
        raise AssertionError("independent replay invoked a proposer")

    for module, name in (
        (qi, "_run"),
        (qi, "_source"),
        (qi, "certify_analytic_contour"),
        (qi, "_propose_implication"),
        (qi, "_propose_multiple"),
        (qr, "_propose_quotient_refinement"),
        (qr, "_propose_refinement"),
        (sz, "_propose_implication"),
        (qc, "_advance"),
        (ac, "certify_analytic_contour"),
        (s, "cancel"),
        (s, "factor"),
        (s, "solveset"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    for p in (
        shared_pole,
        c.denominator,
        c.denominator.implication,
        refinement,
        *[r.denominator for r in refinement.cells],
        run,
        run.termination_contract,
    ):
        assert p.verify() and fp.verify_certificate(p)


def test_joint_refinement_replay():
    q = fp.certify_complex_isolation(
        g / (s.exp(z) - 1),
        z,
        *RECT,
        max_box_width=s.Rational(1, 100),
        policy=POLICY,
        use_newton=True,
    )
    assert q.complete and q.verify() and q.refinements
    assert all(p.verify() for p in (*q.proof.root_regions, *q.proof.pole_regions))
    assert all(
        fp.replay_status(p).certified
        for p in (*q.proof.root_regions, *q.proof.pole_regions)
    )
    result = fp.isolate_complex_roots(
        1 / g, z, RECT, max_box_width=s.Rational(1, 100), policy=POLICY
    )
    assert result.complete and result.verify() and result.refinements


@pytest.mark.parametrize(
    "outer,order",
    [
        (s.sin, 1),
        (s.sinh, 1),
        (s.erf, 1),
        (lambda u: s.exp(u) - 1, 1),
        (lambda u: s.cosh(u) - 1, 2),
    ],
)
def test_supported_outer_orders_and_normalization_rewrites(outer, order):
    q = solve(g / outer(g), SMALL)
    assert q.complete and q.verify() and q.total_count == 0
    assert q.pole_multiplicity_count == order - 1


def test_nonreal_implicit_common_root_is_certified():
    base = s.exp(z) + 1
    q = solve(base / s.sin(base) ** 2, (-1 + 2 * s.I, 1 + 4 * s.I))
    assert q.complete and q.verify() and q.root_count == 0
    assert q.pole_multiplicity_count == q.distinct_pole_count == 1
    assert any(type(c.denominator) is fp.SharedZeroOrderProof for c in q.proof.cells)


def test_refinement_timeout_covers_parent_replay(monkeypatch, shared_pole):
    def forbidden(self):
        raise AssertionError("replay escaped the wall-budget worker")

    monkeypatch.setattr(fp.QuotientIsolationProof, "verify", forbidden)
    assert (
        fp.certify_quotient_refinement(
            shared_pole, policy=replace(POLICY, seconds=0.001)
        )
        is None
    )


@pytest.mark.parametrize("budget", [0, 1, 2, 4, 16])
def test_joint_refinement_work_budget_is_bounded(budget):
    q = solve(g / s.sin(g) ** 2, SMALL)
    r = fp.certify_quotient_refinement(q, policy=replace(POLICY, max_cells=budget))
    assert r is None or (r.verify() and r.tested <= budget)


def test_region_cache_binding():
    from funcprops.complex_newton import _valid_region

    p = fp.certify_analytic_contour(g, z, *SMALL)
    memo = {}
    assert _valid_region(p, g, z, memo)
    assert not _valid_region(p, g + 1, z, memo)
    assert not _valid_region(p, g, s.Symbol("w"), memo)
