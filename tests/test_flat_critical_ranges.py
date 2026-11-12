"""Higher-order exact jets resolve flat stationary points within finite effort."""

from dataclasses import replace

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


def test_flat_minimum():
    f = x**6 + (sp.exp(x) - 1) ** 6
    D = sp.Interval(-sp.Rational(1, 100), sp.Rational(1, 100))
    policy = fp.EnclosurePolicy(
        max_cells=16, max_depth=2, max_root_order=8, max_refinements=0
    )
    coarse = fp.analyze_range(f, x, D, policy=replace(policy, max_root_order=3))
    assert coarse.verify() and not coarse.complete
    r = fp.analyze_range(f, x, D, policy=policy)
    assert r.verify() and r.image.start == 0 and not r.image.left_open
    assert r.cells[0].critical_cover.root_count == 1
    assert r.cells[0].critical_cover.multiplicity_count == 5
    expected = sp.Rational(1, 10**12) + (sp.exp(sp.Rational(1, 100)) - 1) ** 6
    assert sp.simplify(r.image.end - expected) == 0


def test_no_exact_jet_guess():
    f = x**6 + (sp.exp(x) - 1) ** 6 + sp.Rational(1, 10**50) * x
    r = fp.analyze_range(
        f,
        x,
        sp.Interval(-sp.Rational(1, 100), sp.Rational(1, 100)),
        policy=fp.EnclosurePolicy(max_cells=0),
    )
    assert not r.complete and r.image is None
