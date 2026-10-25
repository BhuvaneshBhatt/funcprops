from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, a, b = sp.symbols("x a b", real=True)
P = fp.EnclosurePolicy(
    precision=20, max_precision=80, max_refinements=2, max_cells=80, max_depth=5
)


@pytest.mark.parametrize(
    "f,box,D,count",
    [
        (
            sp.exp(x) + a * x - b,
            {
                a: sp.Interval(-sp.Rational(1, 4), sp.Rational(1, 4)),
                b: sp.Interval(sp.Rational(3, 2), 2),
            },
            sp.Interval(0, 1),
            1,
        ),
        (
            sp.log(x + a) - b,
            {
                a: sp.Interval(1, sp.Rational(11, 10)),
                b: sp.Interval(sp.Rational(3, 10), sp.Rational(2, 5)),
            },
            sp.Interval(0, 1),
            1,
        ),
        (a * x + 10, {a: sp.Interval(-1, 1)}, sp.Interval(-1, 1), 0),
        (x + a * x * x, {a: sp.Interval(0, sp.Rational(1, 4))}, sp.Interval(0, 1), 1),
        (
            x + a * x * x,
            {a: sp.Interval(0, sp.Rational(1, 4))},
            sp.Interval.Lopen(0, 1),
            0,
        ),
        (
            x * x - a,
            {a: sp.Interval(sp.Rational(1, 8), sp.Rational(1, 4))},
            sp.Interval(-1, 1),
            2,
        ),
    ],
)
def test_entire_box_proof_and_disjoint_multi_root_assembly(f, box, D, count):
    c = fp.certify_parameter_box(f, x, box, D, policy=P)
    assert c.complete and c.root_count == count and c.verify() and c.certified
    assert fp.replay_status(c).outcome == "complete-coverage"
    if isinstance(c, fp.UniformParameterCover):
        assert len([a for a in c.leaves if a.root_count]) == 2
        assert sp.Union(*(a.domain for a in c.leaves)) == D
        assert not replace(c, leaves=c.leaves[1:]).verify()
        assert not replace(c, leaves=c.leaves + c.leaves[:1]).verify()


def test_uniform_witness_is_bound_to_whole_box_and_source(monkeypatch):
    g = sp.exp(x) + a * x - b
    box = {
        a: sp.Interval(-sp.Rational(1, 4), sp.Rational(1, 4)),
        b: sp.Interval(sp.Rational(3, 2), 2),
    }
    c = fp.certify_parameter_box(g, x, box, sp.Interval(0, 1), policy=P)
    assert isinstance(c, fp.UniformParameterCertificate)
    assert not replace(
        c, parameter_domains=((a, sp.Interval(-2, 2)), (b, box[b]))
    ).verify()
    assert not replace(c, expression=g + 1, source_syntax=sp.srepr(g + 1)).verify()
    assert not replace(c, root_count=2, multiplicity_count=2).verify()
    bad = replace(c.witness.derivative, lower=100, upper=101)
    assert not replace(c, witness=replace(c.witness, derivative=bad)).verify()

    def disabled(*args, **kwargs):
        raise AssertionError("box search called during replay")

    monkeypatch.setattr("funcprops.parameter_coverage._box_bound", disabled)
    monkeypatch.setattr("funcprops.parameter_coverage.certify_parameter_box", disabled)
    assert c.verify()


@pytest.mark.parametrize(
    "g,box",
    [
        (x * x - a, {a: sp.Interval(-1, 1)}),
        (sp.log(x + a) - 1, {a: sp.Interval(-1, 1)}),
        (1 / (x - a), {a: sp.Interval(-1, 1)}),
        (sp.sqrt(x + a) - 1, {a: sp.Interval(-1, 1)}),
    ],
)
def test_collision_pole_or_branch_change_prevents_complete_count(g, box):
    c = fp.certify_parameter_box(
        g, x, box, sp.Interval(-1, 1), policy=replace(P, max_cells=12)
    )
    assert not c.complete and c.root_count is None


def test_parameter_subdivision_uses_uniform_multi_root_cover():
    c = fp.parameter_root_coverage(
        x * x - a,
        x,
        a,
        sp.Interval(-1, 1),
        parameter_domain=sp.Interval(sp.Rational(1, 8), sp.Rational(1, 4)),
        policy=P,
    )
    assert c.complete and c.verify() and c.cells[0].root_count == 2


def test_transcendental_collision_region_is_explicitly_unresolved():
    c = fp.parameter_root_coverage(
        sp.exp(x) - 1 - x - a,
        x,
        a,
        sp.Interval(-1, 1),
        parameter_domain=sp.Interval(-sp.Rational(1, 10), sp.Rational(1, 10)),
        policy=replace(P, max_cells=12, max_depth=2),
    )
    assert not c.complete and c.unresolved is not sp.S.EmptySet and c.verify()
    assert c.unresolved.contains(0) is sp.S.true


@pytest.mark.parametrize("seconds", [None, 0.001])
def test_zero_or_time_budget_does_not_claim_uniform_box_completion(seconds):
    policy = replace(P, max_cells=0, seconds=seconds)
    c = fp.certify_parameter_box(
        sp.exp(x) - a, x, {a: sp.Interval(1, 2)}, sp.Interval(0, 1), policy=policy
    )
    assert not c.complete and c.root_count is None
    assert fp.replay_status(c).outcome == "resource-exhaustion"
