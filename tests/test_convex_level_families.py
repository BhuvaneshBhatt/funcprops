"""Minimum and endpoint events partition strictly convex transcendental levels."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, a = sp.symbols("x a", real=True)
f = sp.exp(x) - 1 - x - a


@pytest.mark.parametrize(
    "D", [sp.Interval(-1, 1), sp.Interval.open(-1, 1), sp.Interval.Ropen(-1, 1)]
)
def test_level_events(D):
    r = fp.parameter_root_coverage(f, x, a, D)
    assert r.complete and r.verify()
    expected = [(-1, 0, 0), (0, 1, 2), (sp.Rational(1, 10), 2, 2), (1, 0, 0)]
    for value, count, multiplicity in expected:
        p = fp.specialize_parameter_coverage(r, value)
        assert (
            p.verify()
            and p.root_count == count
            and p.multiplicity_count == multiplicity
        )
    at_left = fp.specialize_parameter_coverage(r, sp.exp(-1))
    assert at_left.root_count == (1 if D.left_open else 2)
    at_right = fp.specialize_parameter_coverage(r, sp.E - 2)
    assert at_right.root_count == (0 if D.right_open else 1)
    cell = next(c for c in r.cells if c.region == sp.FiniteSet(0))
    bad = replace(cell, witness=replace(cell.witness, minimum=sp.S.One))
    assert not replace(
        r, cells=tuple(bad if c is cell else c for c in r.cells)
    ).verify()


def test_level_budget():
    r = fp.parameter_root_coverage(
        f, x, a, sp.Interval(-1, 1), policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert not r.complete and r.unresolved is sp.S.Reals


def test_level_replay(monkeypatch):
    r = fp.parameter_root_coverage(f, x, a, sp.Interval(-1, 1))

    def disabled(*args, **kwargs):
        raise AssertionError("root discovery used in replay")

    monkeypatch.setattr("funcprops.parameter_coverage._convex_level_cells", disabled)
    monkeypatch.setattr(sp, "solveset", disabled)
    assert r.verify()
