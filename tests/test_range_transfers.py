"""Elementary images, finite-period reductions and proved unbounded tails."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_images.transfers import PeriodicImage, TailImage

x = sp.Symbol("x", real=True)


@pytest.mark.parametrize(
    "expression,expected",
    [
        (sp.sin(x), sp.Interval(-1, 1)),
        (sp.sin(x) + sp.cos(2 * x), sp.Interval(-2, sp.Rational(9, 8))),
        (sp.exp(sp.sin(x)), sp.Interval(sp.exp(-1), sp.E)),
        (sp.erf(x), sp.Interval.open(-1, 1)),
    ],
)
def test_unbounded_images(expression, expected):
    r = fp.analyze_range(expression, x, certified=True)
    assert r.image == expected and r.complete and r.verify() and r.certified


def test_period_window():
    # The finite root cover is insufficient at this budget. The transfer still
    # preserves honest inner and outer information over a full source period.
    f = sp.sin(x) + sp.sin(2 * x)
    r = fp.analyze_range(
        f, x, sp.Interval.open(0, sp.oo), policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert isinstance(r.transfer, PeriodicImage) and r.verify()
    assert r.transfer.window.measure >= r.transfer.period
    assert not r.complete and r.inner is sp.S.EmptySet and r.outer is sp.S.Reals
    for bad in (
        replace(r, transfer=replace(r.transfer, period=sp.pi)),
        replace(r, transfer=replace(r.transfer, window=sp.Interval(-7, 0))),
        replace(r, expression=f + x),
    ):
        assert not bad.verify()


def test_proved_tails():
    f = x * x + sp.exp(x)
    r = fp.analyze_range(f, x, certified=True)
    assert (
        isinstance(r.transfer, TailImage) and r.complete and r.verify() and r.certified
    )
    assert isinstance(r.image.start, fp.CriticalValue) and r.image.end is sp.oo
    assert not r.image.left_open and r.image.right_open
    assert len(r.transfer.tails) == 2
    for tail in r.transfer.tails:
        assert tail.verify() and fp.verify_certificate(tail, expr=f, var=x)
        assert not replace(tail, limit=0).verify()
        assert not replace(tail, image=sp.S.Reals).verify()
    assert not replace(
        r, transfer=replace(r.transfer, tails=r.transfer.tails[:1])
    ).verify()


def test_halfline_tail():
    r = fp.analyze_range(x * x + sp.exp(x), x, sp.Interval.open(0, sp.oo))
    assert r.image == sp.Interval.open(1, sp.oo) and r.verify()


def test_source_hole():
    # A held removable singularity still removes a unique minimum value.
    held = sp.Mul(
        sp.exp(x * x),
        sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False),
        evaluate=False,
    )
    r = fp.analyze_range(
        held, x, sp.Interval(-1, 1), policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert r.domain_record.effective == sp.Union(
        sp.Interval.Ropen(-1, 0), sp.Interval.Lopen(0, 1)
    )
    assert r.verify() and r.image == sp.Interval.Lopen(1, sp.E)
    assert r.image.contains(1) is sp.false


def test_oscillatory_escape():
    r = fp.analyze_range(x * sp.sin(x), x, policy=fp.EnclosurePolicy(max_cells=0))
    assert r.complete and r.image is sp.S.Reals and r.verify()
