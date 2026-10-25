"""Cofinal fairness, conditional guarantees and selected multiple-root replay."""

import pickle
from dataclasses import replace
from itertools import pairwise

import pytest
import sympy as sp

import funcprops as fp
from funcprops import complex_cofinal as cc
from funcprops import complex_isolation as ci
from funcprops import complex_multiplicity as cm
from funcprops._checkpoints import capture_checkpoints
from funcprops.complex_interval import complex_box_taylor

z = sp.Symbol("z")
RECT = (-1 - sp.I, 1 + sp.I)


@pytest.mark.parametrize(
    "expr",
    [
        sp.exp(z),
        sp.sin(z * z + z),
        sp.cosh(z),
        sp.erf(z),
        sp.erfc(sp.sin(z)),
        (z + sp.I) ** 4,
    ],
)
@pytest.mark.parametrize("order", [0, 1, 2, 3])
def test_complex_taylor_coefficients(expr, order):
    point = sp.Rational(1, 10) + sp.I / 20
    boxes = complex_box_taylor(
        expr, z, (sp.re(point), sp.im(point), sp.re(point), sp.im(point)), order
    )
    assert len(boxes) == order + 1
    for k, (a, b, c, d) in enumerate(boxes):
        real, imag = sp.N(
            sp.diff(expr, z, k).subs(z, point) / sp.factorial(k), 100
        ).as_real_imag()
        assert a <= real <= c and b <= imag <= d


def test_precision_portfolios_are_nested_and_all_caps_grow():
    base = fp.EnclosurePolicy(
        precision=2,
        max_precision=2,
        max_refinements=0,
        max_cells=0,
        max_depth=0,
        max_series_terms=0,
        max_taylor_order=0,
    )
    policies = [fp.complex_isolation_policy_stage(k, base=base) for k in range(8)]
    for a, b in pairwise(policies):
        assert set(a.precisions) <= set(b.precisions)
        assert b.precision == 2 and b.max_precision > a.max_precision
        assert all(
            getattr(b, k) > getattr(a, k)
            for k in (
                "max_refinements",
                "max_depth",
                "max_cells",
                "max_series_terms",
                "max_taylor_order",
            )
        )
    assert policies[-1].precisions == (2, 4, 8, 16, 32, 64, 128, 256)


def test_every_split_index_gets_unbounded_effort():
    pairs = [ci._dovetail(k) for k in range(1000)]
    for candidate in range(12):
        efforts = [j for i, j in pairs if i == candidate]
        assert efforts == list(range(len(efforts))) and len(efforts) > 25


def test_reserved_work_does_not_advance_an_unattempted_split():
    q = fp.certify_complex_isolation(
        sp.sin(z),
        z,
        -4 - sp.I,
        4 + sp.I,
        policy=fp.EnclosurePolicy(max_depth=0),
        use_multiple=False,
    )
    r = ci._run(
        q, fp.EnclosurePolicy(max_cells=256), 14, use_multiple=False, cofinal=True
    )
    assert r.verify() and r.pending == q.pending and r.tested == q.tested
    assert r.exhaustion == "cell-budget"


def test_source_bound_cofinal_resume_and_conditional_scope():
    q = fp.adaptive_complex_isolation(sp.sin(z), z, -4 - sp.I, 4 + sp.I, stages=0)
    assert q.verify() and not q.complete and q.next_stage == 0
    theorem = q.termination_contract
    assert theorem.verify() and theorem.conditional and not theorem.complete
    assert "zero-free-outer-boundary" in theorem.unproved_hypotheses
    assert "all-zeros-simple" in theorem.unproved_hypotheses
    q = fp.resume_adaptive_complex_isolation(pickle.loads(pickle.dumps(q)), stages=4)
    assert q.verify() and q.complete and q.root_count == q.total_count == 3
    theorem = q.termination_contract
    assert theorem.applicable is True and theorem.unproved_hypotheses == (
        "unbounded-completed-cofinal-stages",
    )
    status = fp.replay_status(theorem)
    assert status.certified and not status.complete and not status.factory_replay


@pytest.mark.parametrize(
    "expr,lo,hi,count",
    [
        (
            (sp.exp(z) - 1) * (sp.exp(z) - sp.Rational(1001, 1000)),
            -sp.Rational(1, 100) - sp.I / 100,
            sp.Rational(1, 100) + sp.I / 100,
            2,
        ),
        (sp.sin(16 * z), -1 - sp.I / 5, 1 + sp.I / 5, 11),
        (sp.sin(10**100 + z), -(10**100) - 1 - sp.I / 5, -(10**100) + 1 + sp.I / 5, 1),
        (
            sp.exp(z) - 1 + sp.exp(-100),
            -sp.Rational(1, 10) - sp.I / 10,
            sp.Rational(1, 10) + sp.I / 10,
            1,
        ),
    ],
)
def test_adversarial_simple_entire_problems(expr, lo, hi, count):
    q = fp.adaptive_complex_isolation(
        expr,
        z,
        lo,
        hi,
        stages=7,
        policy=fp.EnclosurePolicy(max_depth=40, max_cells=512),
    )
    assert q.complete and q.verify() and q.root_count == q.total_count == count


def test_boundary_roots_and_quotient_holes():
    q = fp.adaptive_complex_isolation(
        sp.exp(z) - 1,
        z,
        -sp.I,
        1 + sp.I,
        stages=3,
        policy=fp.EnclosurePolicy(max_cells=64, max_depth=0),
        max_boundary_depth=0,
    )
    assert q.verify() and not q.complete and q.total_count is None
    assert "zero-free-outer-boundary" in q.termination_contract.unproved_hypotheses
    raw = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    r = fp.adaptive_complex_isolation(raw, z, *RECT)
    assert r.complete and r.verify() and r.termination_contract.verify()
    assert type(r) is fp.QuotientIsolationRun
    assert r.total_count == r.pole_multiplicity_count == 0
    assert r.proof.source.guards == (z,) and not r.proof.holomorphic_on_rectangle


@pytest.mark.parametrize(
    "mutation",
    [
        lambda q: replace(q, protocol="other"),
        lambda q: replace(q, next_stage=True),
        lambda q: replace(q, max_boundary_depth=-1),
        lambda q: replace(q, use_newton=1),
        lambda q: replace(q, base_policy=fp.EnclosurePolicy(seconds=0.1)),
        lambda q: replace(q, state=replace(q.state, pending=())),
    ],
)
def test_false_cofinal_checkpoints_rejected(mutation):
    q = mutation(fp.adaptive_complex_isolation(sp.sin(z), z, *RECT, stages=0))
    assert not q.verify()
    with pytest.raises(ValueError, match="checkpoint"):
        fp.resume_adaptive_complex_isolation(q)


def test_cofinal_wall_seed_and_resume_preserve_stage_and_source():
    q = fp.adaptive_complex_isolation(
        sp.sin(z),
        z,
        -4 - sp.I,
        4 + sp.I,
        stages=8,
        policy=fp.EnclosurePolicy(seconds=0.001),
    )
    assert q.verify() and not q.complete and q.next_stage == 0
    r = fp.resume_adaptive_complex_isolation(q, stages=4)
    assert r.verify() and r.complete and r.root_count == 3
    seed = fp.resume_adaptive_complex_isolation(q, stages=4, seconds=0.001)
    assert seed.verify() and not seed.complete and seed.expression == sp.sin(z)


@pytest.fixture(scope="module")
def exact():
    parent = fp.certify_analytic_contour(sp.cosh(z) - 1, z, *RECT)
    result = fp.certify_complex_multiple_root(parent, center=sp.S.Zero)
    assert type(result) is fp.ComplexExactMultiplicity and result.verify()
    return result


@pytest.fixture(scope="module")
def power():
    f = sp.exp(z) * (sp.exp(z) - 1) ** 2
    parent = fp.certify_analytic_contour(f, z, *RECT)
    result = fp.certify_complex_multiple_root(parent)
    assert type(result) is fp.ComplexPowerRootRegion and result.verify()
    return result


def test_exact_taylor_order_and_contour_total(exact):
    assert exact.center == 0 and exact.root_count == 1 and exact.multiplicity_count == 2
    assert exact.jets == (0, 0) and exact.taylor.order == 2
    assert fp.verify_certificate(exact, expr=sp.cosh(z) - 1, var=z)


@pytest.mark.parametrize(
    "expr,multiplicity",
    [
        ((sp.exp(z) - 1) ** 2, 2),
        (sp.exp(z) * (sp.exp(z) - 1) ** 2, 2),
        ((z + 3) * (sp.exp(z) - 1) ** 2, 2),
        ((sp.exp(z) - 2) ** 2, 2),
        (sp.erf(z) ** 3, 3),
    ],
)
def test_individual_multiple_roots_and_accuracy(expr, multiplicity):
    rect = (
        (-sp.I, 1 + sp.I)
        if expr == (sp.exp(z) - 2) ** 2
        else (-sp.Rational(1, 10) - sp.I / 10, sp.Rational(1, 10) + sp.I / 10)
        if expr == sp.erf(z) ** 3
        else RECT
    )
    q = fp.certify_complex_isolation(
        expr,
        z,
        *rect,
        max_box_diameter=sp.Rational(1, 100),
        policy=fp.EnclosurePolicy(max_depth=40, max_cells=4096),
    )
    assert (
        q.verify()
        and q.complete
        and q.root_count == 1
        and q.total_count == multiplicity
    )
    assert q.proof.individual_multiplicities == (multiplicity,) and not q.clusters


def test_nearby_simple_pair_is_not_a_guessed_multiple():
    f = (sp.exp(z) - 1) * (sp.exp(z) - sp.Rational(1001, 1000))
    p = fp.certify_analytic_contour(f, z, *RECT)
    assert p.verify() and p.zero_count == 2
    assert fp.certify_complex_multiple_root(p, center=sp.S.Zero) is None
    q = fp.certify_complex_isolation(
        f, z, *RECT, policy=fp.EnclosurePolicy(max_depth=0)
    )
    assert q.coverage_complete and not q.isolation_complete and q.root_count is None


@pytest.mark.parametrize(
    "center",
    [sp.Float("0.0"), sp.Rational(1, 10**20), sp.I / 100, sp.Symbol("a"), sp.log(2)],
)
def test_approximate_or_unproved_centers_are_declined(exact, center):
    assert fp.certify_complex_multiple_root(exact.parent, center=center) is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: replace(c, center=sp.Rational(1, 100)),
        lambda c: replace(c, multiplicity=3),
        lambda c: replace(c, jets=(0, 1)),
        lambda c: replace(c, source_syntax="other"),
        lambda c: replace(
            c, taylor=replace(c.taylor, coefficients=((sp.S.Zero,) * 4,) * 3)
        ),
        lambda c: replace(c, taylor=replace(c.taylor, order=3)),
        lambda c: replace(c, parent=replace(c.parent, zero_count=3)),
    ],
)
def test_false_exact_order_witnesses_rejected(exact, mutation):
    assert not mutation(exact).verify()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: replace(p, multiplicity=3),
        lambda p: replace(p, base=sp.exp(z) + 1),
        lambda p: replace(p, unit=sp.sin(z)),
        lambda p: replace(p, expression=(sp.exp(z) - 1) ** 2),
        lambda p: replace(
            p, unit_witness=replace(p.unit_witness, expression=sp.sin(z))
        ),
        lambda p: replace(p, base_parent=replace(p.base_parent, zero_count=2)),
    ],
)
def test_false_power_and_unit_proofs_rejected(power, mutation):
    assert not mutation(power.factorization).verify()


def test_located_subsets_preserve_boundary_ownership(exact):
    root = fp.ComplexLocatedRegion(
        exact,
        fp.CoverageRectangle(
            -sp.Rational(1, 10) - sp.I / 10, sp.Rational(1, 10) + sp.I / 10
        ),
    )
    zero = fp.ComplexLocatedRegion(
        exact, fp.CoverageRectangle(sp.Rational(1, 10) - sp.I / 10, 1 + sp.I / 10)
    )
    boundary = fp.ComplexLocatedRegion(
        exact, fp.CoverageRectangle(-sp.I / 10, 1 + sp.I / 10)
    )
    assert root.verify() and root.zero_count == 2 and root.root_count == 1
    assert zero.verify() and zero.zero_count == 0
    assert not boundary.verify()


def test_multiple_roots_do_not_satisfy_the_simple_class_guarantee():
    q = fp.adaptive_complex_isolation((sp.exp(z) - 1) ** 2, z, *RECT, stages=4)
    assert q.verify() and q.complete and q.root_count == 1 and q.total_count == 2
    assert (
        q.termination_contract.verify() and q.termination_contract.applicable is False
    )
    assert "all-zeros-simple" in q.termination_contract.unproved_hypotheses


def test_producer_disabled_replay_for_all_records(exact, power, monkeypatch):
    q = fp.adaptive_complex_isolation(sp.sin(z), z, -4 - sp.I, 4 + sp.I, stages=4)

    def disabled(*args, **kwargs):
        raise AssertionError("search called during replay")

    for module, names in (
        (
            cc,
            (
                "_advance",
                "adaptive_complex_isolation",
                "resume_adaptive_complex_isolation",
            ),
        ),
        (ci, ("_run", "_propose_multiple", "certify_analytic_contour")),
        (
            cm,
            (
                "_propose_multiple",
                "certify_complex_multiple_root",
                "certify_analytic_contour",
            ),
        ),
    ):
        for name in names:
            monkeypatch.setattr(module, name, disabled)
    for record in (
        q,
        q.termination_contract,
        exact,
        exact.taylor,
        power,
        power.factorization,
        power.factorization.unit_witness,
    ):
        assert record.verify() and fp.verify_certificate(record)
        status = fp.replay_status(record)
        assert status.certified and not status.factory_replay


def test_atomic_multiple_and_cofinal_checkpoints():
    seen = []
    with capture_checkpoints(seen.append):
        q = fp.adaptive_complex_isolation(
            (sp.exp(z) - 1) ** 2,
            z,
            *RECT,
            stages=5,
            max_box_diameter=sp.Rational(1, 100),
            policy=fp.EnclosurePolicy(max_depth=40),
        )
    assert q.complete and q.verify() and all(c.verify() for c in seen)
    middle = next(c for c in seen if c.proof.root_regions and not c.complete)
    resumed = fp.resume_adaptive_complex_isolation(
        pickle.loads(pickle.dumps(middle)), stages=5
    )
    assert (
        resumed.complete
        and resumed.verify()
        and resumed.root_count == 1
        and resumed.total_count == 2
    )


def test_public_multiplicity_count_fields():
    q = fp.complex_zeros((sp.exp(z) - 1) ** 2, z, rectangle=RECT, return_result=True)
    assert q.complete and q.verify() and q.root_count == 1 and q.multiplicity_count == 2
    assert q.individual_multiplicities == (2,)
    assert (
        q.rectangles[0].multiplicity_count == 2
        and q.rectangles[0].distinct_root_count == 1
    )


def test_exact_nonreal_multiple_root():
    f = (sp.exp(z - sp.I) - 1) ** 2
    p = fp.certify_analytic_contour(
        f,
        z,
        -sp.Rational(1, 10) + sp.I * sp.Rational(9, 10),
        sp.Rational(1, 10) + sp.I * sp.Rational(11, 10),
    )
    c = fp.certify_complex_multiple_root(p, center=sp.I)
    assert (
        c.verify()
        and c.center == sp.I
        and c.root_count == 1
        and c.multiplicity_count == 2
    )


def test_mixed_simple_and_multiple_roots_have_correct_totals():
    f = (sp.exp(z) - 1) ** 2 * (sp.exp(z) - 2)
    q = fp.certify_complex_isolation(
        f,
        z,
        -sp.Rational(1, 10) - sp.I,
        1 + sp.I,
        policy=fp.EnclosurePolicy(max_depth=32, max_cells=4096),
    )
    assert q.complete and q.verify() and q.root_count == 2 and q.total_count == 3
    assert sorted(q.proof.individual_multiplicities) == [1, 2]


def test_cofinal_series_growth_releases_a_small_erf_problem():
    base = fp.EnclosurePolicy(
        precision=2,
        max_precision=2,
        max_refinements=0,
        max_series_terms=0,
        max_cells=64,
        max_depth=12,
    )
    q = fp.adaptive_complex_isolation(
        sp.erf(z),
        z,
        -sp.Rational(1, 10) - sp.I / 10,
        sp.Rational(1, 10) + sp.I / 10,
        stages=8,
        policy=base,
    )
    assert q.complete and q.verify() and q.root_count == 1 and q.next_stage > 1


def test_multiple_refinement_complements():
    q = fp.certify_complex_isolation(
        sp.cosh(z) - 1,
        z,
        *RECT,
        max_box_diameter=sp.Rational(1, 100),
        policy=fp.EnclosurePolicy(max_depth=32),
    )
    assert q.complete and q.verify() and q.proof.zero_regions
    p = q.proof
    for zeros in (p.zero_regions[1:], (*p.zero_regions, p.zero_regions[0])):
        assert not ci._assembled(p, zeros=zeros).verify()


def test_altered_conditional_theorem_and_source_rejected():
    q = fp.adaptive_complex_isolation(sp.sin(z), z, *RECT, stages=0)
    assert not replace(q.termination_contract, theorem="unconditional").verify()
    assert (
        fp.replay_status(q.termination_contract, expr=sp.cos(z), var=z).certified
        is False
    )


def test_multiple_helper_wall_budget_and_false_unit_proof(power):
    assert (
        fp.certify_complex_multiple_root(
            power.factorization.parent, policy=fp.EnclosurePolicy(seconds=0.001)
        )
        is None
    )
    fake = replace(
        power.factorization.unit_witness,
        expression=sp.S.Zero,
        source_syntax=sp.srepr(sp.S.Zero),
    )
    assert not fake.verify()


def test_failed_factor_heuristic_does_not_disable_cofinal_contours(monkeypatch):
    def failed(*args, **kwargs):
        raise sp.PolynomialError("unsupported factor heuristic")

    monkeypatch.setattr(cm.sp, "factor", failed)
    q = fp.adaptive_complex_isolation(sp.sin(z), z, -4 - sp.I, 4 + sp.I, stages=5)
    assert q.complete and q.verify() and q.root_count == 3
