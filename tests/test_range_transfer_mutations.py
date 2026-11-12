"""Every premise of the new image transfers is exercised by a rejecting mutation."""

from dataclasses import fields, replace

import pytest
import sympy as sp

import funcprops as fp

x, z = sp.symbols("x z", real=True)


@pytest.mark.parametrize("kind", ["escape", "dense", "finite"])
def test_transfer_payload(kind):
    if kind == "escape":
        r = fp.analyze_range(x * sp.sin(x), x).transfer
        changes = {
            "expression": r.expression + 1,
            "variable": z,
            "domain": sp.Interval(0, 1),
            "amplitude": sp.S.One,
            "offset": sp.S.One,
            "oscillator": sp.cos(x),
            "direction": -1,
            "sequences": (),
        }
    elif kind == "dense":
        r = fp.analyze_range(sp.sin(x) + sp.sin(sp.sqrt(2) * x), x).transfer
        changes = {
            "expression": r.expression + 1,
            "variable": z,
            "domain": sp.Interval(0, 1),
            "terms": (),
            "offset": sp.S.One,
            "frequency_polynomial": sp.S.One,
            "image": sp.Interval(-2, 2),
        }
    else:
        r = fp.bound_range_tail(sp.sin(x) / x, x, sp.Interval.open(8, sp.oo))
        changes = {
            "expression": r.expression + 1,
            "variable": z,
            "domain": sp.Interval.open(9, sp.oo),
            "limit": sp.S.One,
            "lower": sp.S.Zero,
            "upper": sp.S.Zero,
        }
    assert set(changes) == {f.name for f in fields(r)} - {"certified"}
    assert r.verify()
    for name, value in changes.items():
        assert not replace(r, **{name: value}).verify(), name


def test_convex_witness_payload():
    a = sp.Symbol("a", real=True)
    proof = fp.parameter_root_coverage(sp.exp(x) - 1 - x - a, x, a, sp.Interval(-1, 1))
    cell = next(c for c in proof.cells if c.region == sp.FiniteSet(0))
    w = cell.witness
    changes = {
        "base": w.base + 1,
        "center": sp.Rational(1, 2),
        "minimum": sp.S.One,
        "left_value": sp.S.Zero,
        "right_value": sp.S.Zero,
        "curvature": replace(w.curvature, lower=sp.S(2)),
    }
    assert set(changes) == {f.name for f in fields(w)}
    for name, value in changes.items():
        bad = replace(cell, witness=replace(w, **{name: value}))
        assert not replace(
            proof, cells=tuple(bad if c is cell else c for c in proof.cells)
        ).verify(), name
