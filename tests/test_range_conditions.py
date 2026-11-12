"""Exact image formulas keep ownership without a total critical-value order."""

from dataclasses import replace

import sympy as sp

import funcprops as fp
from funcprops.real_images.analysis import _cell_condition

x, y = sp.symbols("x y", real=True)


def test_unsorted_sites():
    r = fp.analyze_range(x * x, x, sp.Interval.open(-1, 1), _transfers=False)
    cell = replace(
        r.cells[0], sites=tuple(replace(s, enclosure=None) for s in r.cells[0].sites)
    )
    assert cell.verify()
    condition = _cell_condition(cell, y)
    for value, expected in [
        (-1, False),
        (0, True),
        (sp.Rational(1, 2), True),
        (1, False),
        (2, False),
    ]:
        assert bool(condition.subs(y, value)) is expected


def test_condition_contract():
    r = fp.analyze_range(x * x + sp.sin(x), x, sp.Interval(-1, 1))
    assert r.complete and r.verify()
    condition = r.as_condition(y)
    assert condition.subs(y, 0) is sp.true
    assert condition.subs(y, 2) is sp.false
    partial = fp.analyze_range(
        x * x + sp.sin(x), x, sp.Interval(-1, 1), policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert partial.as_condition(y) is None


def test_automatic_parameter_family():
    a = sp.Symbol("a", real=True)
    condition = fp.range(sp.exp(x * x + a * x), x, y, domain=sp.Interval.open(-1, 1))
    assert fp.condition_to_real_set(condition.subs(a, 0), y) == sp.Interval.Ropen(
        1, sp.E
    )


def test_normalized_constant_keeps_hole():
    held = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    r = fp.analyze_range(held, x)
    assert r.image == sp.FiniteSet(1) and r.verify()
    assert r.domain_record.effective == sp.S.Reals - sp.FiniteSet(0)
    assert fp.analyze_range(held, x, sp.FiniteSet(0)).image is sp.S.EmptySet
