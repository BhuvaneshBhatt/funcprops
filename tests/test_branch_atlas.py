from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
P = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=160, max_depth=8
)


def ring():
    return (
        fp.CoverageRectangle(-2 - sp.I / 4, 2 - sp.I / 8),
        fp.CoverageRectangle(-2 + sp.I / 8, 2 + sp.I / 4),
        fp.CoverageRectangle(-2 - sp.I / 4, -sp.Rational(7, 4) + sp.I / 4),
        fp.CoverageRectangle(sp.Rational(7, 4) - sp.I / 4, 2 + sp.I / 4),
    )


@pytest.fixture(scope="module")
def loop():
    return fp.certify_log_atlas(z, z, ring(), policy=P)


def test_negative_axis_chart_and_gluing_across_principal_cut():
    D = fp.CoverageRectangle(-2 - sp.I / 4, -1 + sp.I / 4)
    a = fp.certify_log_atlas(z, z, (D,), policy=P)
    assert a.verify() and a.complete and a.charts[0].phase == 2
    assert (
        a.charts[0].logarithm.subs(z, -sp.Rational(3, 2))
        == sp.log(sp.Rational(3, 2)) + sp.I * sp.pi
    )
    assert fp.verify_certificate(a.charts[0])
    assert not fp.verify_certificate(replace(a.charts[0], phase=0))
    top = fp.certify_log_atlas(
        z, z, (fp.CoverageRectangle(-2 + sp.I / 8, -1 + sp.I / 2),), policy=P
    )
    glued = fp.glue_log_charts(a.charts + top.charts)
    assert glued.verify() and glued.complete
    assert all(t.turns == 0 for t in glued.transitions)


def test_nontrivial_log_monodromy_and_power_transitions(loop):
    assert loop.verify() and loop.coverage_complete and not loop.gluing_complete
    assert loop.obstructions and not loop.complete
    assert fp.replay_status(loop).complete is False
    p = fp.GluedPowerProof(loop, sp.S.One)
    assert p.verify() and p.complete and fp.verify_certificate(p)
    q = fp.GluedPowerProof(loop, sp.S.Half)
    assert q.verify() and not q.complete
    assert -1 in q.multipliers
    assert not fp.verify_certificate(replace(p, exponent=z))


def test_power_can_glue_even_when_logarithm_cannot():
    a = fp.certify_log_atlas(z * z, z, ring(), policy=P)
    assert a.verify() and a.coverage_complete and not a.complete
    p = fp.GluedPowerProof(a, sp.S.Half)
    assert p.verify() and p.complete
    assert all(m == 1 for m in p.multipliers)


def test_single_valued_exponential_log_lift():
    a = fp.certify_log_atlas(
        sp.exp(z), z, (fp.CoverageRectangle(-1 - 4 * sp.I, 1 + 4 * sp.I),), policy=P
    )
    assert a.verify() and a.complete
    assert len(a.charts) > 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda a: replace(a, transitions=()),
        lambda a: replace(a, transitions=a.transitions * 2),
        lambda a: replace(
            a, transitions=(replace(a.transitions[0], turns=77), *a.transitions[1:])
        ),
        lambda a: replace(a, charts=a.charts[:-1]),
        lambda a: replace(a, charts=a.charts * 2),
        lambda a: replace(a, expression=z + 1),
        lambda a: replace(
            a, requested=(fp.CoverageRectangle(-2 - 2 * sp.I, 2 + 2 * sp.I),)
        ),
        lambda a: replace(a, schema_version=2),
    ],
)
def test_altered_atlas_rejected(loop, mutate):
    assert not mutate(loop).verify() and fp.verify_certificate(mutate(loop)) is False


def test_unresolved_zero_and_work_limits_remain_incomplete():
    a = fp.certify_log_atlas(
        z,
        z,
        (fp.CoverageRectangle(-1 - sp.I, 1 + sp.I),),
        policy=replace(P, max_depth=2, max_cells=16, max_refinements=0),
    )
    assert a.verify() and not a.coverage_complete and a.unresolved
    a = fp.certify_log_atlas(
        z, z, (fp.CoverageRectangle(1, 2 + sp.I),), policy=replace(P, max_cells=0)
    )
    assert a.verify() and not a.complete


def test_atlas_replay_does_not_call_search(loop, monkeypatch):
    def disabled(*args, **kwargs):
        raise AssertionError("search called")

    monkeypatch.setattr("funcprops.branch_atlas.certify_log_atlas", disabled)
    monkeypatch.setattr("funcprops.branch_atlas.glue_log_charts", disabled)
    assert loop.verify() and fp.verify_certificate(loop)


def test_raw_source_holes_and_symbol_assumptions_decline():
    raw = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    for f, x in [(raw, z), (z, sp.Symbol("z", real=True))]:
        with pytest.raises(ValueError):
            fp.certify_log_atlas(f, x, (fp.CoverageRectangle(1, 2 + sp.I),), policy=P)
