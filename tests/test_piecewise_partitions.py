"""Owned cells and seams in reusable Piecewise monotonic partitions."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.monotonic_certificates import matching_partition

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    "left_open,right_open", [(False, False), (True, False), (False, True), (True, True)]
)
def test_jump_images(left_open, right_open):
    expression = sp.Piecewise((x, x < 0), (x + 2, True))
    support = sp.Interval(-1, 1, left_open, right_open)
    p = fp.monotonic_partition(expression, x, domain=support, return_result=True)
    assert (
        p.complete and p.same_strict_direction() is fp.Monotonicity.STRICTLY_INCREASING
    )
    expected = sp.Union(
        sp.Interval(-1, 0, left_open, True), sp.Interval(2, 3, False, right_open)
    )
    assert fp.range_from_monotonic_partition(expression, x, p).image == expected
    assert fp.injectivity_from_partition(p) is fp.TruthValue.TRUE
    assert matching_partition(p, expression, x, support) is p
    assert fp.verify_certificate(p, expr=expression, var=x)


@pytest.mark.parametrize("point", [-1, 0, 1])
def test_owned_spikes(point):
    expression = sp.Piecewise((100, sp.Eq(x, point)), (x, True))
    p = fp.monotonic_partition(
        expression, x, domain=sp.Interval(-1, 1), return_result=True
    )
    assert p.complete
    expected = fp.Monotonicity.STRICTLY_INCREASING if point == 1 else None
    assert p.same_strict_direction() is expected
    assert p.direction_changes == {-1: 1, 0: 2, 1: 0}[point]
    image = fp.range_from_monotonic_partition(expression, x, p).image
    assert image == sp.Union(
        sp.Interval(-1, 1) - sp.FiniteSet(point), sp.FiniteSet(100)
    )


def test_constant_branches():
    expression = sp.Piecewise((0, x < 0), (1, True))
    p = fp.monotonic_partition(
        expression, x, domain=sp.Interval(-1, 1), return_result=True
    )
    assert p.complete and fp.range_from_monotonic_partition(
        expression, x, p
    ).image == sp.FiniteSet(0, 1)
    assert fp.injectivity_from_partition(p) is fp.TruthValue.FALSE


def test_nested_and_stationary_cells():
    expression = x**2 + sp.Piecewise((10, x < 0), (0, True))
    p = fp.monotonic_partition(
        expression, x, domain=sp.Interval(-1, 1), return_result=True
    )
    assert p.complete and len(p.cells) == 2 and len(p.seams) == 1
    assert fp.range_from_monotonic_partition(expression, x, p).image == sp.Union(
        sp.Interval(0, 1), sp.Interval.Lopen(10, 11)
    )


@pytest.mark.parametrize(
    "field,value",
    [("points", ()), ("seams", ()), ("branch_partitions", ()), ("expression", x)],
)
def test_partition_mutation(field, value):
    expression = sp.Piecewise((x, x < 0), (x + 2, True))
    p = fp.monotonic_partition(
        expression, x, domain=sp.Interval(-1, 1), return_result=True
    )
    altered = replace(p, **{field: value})
    assert matching_partition(altered, expression, x, p.domain) is None
    assert not fp.verify_certificate(altered, expr=expression, var=x)


def test_source_holes_decline():
    held = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    expression = sp.Piecewise((held, x < 1), (x, True), evaluate=False)
    p = fp.monotonic_partition(
        expression, x, domain=sp.Interval(-1, 2), return_result=True
    )
    assert not p.complete
    incomplete = sp.Piecewise((x, x < 0))
    assert not fp.monotonic_partition(
        incomplete, x, domain=sp.Interval(-1, 1), return_result=True
    ).complete


def test_equal_owned_gap_values():
    expression = sp.Piecewise((x, x <= 0), (x - 1, True))
    support = sp.Union(sp.Interval(-1, 0), sp.Interval(1, 2))
    p = fp.monotonic_partition(expression, x, domain=support, return_result=True)
    assert p.complete and p.same_strict_direction() is None
    assert expression.subs(x, 0) == expression.subs(x, 1) == 0
