"""Dense closures do not determine exact endpoint attainment."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_images.trigonometric import dense_trig_data

x = sp.Symbol("x", real=True)
a, b = sp.sin(x), sp.sin(sp.sqrt(2) * x)


@pytest.mark.parametrize(
    "f,image",
    [
        (a + b, sp.Interval.open(-2, 2)),
        (a * a + b * b, sp.Interval.Ropen(0, 2)),
        (2 - a * a - b * b, sp.Interval.Lopen(0, 2)),
        (sp.cos(x) + sp.cos(sp.sqrt(2) * x), sp.Interval.Lopen(-2, 2)),
    ],
)
def test_dense_images(f, image):
    r = fp.analyze_range(f, x, policy=fp.EnclosurePolicy(max_cells=0))
    assert r.image == image and r.verify()
    assert not replace(
        r,
        transfer=replace(
            r.transfer, frequency_polynomial=sp.Symbol("frequency_ratio") - 2
        ),
    ).verify()


def test_removed_common_phase():
    r = fp.analyze_range(a * a + b * b, x, sp.S.Reals - sp.FiniteSet(0))
    assert r.image == sp.Interval.open(0, 2) and r.verify()
    r = fp.analyze_range(a * a + b * b, x, sp.Interval.open(0, sp.oo))
    assert r.image == sp.Interval.open(0, 2) and r.verify()


def test_commensurate_decline():
    assert dense_trig_data(sp.sin(x) + sp.sin(2 * x), x, sp.S.Reals) is None


def test_dense_dispatch():
    y = sp.Symbol("y", real=True)
    condition = fp.range(a + b, x, y)
    assert condition.subs(y, 0) is sp.true and condition.subs(y, 2) is sp.false
