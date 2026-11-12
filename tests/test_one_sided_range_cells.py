"""Open source cells retain finite limits, infinite limits and owned seams."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


@pytest.mark.parametrize(
    "f,D,image",
    [
        (x * sp.log(x), sp.Interval(0, 1), sp.Interval(-1 / sp.E, 0)),
        (sp.sqrt(x) + sp.exp(x), sp.Interval(0, 1), sp.Interval(1, 1 + sp.E)),
        (sp.log(x) + 1 / x, sp.Interval.open(0, 1), sp.Interval.open(1, sp.oo)),
        (sp.Abs(x) + sp.exp(x), sp.Interval(-1, 1), sp.Interval(1, 1 + sp.E)),
    ],
)
def test_boundary_images(f, D, image):
    r = fp.analyze_range(f, x, D, certified=True)
    assert r.image == image and r.complete and r.verify() and r.certified


def test_limit_ownership():
    r = fp.analyze_range(x * sp.log(x), x, sp.Interval(0, 1))
    assert r.domain_record.effective == sp.Interval.Lopen(0, 1)
    assert r.cells[0].sites[0].value == 0 and not r.cells[0].sites[0].attained
    assert r.cells[0].sites[1].value == 0 and r.cells[0].sites[1].attained
    cell = r.cells[0]
    assert not replace(
        cell, sites=(replace(cell.sites[0], value=1), *cell.sites[1:])
    ).verify()
    assert not replace(cell.critical_cover, roots=()).verify()


def test_owned_spike():
    f = sp.Piecewise((sp.Abs(x) + sp.exp(x), sp.Ne(x, 0)), (10, True))
    r = fp.analyze_range(f, x, sp.Interval(-1, 1))
    assert r.image == sp.Union(sp.Interval.Lopen(1, 1 + sp.E), sp.FiniteSet(10))
    assert r.verify()
