"""General local recipes, implicit relations and exhaustive overlap replay."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

z, w, u, v = sp.symbols("z w u v")
D = fp.CoverageRectangle(1 - sp.I / 4, 2 + sp.I / 4)


@pytest.fixture(scope="module")
def logarithm():
    return fp.certify_log_atlas(z, z, (D,)).charts[0]


def root_chart(logarithm, sheet):
    return fp.certify_branch_chart(
        (w - z) ** 2 - z,
        z,
        w,
        D,
        z + sp.exp(u / 2),
        logarithms=((u, replace(logarithm, sheet=sheet)),),
    )


def test_recipe_gluing(logarithm):
    a, b = root_chart(logarithm, 0), root_chart(logarithm, 2)
    p = fp.glue_branch_charts((a, b))
    assert a.verify() and fp.verify_certificate(a)
    assert p.verify() and p.coverage_complete and p.gluing_complete
    assert p.overlaps[0].method == "log-transitions"
    assert p.overlaps[0].turns == ((0, 0, 2),)
    assert fp.verify_certificate(p, expr=(w - z) ** 2 - z, var=z)


def test_different_branches(logarithm):
    p = fp.glue_branch_charts((root_chart(logarithm, 0), root_chart(logarithm, 1)))
    assert p.verify() and p.coverage_complete and not p.complete
    assert len(p.obstructions) == 1 and p.obstructions[0].status == "different"
    assert (
        fp.replay_status(p).certified is True and fp.replay_status(p).complete is False
    )


def test_derivative_anchor_gluing(logarithm):
    base = fp.certify_log_atlas(z * z, z, (D,)).charts[0]
    a = fp.certify_branch_chart(
        sp.exp(2 * w) - z * z, z, w, D, u, logarithms=((u, logarithm),)
    )
    b = fp.certify_branch_chart(
        sp.exp(2 * w) - z * z, z, w, D, v / 2, logarithms=((v, base),)
    )
    p = fp.glue_branch_charts((a, b))
    assert p.verify() and p.complete
    assert p.overlaps[0].method == "derivative-anchor"


def test_multiple_logarithms(logarithm):
    shifted = fp.certify_log_atlas(z + 1, z, (D,)).charts[0]
    relation = w * w - z * (z + 1)
    a = fp.certify_branch_chart(
        relation,
        z,
        w,
        D,
        sp.exp((u + v) / 2),
        logarithms=((u, logarithm), (v, shifted)),
    )
    b = fp.certify_branch_chart(
        relation,
        z,
        w,
        D,
        sp.exp((u + v) / 2),
        logarithms=((u, replace(logarithm, sheet=1)), (v, replace(shifted, sheet=1))),
    )
    p = fp.glue_branch_charts((a, b))
    assert p.verify() and p.complete
    assert p.overlaps[0].turns == ((0, 0, 1), (1, 1, 1))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, overlaps=()),
        lambda p: replace(p, overlaps=p.overlaps * 2),
        lambda p: replace(p, overlaps=(replace(p.overlaps[0], anchor=0),)),
        lambda p: replace(p, overlaps=(replace(p.overlaps[0], turns=((0, 0, 99),)),)),
        lambda p: replace(p, charts=p.charts * 2),
        lambda p: replace(p, relation=w * w - z),
        lambda p: replace(p, variable=sp.Symbol("q")),
        lambda p: replace(p, requested=(fp.CoverageRectangle(0, 3 + sp.I),)),
    ],
)
def test_gluing_mutations(logarithm, mutate):
    p = fp.glue_branch_charts((root_chart(logarithm, 0), root_chart(logarithm, 2)))
    altered = mutate(p)
    assert not altered.verify() and not fp.verify_certificate(altered)


def test_unresolved_overlap(logarithm):
    p = fp.glue_branch_charts((root_chart(logarithm, 0), root_chart(logarithm, 2)))
    partial = replace(
        p,
        overlaps=(
            replace(p.overlaps[0], status="unresolved", method="unresolved", turns=()),
        ),
    )
    assert partial.verify() and not partial.complete and partial.unresolved_overlaps
    assert not replace(
        partial, overlaps=(replace(partial.overlaps[0], status="equal"),)
    ).verify()


def test_unresolved_coverage(logarithm):
    chart = root_chart(logarithm, 0)
    larger = fp.CoverageRectangle(1 - sp.I / 4, 3 + sp.I / 4)
    missing = fp.CoverageRectangle(2 - sp.I / 4, 3 + sp.I / 4)
    p = fp.glue_branch_charts((chart,), requested=(larger,), unresolved=(missing,))
    assert p.verify() and not p.coverage_complete
    assert not replace(p, unresolved=()).verify()


def test_gluing_replay(logarithm, monkeypatch):
    p = fp.glue_branch_charts((root_chart(logarithm, 0), root_chart(logarithm, 2)))

    def disabled(*args, **kwargs):
        raise AssertionError("proposer called")

    monkeypatch.setattr("funcprops.branch_gluing.glue_branch_charts", disabled)
    monkeypatch.setattr("funcprops.branch_gluing.certify_branch_chart", disabled)
    monkeypatch.setattr("funcprops.branch_atlas.certify_log_atlas", disabled)
    assert p.verify() and fp.verify_certificate(p)


def test_chart_source_binding(logarithm):
    a = root_chart(logarithm, 0)
    for bad in (
        replace(a, formula=z),
        replace(a, relation=w - z),
        replace(a, logarithms=()),
        replace(a, value_symbol=sp.Symbol("w", real=True)),
    ):
        assert not bad.verify() and not fp.verify_certificate(bad)


def test_held_hole_rejected():
    raw = sp.Add(
        z, sp.Mul(0, sp.Pow(z - 1, -1, evaluate=False), evaluate=False), evaluate=False
    )
    with pytest.raises(ValueError):
        fp.certify_branch_chart(w - z, z, w, D, raw)


def test_boundary_germs():
    a = fp.certify_branch_chart(w - z * z, z, w, D, z * z)
    E = fp.CoverageRectangle(2 - sp.I / 4, 3 + sp.I / 4)
    b = fp.certify_branch_chart(w - z * z, z, w, E, z * z)
    p = fp.glue_branch_charts((a, b))
    assert p.verify() and p.complete and len(p.overlaps) == 1
    assert p.overlaps[0].anchor == 2


def test_gluing_budget(logarithm):
    result = fp.glue_branch_charts(
        (root_chart(logarithm, 0),), work_budget=sp.Rational(1, 1000000)
    )
    assert result.complete is False and result.certified is False
