"""Mathematical quotient/pole cases and adversarial, search-free replay."""

import pickle
from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops import analytic_contours as ac
from funcprops import quotient_isolation as qi
from funcprops._checkpoints import capture_checkpoints
from funcprops.complex_isolation import ComplexIsolationTask
from funcprops.transcendental import complex_roots as cr

z = s.Symbol("z")
RECT = (-1 - s.I, 1 + s.I)
P = fp.EnclosurePolicy(max_depth=16, max_cells=8192, max_taylor_order=5)


def solve(f, **kwargs):
    return fp.certify_quotient_isolation(f, z, *RECT, policy=P, **kwargs)


@pytest.fixture(scope="module")
def holomorphic():
    return solve((s.exp(z) - 2) / (z + 2))


@pytest.fixture(scope="module")
def mixed():
    return solve((s.exp(z) - 2) / (s.exp(z) - 1))


@pytest.mark.parametrize(
    "f,n,p,w",
    [
        ((s.exp(z) - 2) / (z + 2), 1, 0, 1),
        (1 / (s.exp(z) - 2), 0, 1, -1),
        ((s.exp(z) - 2) / (s.exp(z) - 1), 1, 1, 0),
        (s.exp(z) * (s.exp(z) - 2) / (s.exp(z) - 1) ** 2, 1, 2, -1),
        (s.sin(z) / (s.exp(z) - 1), 0, 0, 0),
        (s.sin(z) / (s.exp(z) - 1) ** 3, 0, 2, -2),
        ((s.exp(z) - 1) / s.sin(z) ** 2, 0, 1, -1),
        (s.sin(z) ** 3 / (s.exp(z) - 1), 0, 0, 2),
        ((s.exp(z) - 2) ** 2 / (z + 2), 2, 0, 2),
        (1 / (s.exp(z) - 2) ** 3, 0, 3, -3),
        ((s.exp(z) + 3) / (z + 2), 0, 0, 0),
    ],
)
def test_exact_zero_and_pole_multiplicities(f, n, p, w):
    q = solve(f)
    assert q.verify() and q.complete
    assert q.total_count == n and q.pole_multiplicity_count == p
    assert q.proof.winding_count == w
    assert q.proof.extension_zero_count - q.proof.pole_multiplicity_count == w
    assert (
        q.proof.extension_zero_count - q.total_count
        == q.proof.excluded_zero_multiplicity
    )


@pytest.mark.parametrize(
    "fun,n,p",
    [
        (s.tan, 1, 0),
        (s.cot, 0, 1),
        (s.sec, 0, 0),
        (s.csc, 0, 1),
        (s.tanh, 1, 0),
        (s.coth, 0, 1),
        (s.sech, 0, 0),
        (s.csch, 0, 1),
    ],
)
def test_explicit_meromorphic_primitive_rules(fun, n, p):
    q = solve(fun(z))
    assert q.complete and q.verify()
    assert q.root_count == n and q.distinct_pole_count == p
    assert q.proof.source.guards


def test_nonreal_poles_and_many_real_poles():
    for f, poles in ((s.tanh(2 * z), 2), (s.tan(2 * z), 2)):
        q = solve(f)
        assert q.complete and q.verify()
        assert q.root_count == 1 and q.distinct_pole_count == poles
        assert len(q.proof.pole_regions) == 2


def test_global_denominator_exclusion_is_replayable(holomorphic):
    p = holomorphic.proof
    assert p.holomorphic_on_rectangle
    assert p.source.guards == (z + 2,)
    w = p.root_regions[0].exclusions[0]
    assert type(w) is fp.DenominatorExclusionProof and w.verify()
    assert fp.verify_certificate(w, expr=z + 2, var=z)
    assert not fp.replay_status(w).factory_replay


def test_cancellation_keeps_original_source_holes():
    a = s.exp(z) - 1
    f = s.Mul(a, s.Pow(a, -1, evaluate=False), evaluate=False)
    q = solve(f)
    assert q.complete and q.verify() and q.root_count == q.total_count == 0
    assert q.proof.source.numerator == q.proof.source.denominator == 1
    assert q.proof.source.guards == (a,)
    assert not q.proof.holomorphic_on_rectangle
    assert q.pole_multiplicity_count == 0


def test_cancellation_does_not_restore_a_zero_at_a_hole():
    f = s.Mul(z, s.Pow(z, -1, evaluate=False), s.exp(z) - 1, evaluate=False)
    q = solve(f)
    assert q.verify() and q.complete and q.root_count == 0
    assert q.proof.extension_zero_count == q.proof.excluded_zero_multiplicity == 1
    assert q.proof.winding_count == 1
    assert q.proof.source.guards == (z,)


def test_nested_reciprocals_keep_inner_domain():
    f = s.Pow(s.Pow(s.sin(z), -1, evaluate=False), -1, evaluate=False)
    q = solve(f)
    assert q.complete and q.verify() and q.root_count == 0
    assert s.sin(z) in q.proof.source.guards


def test_addition_and_integer_powers_of_quotients():
    f = 1 / (s.exp(z) - 1) + 1 / (s.exp(z) + 1)
    q = solve(f)
    assert q.complete and q.verify()
    assert q.root_count == 0 and q.pole_multiplicity_count == 1
    assert len(q.proof.source.guards) == 2


def test_implicit_common_zero_order():
    f = s.sin(z - s.Rational(1, 3)) / (s.exp(z - s.Rational(1, 3)) - 1)
    q = fp.certify_quotient_isolation(f, z, *RECT, policy=replace(P, max_depth=0))
    assert q.verify() and q.complete and q.coverage_complete
    assert q.root_count == q.total_count == q.pole_multiplicity_count == 0
    c = q.proof.cells[0]
    assert type(c.denominator) is fp.SharedZeroOrderProof
    point = s.Rational(1, 3)
    nl = fp.ExactLocalZeroProof(c.numerator, point, (s.S.Zero,))
    dl = fp.ExactLocalZeroProof(c.denominator, point, (s.S.Zero,))
    assert nl.verify() and dl.verify()
    cell = replace(c, numerator_location=nl, denominator_location=dl)
    p = replace(q.proof, cells=(cell,), exhaustion=None)
    assert p.verify() and p.complete and p.root_count == p.pole_multiplicity_count == 0


@pytest.mark.parametrize(
    "epsilon", [s.Rational(1, 4), s.Rational(1, 1000), s.Rational(1, 10**12)]
)
def test_near_collision_is_never_exact_cancellation(epsilon):
    f = s.sin(z) / (s.exp(z) - 1 - epsilon)
    q = fp.certify_quotient_isolation(
        f, z, *RECT, policy=replace(P, max_cells=2048, max_depth=8)
    )
    assert q.verify()
    if q.complete:
        assert q.root_count == q.distinct_pole_count == 1
        assert q.total_count == q.pole_multiplicity_count == 1
    else:
        assert q.total_count is None or q.total_count == 1
        assert q.pole_multiplicity_count is None or q.pole_multiplicity_count == 1


@pytest.mark.parametrize(
    "f",
    [
        s.log(z),
        s.exp(1 / z),
        s.sqrt(z) / (z + 2),
        s.conjugate(z) / (z + 2),
        (s.exp(z) - 2) / (z + s.Symbol("a")),
        s.exp(z) / (z + s.Float(2)),
        s.Piecewise((1 / z, s.re(z) > 0), (z, True)),
    ],
)
def test_unsupported_grammar_does_not_acquire_certification(f):
    assert not qi.quotient_source_supported(f, z)
    with pytest.raises(ValueError, match="unsupported"):
        solve(f)


@pytest.mark.parametrize(
    "f",
    [
        1 / (s.exp(z) - 1),
        s.Mul(s.exp(z) - 1, s.Pow(s.exp(z) - 1, -1, evaluate=False), evaluate=False),
    ],
)
def test_outer_poles_and_source_holes_remain_unresolved(f):
    q = fp.certify_quotient_isolation(
        f, z, -s.I, 1 + s.I, policy=replace(P, max_cells=64)
    )
    assert q.verify() and not q.complete
    assert q.total_count is None and q.pole_multiplicity_count is None
    assert q.proof.unresolved == (q.proof.rectangle,)


def test_multiple_root_and_pole_clusters_have_separate_completion():
    q = fp.certify_quotient_isolation(
        1 / (s.exp(z) - 2) ** 2,
        z,
        *RECT,
        policy=replace(P, max_depth=0),
        use_multiple=False,
    )
    assert q.verify() and q.coverage_complete
    assert not q.isolation_complete and not q.accuracy_complete and not q.complete
    assert q.total_count == 0 and q.pole_multiplicity_count == 2
    assert q.root_count is None and q.distinct_pole_count is None
    assert len(q.clusters) == 1


@pytest.mark.parametrize(
    "name,value",
    [("max_box_width", s.Rational(1, 2)), ("max_box_diameter", s.Rational(1, 2))],
)
def test_requested_accuracy_for_zeros_and_poles(name, value):
    q = solve((s.exp(z) - 2) / (s.exp(z) - 1), **{name: value})
    assert q.verify() and q.complete
    for c in (*q.proof.root_regions, *q.proof.pole_regions):
        a, b, u, v = c.rectangle.bounds()
        assert max(u - a, v - b) <= value
        if name == "max_box_diameter":
            assert (u - a) ** 2 + (v - b) ** 2 <= value**2


def test_accuracy_is_not_implied_by_individual_isolation():
    q = fp.certify_quotient_isolation(
        1 / (s.exp(z) - 2),
        z,
        *RECT,
        max_box_diameter=s.Rational(1, 100),
        policy=replace(P, max_depth=0),
    )
    assert q.verify() and q.coverage_complete and q.isolation_complete
    assert not q.accuracy_complete and not q.complete


@pytest.mark.parametrize("budget", [0, 1, 5, 15, 64, 128])
def test_query_work_budget_and_resume(budget):
    f = (s.exp(z) - 2) / (s.exp(z) - 1)
    q = fp.certify_complex_isolation(f, z, *RECT, policy=replace(P, max_cells=budget))
    assert type(q) is fp.QuotientIsolationState and q.tested <= budget and q.verify()
    q = pickle.loads(pickle.dumps(q))
    r = fp.resume_complex_isolation(q, policy=P)
    assert r.verify() and r.complete and r.root_count == r.distinct_pole_count == 1
    assert r.tested - q.tested <= P.max_cells


def test_all_atomic_checkpoints_replay():
    saved = []
    with capture_checkpoints(saved.append):
        q = solve((s.exp(z) - 2) / (s.exp(z) - 1))
    assert q.complete and saved and all(t.verify() for t in saved)
    r = fp.resume_quotient_isolation(saved[len(saved) // 2], policy=P)
    assert r.verify() and r.complete and r.total_count == q.total_count


@pytest.mark.parametrize(
    "entry",
    [
        "certify_quotient_isolation",
        "certify_complex_isolation",
        "isolate_complex_roots",
    ],
)
def test_wall_timeout_returns_replayable_resumable_quotient_state(entry):
    f = (s.exp(z) - 2) / (z + 2)
    policy = replace(P, seconds=0.001)
    if entry == "isolate_complex_roots":
        q = getattr(fp, entry)(f, z, RECT, policy=policy)
    else:
        q = getattr(fp, entry)(f, z, *RECT, policy=policy)
    assert q.verify() and not q.complete
    state = q.state
    assert (
        type(state) is fp.QuotientIsolationState and state.exhaustion == "wall-budget"
    )
    r = fp.resume_complex_isolation(state, policy=P)
    assert r.verify() and r.complete and r.root_count == 1


def test_public_route_and_consistent_status(mixed):
    f = mixed.proof.expression
    assert fp.check_complex_isolation(mixed.proof).certified is True
    result = fp.complex_zeros(f, z, rectangle=RECT, return_result=True, policy=P)
    assert result.method == "native_quotient_complex_isolation"
    assert result.verify() and result.complete and result.root_count == 1
    assert result.pole_multiplicity_count == result.distinct_pole_count == 1
    assert result.isolation_certificate is result.state.proof
    assert len(result.rectangles) == len(result.pole_regions) == 1
    assert result.rectangles[0].certificate.verify()
    for record in (result, result.state, result.proof):
        st = fp.replay_status(record, expr=f, var=z)
        assert st.certified and st.complete and not st.factory_replay
        assert st.outcome == "complete-coverage"
        assert fp.replay_status(record, expr=s.sin(z), var=z).certified is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: replace(p, cells=p.cells[:-1]),
        lambda p: replace(p, cells=(*p.cells, p.cells[0])),
        lambda p: replace(p, expression=1 / p.expression),
        lambda p: replace(p, source_syntax="changed"),
        lambda p: replace(p, coordinate_assumptions=()),
        lambda p: replace(p, rectangle=fp.CoverageRectangle(-2 - s.I, 2 + s.I)),
        lambda p: replace(p, source=replace(p.source, guards=())),
        lambda p: replace(p, source=replace(p.source, common=s.Integer(2))),
        lambda p: replace(
            p, source=replace(p.source, numerator=p.source.numerator + 1)
        ),
        lambda p: replace(p, outer=p.outer[:-1]),
        lambda p: replace(
            p, outer=(*p.outer[:1], replace(p.outer[1], zero_count=0), *p.outer[2:])
        ),
        lambda p: replace(p, unresolved=(p.rectangle,)),
        lambda p: replace(p, max_box_width=s.Float(1)),
        lambda p: replace(p, schema_version=True),
        lambda p: replace(p, exhaustion="wall-budget"),
    ],
)
def test_assembly_rejects_tampering(mixed, mutation):
    assert not mutation(mixed.proof).verify()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda w: replace(w, expression=w.expression + 1),
        lambda w: replace(w, rectangle=fp.CoverageRectangle(-3 - s.I, 3 + s.I)),
        lambda w: replace(w, contour=replace(w.contour, zero_count=1)),
        lambda w: replace(w, contour=replace(w.contour, zero_count=False)),
        lambda w: replace(w, schema_version=True),
    ],
)
def test_denominator_exclusion_rejects_tampering(holomorphic, mutation):
    cell = holomorphic.proof.cells[0]
    w = mutation(cell.exclusions[0])
    assert not w.verify()
    p = replace(holomorphic.proof, cells=(replace(cell, exclusions=(w,)),))
    assert not p.verify()


def test_approximate_common_zero_and_altered_jets_are_rejected():
    p = solve(s.sin(z) / (s.exp(z) - 1)).proof
    c = p.cells[0]
    for loc in (
        replace(c.numerator_location, center=s.Float(0)),
        replace(c.numerator_location, center=s.Rational(1, 10**30)),
        replace(c.numerator_location, jets=(s.Integer(1),)),
        replace(c.numerator_location, schema_version=True),
    ):
        assert not loc.verify()
        assert not replace(p, cells=(replace(c, numerator_location=loc),)).verify()


def test_bad_checkpoint_paths_and_duplicate_tasks_are_rejected():
    q = fp.certify_quotient_isolation(
        1 / (s.exp(z) - 2), z, *RECT, policy=replace(P, max_cells=0)
    )
    t = q.pending[0]
    for bad in (
        replace(q, pending=()),
        replace(q, pending=(t, t)),
        replace(q, pending=(replace(t, attempt=True),)),
        replace(q, pending=(replace(t, path=((0, s.Rational(1, 2), 1),)),)),
        replace(q, tested=True),
        replace(q, generation=-1),
    ):
        assert not bad.verify()
        with pytest.raises(ValueError):
            fp.resume_quotient_isolation(bad)


def test_local_records_and_result_replay_with_all_search_disabled(
    monkeypatch, holomorphic, mixed
):
    coincidence = solve(s.sin(z) / (s.exp(z) - 1))
    result = cr._quotient_result(mixed)
    source = holomorphic.proof.source
    exclusion = holomorphic.proof.cells[0].exclusions[0]
    local = coincidence.proof.cells[0].numerator_location

    def forbidden(*args, **kwargs):
        raise AssertionError("replay called the proposing algorithm")

    for module, name in (
        (qi, "_run"),
        (qi, "_source"),
        (qi, "certify_quotient_isolation"),
        (qi, "certify_analytic_contour"),
        (ac, "certify_analytic_contour"),
        (qi, "_propose_multiple"),
        (s, "cancel"),
        (s, "factor"),
        (s, "solveset"),
    ):
        monkeypatch.setattr(module, name, forbidden)
    for record in (
        holomorphic,
        mixed,
        coincidence,
        result,
        source,
        exclusion,
        local,
        result.rectangles[0].certificate,
    ):
        assert record.verify()
        assert fp.verify_certificate(record)
        assert fp.replay_status(record).certified is True


def test_self_attesting_subclasses_cannot_enter_unified_replay(holomorphic):
    for record in (
        holomorphic,
        holomorphic.proof,
        holomorphic.proof.source,
        holomorphic.proof.cells[0].exclusions[0],
    ):

        class Forged(type(record)):
            def verify(self):
                return True

        forged = Forged(**record.__dict__)
        assert not fp.verify_certificate(forged)
        assert fp.replay_status(forged).certified is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_box_width", 0),
        ("max_box_diameter", -1),
        ("max_box_width", s.Float(1)),
        ("use_multiple", 1),
        ("max_boundary_depth", True),
    ],
)
def test_invalid_controls_are_rejected(field, value):
    with pytest.raises(ValueError):
        solve(1 / (s.exp(z) - 2), **{field: value})


def test_standalone_pole_region_replay_and_kind_binding(mixed):
    record = mixed.proof.pole_regions[0]
    assert record.kind == "pole" and record.verify()
    assert record.multiplicity_count == record.distinct_pole_count == 1
    assert fp.verify_certificate(record) and not fp.replay_status(record).factory_replay
    assert not replace(record, kind="zero").verify()
    assert not replace(record, kind="unknown").verify()


def test_joint_count_checker_rejects_altered_component_box(mixed):
    c = mixed.proof.cells[0]
    n = c.numerator
    bad = replace(n, rectangle=fp.CoverageRectangle(-1 - s.I, 1 + s.I))
    # The local contour belongs to its original cell, not the enlarged box.
    p = replace(mixed.proof, cells=(replace(c, numerator=bad), *mixed.proof.cells[1:]))
    assert not p.verify()


@pytest.mark.parametrize(
    "f,zeros,poles,winding,source_zeros",
    [
        ((s.exp(z) - 2) / (s.exp(z) - 1), 1, 1, 0, 1),
        (s.sin(z) / (s.exp(z) - 1), 0, 0, 0, 0),
        (s.sin(z) ** 3 / (s.exp(z) - 1), 2, 0, 2, 0),
        (s.sin(z) / (s.exp(z) - 1) ** 3, 0, 2, -2, 0),
        (1 / (s.exp(z) - 2) ** 2, 0, 2, -2, 0),
    ],
)
def test_public_meromorphic_counter_has_explicit_extension_counts(
    f, zeros, poles, winding, source_zeros
):
    c = fp.meromorphic_rectangle_count(f, z, *RECT, policy=P)
    assert type(c) is fp.QuotientContourCertificate and c.verify()
    assert (c.zeros, c.poles, c.winding, c.source_zero_count) == (
        zeros,
        poles,
        winding,
        source_zeros,
    )
    assert fp.verify_certificate(c)
    status = fp.replay_status(c, expr=f, var=z)
    assert status.certified and status.complete and not status.factory_replay
    assert not replace(c, schema_version=True).verify()


def test_meromorphic_count_does_not_require_individual_pole_isolation():
    c = fp.meromorphic_rectangle_count(
        1 / (s.exp(z) - 2) ** 2,
        z,
        *RECT,
        policy=replace(P, max_depth=0, max_taylor_order=0),
    )
    assert c.verify() and c.complete
    assert c.poles == 2


def test_unseparated_quotient_divisors():
    f = s.sin(z - s.Rational(1, 3)) / (
        s.exp(z - s.Rational(1, 3)) - 1 - s.Rational(1, 10**12)
    )
    assert (
        fp.meromorphic_rectangle_count(f, z, *RECT, policy=replace(P, max_depth=0))
        is None
    )


def test_meromorphic_certificate_replay_does_not_call_search(monkeypatch, mixed):
    c = fp.QuotientContourCertificate(mixed.proof)

    def forbidden(*args, **kwargs):
        raise AssertionError("divisor replay called search")

    monkeypatch.setattr(qi, "certify_quotient_isolation", forbidden)
    monkeypatch.setattr(qi, "_run", forbidden)
    monkeypatch.setattr(qi, "_source", forbidden)
    assert c.verify() and fp.verify_certificate(c)
    assert fp.replay_status(c).certified


def test_counted_outer_checkpoint_resume(mixed):
    p = replace(
        mixed.proof,
        cells=(),
        unresolved=(mixed.proof.rectangle,),
        exhaustion="cell-budget",
    )
    state = fp.QuotientIsolationState(p, (ComplexIsolationTask(p.rectangle),))
    assert state.verify()
    q = fp.resume_quotient_isolation(state, policy=P)
    assert q.complete and q.verify() and q.root_count == q.distinct_pole_count == 1


def test_unsupported_source_is_rejected_before_wall_worker():
    with pytest.raises(ValueError, match="unsupported"):
        fp.certify_quotient_isolation(
            s.log(z), z, *RECT, policy=replace(P, seconds=0.001)
        )


@pytest.mark.parametrize(
    "entry", [fp.certify_complex_isolation, fp.resume_complex_isolation]
)
def test_generic_dispatch_does_not_ignore_invalid_newton_mode(entry, mixed):
    with pytest.raises(ValueError, match="use_newton"):
        if entry is fp.certify_complex_isolation:
            entry(mixed.proof.expression, z, *RECT, use_newton=1)
        else:
            entry(mixed, use_newton=1)


def test_resumed_exact_locations():
    q = fp.certify_quotient_isolation(
        1 / (s.cosh(z) - 1),
        z,
        *RECT,
        max_box_width=s.Rational(1, 2),
        policy=replace(P, max_depth=0),
        use_multiple=False,
    )
    c = q.proof.cells[0]
    loc = fp.ExactLocalZeroProof(c.denominator, s.S.Zero, (s.S.Zero, s.S.Zero))
    assert loc.verify()
    proof = replace(q.proof, cells=(replace(c, denominator_location=loc),))
    seed = replace(q, proof=proof)
    assert seed.verify()
    r = fp.resume_quotient_isolation(seed, policy=replace(P, max_depth=0))
    assert r.verify() and r.proof.pole_multiplicity_count == 2
    c = r.proof.cells[0]
    assert c.denominator_location.region == c.denominator
