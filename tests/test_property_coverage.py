from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.property_checker import candidates

x = sp.Symbol("x", real=True)
P = fp.EnclosurePolicy(
    precision=20, max_precision=60, max_refinements=2, max_cells=240, max_depth=6
)


def test_exp_minus_x_global_range_and_extrema(monkeypatch):
    f = sp.exp(x) - x
    c = fp.certify_property_coverage(f, x, sp.Interval(-1, 2), policy=P)
    assert c.verify() and c.complete and c.range_complete and c.optimization_complete
    assert c.conclusion("minimum").value == (1, sp.FiniteSet(0))
    assert c.conclusion("maximum").value == (sp.exp(2) - 2, sp.FiniteSet(2))
    assert c.conclusion("range").value == sp.Interval(1, sp.exp(2) - 2)
    assert c.sign_complete and c.monotonicity_complete

    def disabled(*a, **k):
        raise AssertionError("producer used in replay")

    monkeypatch.setattr(
        "funcprops.property_coverage.certify_property_coverage", disabled
    )
    monkeypatch.setattr("funcprops.property_coverage.adaptive_root_coverage", disabled)
    monkeypatch.setattr(sp, "solveset", disabled)
    assert c.verify() and fp.verify_certificate(c, expr=f, var=x)
    assert fp.replay_status(c).outcome == "complete-coverage"
    assert fp.replay_status(c).factory_replay is False
    assert (
        next(
            r
            for r in fp.proof_api_manifest()["records"]
            if r["type"] == "funcprops.property_contract.PropertyCoverageProof"
        )["contract"]
        == "witness-kernel"
    )


@pytest.mark.parametrize(
    "D,expected,owners",
    [
        (sp.Interval.open(-1, 2), sp.Interval.Ropen(0, 4), sp.FiniteSet(0)),
        (sp.Interval.open(0, 2), sp.Interval.open(0, 4), sp.S.EmptySet),
        (
            sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2)),
            sp.Interval(1, 4),
            sp.FiniteSet(-1, 1),
        ),
        (sp.FiniteSet(0, 2), sp.FiniteSet(0, 4), sp.FiniteSet(0)),
    ],
)
def test_components_endpoints_singletons(D, expected, owners):
    c = fp.certify_property_coverage(x * x, x, D, policy=P)
    assert c.complete and c.verify()
    assert c.conclusion("range").value.doit() == expected
    assert c.conclusion("minimum").value[1] == owners


def test_piecewise_jump_and_singleton_value_are_not_dropped():
    f = sp.Piecewise((x, x < 0), (100, sp.Eq(x, 0)), (x + 10, True))
    c = fp.certify_property_coverage(f, x, sp.Interval(-1, 1), policy=P)
    assert c.complete and c.verify()
    assert c.conclusion("maximum").value == (100, sp.FiniteSet(0))
    image = c.conclusion("range").value
    assert image.contains(100) is sp.S.true and image.contains(0) is sp.S.false
    assert image.doit() == sp.Union(
        sp.Interval.Ropen(-1, 0), sp.Interval.Lopen(10, 11), sp.FiniteSet(100)
    )
    assert not replace(c, pieces=c.pieces[:-1]).verify()
    assert not replace(c, pieces=c.pieces + c.pieces[:1]).verify()


@pytest.mark.parametrize(
    "f,D",
    [
        (sp.S(3), sp.Interval.open(-1, 1)),
        (sp.S.Zero, sp.Interval(-1, 1)),
        (x, sp.S.EmptySet),
    ],
)
def test_constant_and_empty_domains(f, D):
    c = fp.certify_property_coverage(f, x, D, policy=P)
    assert c.complete and c.verify()
    if D is not sp.S.EmptySet:
        assert c.conclusion("range").value == sp.FiniteSet(f)
        assert c.conclusion("minimum").value == (f, D)
    else:
        assert c.conclusion("range").value is sp.S.EmptySet


def test_unresolved_critical_cover_keeps_range_incomplete():
    f = sp.exp(x) - x
    D = sp.Interval(-1, 2)
    pending = fp.adaptive_root_coverage(
        sp.exp(x) - 1, x, sp.Interval.open(-1, 2), policy=replace(P, max_cells=0)
    ).proof
    c = fp.certify_property_coverage(f, x, D, policy=P, critical_covers=(pending,))
    assert c.verify() and not c.range_complete and not c.optimization_complete
    assert c.sign_complete and not c.monotonicity_complete
    assert c.conclusion("minimum").value is None
    assert not replace(
        c, conclusions=tuple(replace(q, complete=True) for q in c.conclusions)
    ).verify()


def test_forged_critical_locations_and_value_orders_rejected():
    c = fp.certify_property_coverage(sp.exp(x) - x, x, sp.Interval(-1, 2), policy=P)
    p = c.pieces[0]
    assert not replace(c, pieces=(replace(p, critical_points=()),)).verify()
    assert not replace(c, pieces=(replace(p, critical_points=(sp.S.One,)),)).verify()
    assert not replace(
        c, pieces=(replace(p, critical_points=(sp.S.Zero, sp.S.Zero)),)
    ).verify()
    assert not replace(c, candidate_order=tuple(reversed(c.candidate_order))).verify()
    assert not replace(c, comparisons=(None,) * len(c.comparisons)).verify()
    assert not replace(
        c, expression=sp.exp(x) + x, source_syntax=sp.srepr(sp.exp(x) + x)
    ).verify()
    assert fp.replay_status(replace(c, schema_version=2)).certified is None
    assert len(candidates(c)) == 3


def test_wrong_supplied_cover_and_source_holes():
    wrong = fp.adaptive_root_coverage(x, x, sp.Interval.open(-1, 2), policy=P).proof
    with pytest.raises(ValueError):
        fp.certify_property_coverage(
            sp.exp(x) - x, x, sp.Interval(-1, 2), policy=P, critical_covers=(wrong,)
        )
    raw = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    c = fp.certify_property_coverage(raw, x, sp.Interval(-1, 1), policy=P)
    assert not c.range_complete and not c.optimization_complete
    assert c.domain_record.effective.contains(0) is sp.S.false
    assert not fp.certify_property_coverage(
        sp.log(x), x, sp.Interval(0, 1), policy=P
    ).range_complete


def test_property_budget_and_missing_exact_locations():
    c = fp.certify_property_coverage(
        sp.exp(x) - x, x, sp.Interval(-1, 2), policy=replace(P, max_cells=0)
    )
    assert c.tested == 0 and c.verify() and not c.complete
    assert fp.replay_status(c).outcome == "resource-exhaustion"
    # Exhaustive numerical critical isolation alone does not provide an exact
    # image of that root, so this exact-range interface remains incomplete.
    c = fp.certify_property_coverage(sp.exp(x) - 2 * x, x, sp.Interval(-1, 2), policy=P)
    if c.range_complete:
        assert c.conclusion("minimum").value[1] == sp.FiniteSet(sp.log(2))
    else:
        assert c.conclusion("range").value is None


def test_wall_timeout_and_unbounded_domains_are_explicit():
    c = fp.certify_property_coverage(
        sp.exp(x) - x, x, sp.Interval(-1, 2), policy=replace(P, seconds=0.000001)
    )
    assert not c.complete and c.verify() and c.exhaustion == "wall-budget"
    assert fp.replay_status(c).outcome == "resource-exhaustion"
    c = fp.certify_property_coverage(x * x, x, sp.S.Reals, policy=P)
    assert not c.complete and fp.replay_status(c).complete is False


def test_partition_seam_ownership():
    f = sp.Piecewise((x * x, x < 0), (-5, sp.Eq(x, 0)), (2 - x, True))
    D = sp.Interval(-2, 3)
    c = fp.certify_property_coverage(f, x, D, policy=P)
    assert c.complete and c.verify()
    for name in ("sign", "monotonicity"):
        cells = tuple(d for d, _ in c.conclusion(name).value)
        assert sp.Union(*cells) == D
        for i, a in enumerate(cells):
            assert all(sp.Intersection(a, b) is sp.S.EmptySet for b in cells[i + 1 :])
    assert c.conclusion("minimum").value == (-5, sp.FiniteSet(0))


def test_endpoint_witnesses_use_kernel_replay_not_self_attestation(monkeypatch):
    from types import SimpleNamespace

    from funcprops.property_checker import _AUX

    c = fp.certify_property_coverage(x, x, sp.FiniteSet(-1), policy=P)
    fake = SimpleNamespace(
        expression=sp.S.NegativeOne,
        variable=_AUX,
        domain=sp.FiniteSet(0),
        lower=sp.S.One,
        upper=sp.Integer(2),
        verify=lambda: True,
    )
    p = replace(c.pieces[0], sign_samples=(fake,))
    conclusions = tuple(
        replace(q, value=((sp.FiniteSet(-1), 1),)) if q.name == "sign" else q
        for q in c.conclusions
    )
    assert replace(c, pieces=(p,), conclusions=conclusions).check().certified is False
    # Even an altered self-verifier on the native class cannot replace the
    # primitive enclosure checker used for endpoint and candidate-order replay.
    monkeypatch.setattr(fp.EnclosureWitness, "verify", lambda self: True)
    w = replace(c.pieces[0].sign_samples[0], lower=sp.S.One, upper=sp.Integer(2))
    assert not replace(
        c, pieces=(replace(p, sign_samples=(w,)),), conclusions=conclusions
    ).verify()
    assert c.verify()
