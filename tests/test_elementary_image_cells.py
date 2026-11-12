import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.image_rules import exact_image

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    "head,source,expected",
    [
        (sp.asinh, sp.S.Reals - sp.FiniteSet(0), sp.S.Reals - sp.FiniteSet(0)),
        (sp.asin, sp.Interval.open(-2, 2), sp.Interval(-sp.pi / 2, sp.pi / 2)),
        (sp.acos, sp.Interval.Ropen(-1, 1), sp.Interval.Lopen(0, sp.pi)),
        (sp.acosh, sp.Interval.open(0, 2), sp.Interval.Ropen(0, sp.acosh(2))),
        (sp.atanh, sp.Interval(-2, 2), sp.S.Reals),
        (
            sp.erf,
            sp.S.Reals - sp.FiniteSet(0),
            sp.Interval.open(-1, 1) - sp.FiniteSet(0),
        ),
        (sp.erfc, sp.Interval.open(-sp.oo, 0), sp.Interval.open(1, 2)),
        (sp.Abs, sp.Interval.open(-1, 1), sp.Interval.Ropen(0, 1)),
        (sp.cosh, sp.Interval.open(-1, 1), sp.Interval.Ropen(1, sp.cosh(1))),
        (sp.sech, sp.S.Reals - sp.FiniteSet(0), sp.Interval.open(0, 1)),
        (sp.tan, sp.Interval.open(0, sp.pi), sp.S.Reals - sp.FiniteSet(0)),
        (sp.cot, sp.Interval.open(0, sp.pi), sp.S.Reals),
    ],
)
def test_elementary_images(head, source, expected):
    assert exact_image(head(x), x, source) == expected


@pytest.mark.parametrize(
    "head,expected",
    [
        (sp.asinh, sp.S.Reals - sp.FiniteSet(0)),
        (sp.erf, sp.Interval.open(-1, 1) - sp.FiniteSet(0)),
        (sp.acos, sp.Interval(0, sp.pi) - sp.FiniteSet(sp.pi / 2)),
        (sp.acosh, sp.Interval(0, sp.oo)),
    ],
)
def test_composed_holes(head, expected):
    assert fp.condition_to_real_set(fp.range(head(1 / x), x, y), y) == expected


def test_nonreal_points():
    assert exact_image(sp.atan(x), x, sp.FiniteSet(sp.oo, sp.I, 0)) == sp.FiniteSet(0)
