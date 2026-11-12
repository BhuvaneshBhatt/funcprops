"""Function-value bounds close some tails with infinitely many stationary points."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
f = x * x + sp.sin(x**3) ** 2


def test_nonmonotone_tail_image():
    facts = tuple(
        fp.bound_range_tail(f, x, D)
        for D in (
            sp.Interval.open(-sp.oo, -sp.Rational(1, 2)),
            sp.Interval.open(sp.Rational(1, 2), sp.oo),
        )
    )
    assert all(
        t.verify() and not t.certified and t.bound == sp.Rational(1, 4) for t in facts
    )
    r = fp.analyze_range(f, x, tail_facts=facts, certified=True)
    assert r.image == sp.Interval(0, sp.oo) and r.verify() and r.certified
    assert not r.critical_coverage_complete
    assert fp.refine_range(r).image == r.image
    for bad in (
        replace(facts[0], bound=2),
        replace(facts[0], limit=-sp.oo),
        replace(facts[0], remainder_bounds=(0, 0)),
    ):
        assert not bad.verify()
        with pytest.raises(ValueError):
            fp.analyze_range(f, x, tail_facts=(bad, facts[1]))
    with pytest.raises(ValueError):
        fp.analyze_range(f + 1, x, tail_facts=facts)


def test_unknown_tail():
    assert fp.bound_range_tail(sp.sin(x**3), x, sp.Interval.open(1, sp.oo)) is None
    assert fp.bound_range_tail(f, x, sp.Interval.open(1, sp.oo), limit=-sp.oo) is None


def test_automatic_tail_route():
    r = fp.analyze_range(f, x)
    assert r.image == sp.Interval(0, sp.oo) and r.verify()
    y = sp.Symbol("y", real=True)
    assert fp.condition_to_real_set(fp.range(f, x, y), y) == sp.Interval(0, sp.oo)


def test_tail_join_ownership():
    g = (x - 2) ** 2 + sp.sin((x - 2) ** 3) ** 2
    assert fp.bound_range_tail(g, x, sp.Interval(2, sp.oo)) is None
    fact = fp.bound_range_tail(g, x, sp.Interval.open(2, sp.oo))
    r = fp.analyze_range(g, x, sp.Interval(1, sp.oo), tail_facts=(fact,))
    assert r.image == sp.Interval(0, sp.oo) and r.verify()


def test_opposite_limits_need_no_core_search():
    g = x**3 + sp.sin(x**3)
    facts = tuple(
        fp.bound_range_tail(g, x, D)
        for D in (sp.Interval.open(-sp.oo, -1), sp.Interval.open(1, sp.oo))
    )
    r = fp.analyze_range(g, x, tail_facts=facts, policy=fp.EnclosurePolicy(max_cells=0))
    assert r.image is sp.S.Reals and r.verify() and r.transfer.core is None
    assert not replace(r, transfer=replace(r.transfer, tails=facts[:1])).verify()


def test_tail_core_binding():
    r = fp.analyze_range(f, x)
    core = r.transfer.core
    other = fp.analyze_range(-sp.S.One, x, core.requested)
    assert other.verify() and other.image == sp.FiniteSet(-1)
    forged = replace(
        r,
        transfer=replace(r.transfer, core=other),
        image=sp.Interval(-1, sp.oo),
        inner=sp.Interval(-1, sp.oo),
        outer=sp.Interval(-1, sp.oo),
    )
    assert not forged.verify()
