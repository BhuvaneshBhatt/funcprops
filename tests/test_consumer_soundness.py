"""Source-bound partitions and domain/seam premises for real-property rules."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.common import condition_to_set
from funcprops.real_analysis.monotonic_certificates import matching_partition
from funcprops.singularities.regularity import _condition_intersects_domain

x, y = sp.symbols("x y", real=True)
D = sp.Interval(-2, 2)


@pytest.fixture
def linear_partition():
    return fp.monotonic_partition(x, x, domain=D, return_result=True)


def test_foreign_range(linear_partition):
    result = fp.range(sp.sin(x), x, y, domain=D, partition=linear_partition)
    assert condition_to_set(result, y) == sp.Interval(-1, 1)
    direct = fp.range_from_monotonic_partition(sp.sin(x), x, linear_partition, domain=D)
    assert not direct.complete and direct.image is None


def test_foreign_monotonicity(linear_partition):
    result = fp.monotonicity(
        sp.sin(x), x, domain=D, partition=linear_partition, return_result=True
    )
    assert result.primary is fp.Monotonicity.NOT_MONOTONE


def test_foreign_extrema(linear_partition):
    result = fp.symbolic_extremum_range(x**2, x, D, partition=linear_partition)
    assert result.complete
    assert (result.lower, result.upper) == (0, 4)
    assert result.lower_attained is True and result.upper_attained is True


def test_foreign_oscillation(linear_partition):
    assert (
        fp.oscillation(x**2, x, domain=D, partition=linear_partition)
        is fp.Oscillation.FINITELY_OSCILLATORY
    )


def test_inverse_domain(linear_partition):
    result = fp.certified_monotonic_inverse(
        x**2, x, 1, domain=sp.Interval(0, 2), partition=linear_partition
    )
    assert result.complete and result.solutions == sp.FiniteSet(1)
    assert result.domain == sp.Interval(0, 2)


@pytest.mark.parametrize(
    "field,value",
    [
        ("expression", -x),
        ("variable", y),
        ("domain", sp.Interval(-1, 1)),
        ("derivative", sp.S.Zero),
        ("cells", ()),
        ("complete", 1),
        ("critical_points_complete", 1),
    ],
)
def test_partition_mutations(linear_partition, field, value):
    altered = replace(linear_partition, **{field: value})
    assert matching_partition(altered, x, x, D) is None
    result = fp.range(x, x, y, domain=D, partition=altered)
    assert condition_to_set(result, y) == D
    assert not fp.verify_certificate(altered, expr=x, var=x)


def test_endpoint_mutation(linear_partition):
    cell = replace(linear_partition.cells[0], right_limit=sp.Integer(99))
    altered = replace(linear_partition, cells=(cell,))
    assert matching_partition(altered, x, x, D) is None
    result = fp.range_from_monotonic_partition(x, x, altered, domain=D)
    assert result.complete and result.image == D


@pytest.mark.parametrize("compact", [False, True])
def test_valid_partition_reuse(linear_partition, compact):
    partition = fp.monotonic_partition(x, x, domain=D) if compact else linear_partition
    assert matching_partition(partition, x, x, D) is linear_partition
    result = fp.range_from_monotonic_partition(x, x, partition)
    assert result.complete and result.image == D
    assert result.partition is linear_partition


@pytest.mark.parametrize("shift", [0, 1, -1])
@pytest.mark.parametrize("scale", [1, -1])
def test_nested_jumps(shift, scale):
    step = sp.Piecewise((10, x < shift), (0, True))
    expression = scale * (x - shift + step)
    support = sp.Interval(shift - 1, shift + 1)
    assert fp.convexity(expression, x, domain=support) is fp.Convexity.NEITHER
    assert (
        fp.monotonicity(expression, x, domain=support) is fp.Monotonicity.NOT_MONOTONE
    )
    assert fp.variation(expression, x, domain=support) == 12
    partition = fp.monotonic_partition(
        expression, x, domain=support, return_result=True
    )
    assert partition.complete and not partition.critical_points_complete
    assert len(partition.seams) == 1 and partition.direction_changes == 2


def test_transcendental_jump_variation():
    expression = sp.exp(x) + sp.Piecewise((10, x < 0), (0, True))
    result = fp.variation(expression, x, domain=sp.Interval(-1, 1), return_result=True)
    assert result.bounded_variation is fp.TruthValue.TRUE
    assert sp.simplify(result.total_variation - (10 + 2 * sp.sinh(1))) == 0


@pytest.mark.parametrize("variables", [x, (x, y)])
def test_slope_seams(variables):
    expression = x**2 + sp.Piecewise((-x, x < 0), (-2 * x, True))
    if isinstance(variables, tuple):
        expression += y**2
    result = fp.convexity(expression, variables)
    assert result in (fp.Convexity.UNKNOWN, fp.Convexity.NEITHER)
    # At y=0 these three values violate the midpoint convexity inequality.
    assert (
        expression.subs({x: 0, y: 0})
        > (
            expression.subs({x: -sp.Rational(1, 8), y: 0})
            + expression.subs({x: sp.Rational(1, 8), y: 0})
        )
        / 2
    )


def test_multivariate_jump():
    expression = x**2 + y**2 + sp.Piecewise((10, x < 0), (0, True))
    assert fp.convexity(expression, (x, y)) is fp.Convexity.UNKNOWN
    positive = sp.Piecewise((-x, x < 0), (2 * x, True)) + y**2
    assert fp.convexity(positive, (x, y)) is fp.Convexity.CONVEX


@pytest.mark.parametrize("entire", [False, True])
def test_multivariate_source_holes(entire):
    if entire:
        expression = sp.Mul(
            x,
            sp.Pow(x, -1, evaluate=False),
            sp.exp(x) + sp.exp(-x) + y**2,
            evaluate=False,
        )
    else:
        expression = sp.Add(
            x**2,
            y**2,
            sp.Mul(0, sp.Pow(x + y, -1, evaluate=False), evaluate=False),
            evaluate=False,
        )
    assert fp.convexity(expression, (x, y)) is fp.Convexity.UNKNOWN
    assert fp.convexity(x**2 + y**2, (x, y)) is fp.Convexity.STRONGLY_CONVEX


@pytest.mark.parametrize(
    "support,expected",
    [
        (sp.Interval(-1, 1), True),
        (sp.Interval.open(0, 1), False),
        (sp.FiniteSet(0, 2), True),
        (sp.Union(sp.Interval(-2, -1), sp.Interval(0, 1)), True),
    ],
)
def test_membership_intersection(support, expected):
    assert (
        _condition_intersects_domain(sp.Eq(x, 0), sp.Contains(x, support)) is expected
    )


@pytest.mark.parametrize("expression", [sp.Abs(x), sp.sqrt(sp.Abs(x)), sp.sign(x)])
def test_membership_regularity(expression):
    support = sp.Contains(x, sp.Interval(-1, 1))
    assert fp.analytic(expression, x, domain=support) is not fp.Analyticity.ANALYTIC
    result = fp.smoothness(
        expression, x, domain=support, max_order=1, return_result=True
    )
    assert result.smooth is not True
    assert result.differentiability_order != sp.oo


@pytest.mark.parametrize("support", [sp.Interval(1, 2), sp.Interval(-2, -1)])
def test_off_cusp_regularity(support):
    assert (
        fp.analytic(sp.Abs(x), x, domain=sp.Contains(x, support))
        is fp.Analyticity.ANALYTIC
    )


@pytest.mark.parametrize("mode", ["conditions", "union", "records"])
def test_restricted_branch_cut(mode):
    expression = fp.ConditionalExpression(sp.log(x), x < 1)
    result = fp.branch_cuts(expression, x, mode=mode)
    if mode == "records":
        condition = sp.Or(*(record.condition for record in result))
    elif mode == "conditions":
        condition = sp.Or(*result)
    else:
        condition = result
    assert condition_to_set(condition, x) == sp.Interval.open(-sp.oo, 0)


@pytest.mark.parametrize("expression", [1 / x, sp.tan(x), 1 / x**2])
def test_extrema_definition_premise(expression):
    support = sp.Interval(-2, 2)
    assert fp.symbolic_extremum_range(expression, x, support) is None


def test_valid_extrema():
    support = sp.Interval(1, 2)
    result = fp.symbolic_extremum_range(1 / x, x, support)
    assert result.complete and (result.lower, result.upper) == (sp.Rational(1, 2), 1)
    assert result.lower_attained is True and result.upper_attained is True


def test_guard_holes_in_variation():
    expression = sp.Piecewise((x, sp.log(x) > 0), (0, True))
    result = fp.variation(expression, x, domain=sp.Interval(-1, 2), return_result=True)
    assert result.total_variation is None
    assert result.bounded_variation is fp.TruthValue.UNKNOWN
