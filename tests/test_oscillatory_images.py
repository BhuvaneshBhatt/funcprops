"""Exact phase sequences prove surjective without stationary-root searches."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    "f",
    [
        x * sp.sin(x),
        -x * x * sp.cos(2 * x + 1) + 3,
        (x**3 - x) * sp.sin(-x + sp.pi / 4),
    ],
)
@pytest.mark.parametrize(
    "domain", [sp.S.Reals, sp.Interval.open(2, sp.oo), sp.Interval(-sp.oo, -1)]
)
def test_escape(f, domain):
    r = fp.analyze_range(f, x, domain, policy=fp.EnclosurePolicy(max_cells=0))
    assert r.image is sp.S.Reals and r.verify()
    assert not replace(r, transfer=replace(r.transfer, amplitude=sp.S.One)).verify()
    assert not replace(
        r, transfer=replace(r.transfer, sequences=r.transfer.sequences[:1])
    ).verify()


def test_escape_scope():
    r = fp.analyze_range(
        x * sp.sin(x), x, sp.Interval(0, 1), policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert r.image is not sp.S.Reals
    assert fp.range(x * sp.sin(x), x, y) is sp.true
