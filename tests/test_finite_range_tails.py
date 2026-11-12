"""Finite asymptotic enclosures preserve source holes and exact endpoint ownership."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
f = sp.sin(x) / x


def test_finite_tail_bound():
    tail = fp.bound_range_tail(f, x, sp.Interval.open(8, sp.oo))
    assert isinstance(tail, fp.FiniteTailBound)
    assert (tail.limit, tail.lower, tail.upper) == (
        0,
        -sp.Rational(1, 8),
        sp.Rational(1, 8),
    )
    assert (
        tail.verify()
        and fp.verify_certificate(tail, expr=f, var=x)
        and not tail.certified
    )
    assert not replace(tail, lower=0).verify()
    assert fp.bound_range_tail(f, x, sp.Interval.open(8, sp.oo), limit=1) is None


@pytest.fixture(scope="module")
def sinc_image():
    return fp.analyze_range(
        f, x, policy=fp.EnclosurePolicy(max_cells=256, max_depth=10, precision=20)
    )


def test_sinc_image(sinc_image):
    r = sinc_image
    assert r.complete and r.verify() and r.image.end == 1 and r.image.right_open
    assert r.domain_record.effective == sp.S.Reals - sp.FiniteSet(0)
    assert isinstance(r.image.start, fp.CriticalValue) and not r.image.left_open
    bound = r.image.start.enclosure(12)
    assert -sp.Rational(218, 1000) < bound.lower < bound.upper < -sp.Rational(217, 1000)
    assert r.image.contains(0) is sp.true and r.image.contains(1) is sp.false
    core = r.transfer.analysis.transfer.core
    cell = core.cells[0]
    assert isinstance(cell.critical_cover, fp.InteriorRootCover)
    bad = replace(cell.critical_cover, denominator=x)
    assert not bad.verify()


def test_finite_tail_scope():
    assert fp.bound_range_tail(sp.sin(x), x, sp.Interval.open(1, sp.oo)) is None
    assert fp.bound_range_tail(f, x, sp.Interval(0, sp.oo)) is None
