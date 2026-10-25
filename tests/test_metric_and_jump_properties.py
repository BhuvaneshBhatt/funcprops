"""Finite metric bounds, jumps, local rewrites and absolute homogeneity."""

import pytest
import sympy as sp

import funcprops as fp
from funcprops import Convexity, Homogeneity, TruthValue
from funcprops.real_analysis.restricted_simplify import simplify_on_domain

x, y, a = sp.symbols("x y a", real=True)


@pytest.mark.parametrize(
    "expr,points,constant",
    [
        (x * x, sp.FiniteSet(0, 1, 2), 3),
        (x * x, sp.FiniteSet(-1, 1), 0),
        (a * x, sp.FiniteSet(0, 2), sp.Abs(a)),
        (x, sp.FiniteSet(3), 0),
        (x, sp.S.EmptySet, 0),
        (1 / x, sp.FiniteSet(0, 1, 2), sp.Rational(1, 2)),
        (sp.Piecewise((0, x < 0), (1, True)), sp.FiniteSet(-1, 1), sp.Rational(1, 2)),
    ],
)
def test_finite_exact_optimal_lipschitz(expr, points, constant):
    result = fp.lipschitz(expr, x, domain=points, return_result=True)
    assert result.value is TruthValue.TRUE
    assert result.optimal is TruthValue.TRUE
    assert result.constant == constant
    boolean = sp.Or(*(sp.Eq(x, p) for p in points))
    assert fp.lipschitz(expr, x, domain=boolean) == constant


def test_finite_parameter_point_collisions_decline():
    b = sp.Symbol("b", real=True)
    assert (
        fp.lipschitz(x * x, x, domain=sp.FiniteSet(a, b), return_result=True).value
        is TruthValue.UNKNOWN
    )


def test_finite_metric_consumers_override_continuity_at_ambient_seams():
    e = sp.Piecewise((0, x < 0), (1, True))
    assert fp.uniformly_continuous(e, x, domain=sp.FiniteSet(0, 1)) is TruthValue.TRUE
    assert fp.holder_regularity(sp.sqrt(x), x, domain=sp.FiniteSet(0, 1)) == 1


@pytest.mark.parametrize(
    "expr,support,total",
    [
        (sp.Piecewise((0, x < 0), (1, x < 1), (0, True)), sp.Interval(-1, 2), 2),
        (sp.Piecewise((10, sp.Eq(x, 0)), (0, True)), sp.Interval(-1, 1), 20),
        (sp.Piecewise((10, sp.Eq(x, 0)), (0, True)), sp.Interval(0, 1), 10),
        (sp.Piecewise((10, sp.Eq(x, 0)), (0, True)), sp.Interval.open(0, 1), 0),
        (sp.Piecewise((x * x, x < 0), (x * x + 3, True)), sp.Interval(-1, 1), 5),
        (sp.Piecewise((x * x, x < 0), (x * x + 3, True)), sp.Interval.open(-1, 1), 5),
        (sp.Piecewise((0, x < 0), (a, True)), sp.Interval(-1, 1), sp.Abs(a)),
    ],
)
def test_piecewise_variation_counts_jumps_points_and_branch_motion(
    expr, support, total
):
    result = fp.variation(expr, x, domain=support, return_result=True)
    assert result.bounded_variation is TruthValue.TRUE
    assert result.total_variation == total


def test_missing_piecewise_coverage_does_not_invent_variation():
    result = fp.variation(
        sp.Piecewise((x, x < 0)), x, domain=sp.Interval(-1, 1), return_result=True
    )
    assert result.bounded_variation is not TruthValue.TRUE


def test_infinite_variation_is_not_bounded():
    result = fp.variation(1 / x, x, domain=sp.Interval.open(0, 1), return_result=True)
    assert result.total_variation is sp.oo
    assert result.bounded_variation is TruthValue.FALSE


@pytest.mark.parametrize(
    "expr,support,replacement",
    [
        (sp.Abs(x), sp.Interval(0, 2), x),
        (sp.Abs(x), sp.Interval(-2, 0), -x),
        (sp.Min(x, 2), sp.Interval(-2, 1), x),
        (sp.Max(0, x), sp.Interval(2, 3), x),
        (sp.Piecewise((x, x < 0), (x * x, True)), sp.Interval(1, 2), x * x),
        (sp.exp(sp.Max(0, x)), sp.Interval(2, 3), sp.exp(x)),
    ],
)
def test_local_rewrites_are_proved_on_whole_support(expr, support, replacement):
    actual, _restriction = simplify_on_domain(expr, x, support)
    assert actual == replacement
    assert fp.range(expr, x, y, domain=support) == fp.range(
        replacement, x, y, domain=support
    )


def test_no_rewrite_across_sign_or_piecewise_seam():
    e = sp.Abs(x)
    assert simplify_on_domain(e, x, sp.Interval(-1, 1))[0] == e
    e = sp.Piecewise((x, x < 0), (x * x, True))
    assert simplify_on_domain(e, x, sp.Interval(-1, 1))[0] == e


def test_restricted_convexity_gain():
    assert (
        fp.convexity(sp.exp(sp.Max(0, x)), x, domain=sp.Interval(2, 3))
        is Convexity.STRONGLY_CONVEX
    )


def test_rewrite_keeps_original_pole_exclusion():
    expr = (sp.Abs(x) - x) / (x - 1)
    rewritten, restriction = simplify_on_domain(expr, x, sp.Interval(0, 2))
    assert rewritten == 0
    assert restriction.subs(x, 1) is sp.S.false
    assert fp.range(expr, x, y, domain=sp.FiniteSet(1)) is sp.S.false
    assert fp.range(expr, x, y, domain=sp.Interval(0, 2)) == sp.Eq(y, 0)


@pytest.mark.parametrize(
    "support,expected",
    [
        (sp.Interval(0, 1), sp.Interval(1, sp.E)),
        (sp.Interval.open(0, 1), sp.Interval.open(1, sp.E)),
        (sp.Interval(0, sp.oo), sp.Interval(1, sp.oo)),
        (sp.FiniteSet(0, 1), sp.FiniteSet(1, sp.E)),
    ],
)
def test_range_domain_keyword_is_respected(support, expected):
    condition = fp.range(sp.exp(x), x, y, domain=support)
    for value in (0, 1, 2, sp.E, 4):
        assert sp.simplify(condition.subs(y, value)) == expected.contains(value)


def test_range_domain_and_constraints_intersect():
    assert fp.range(
        x, x, y, domain=sp.Interval(0, 2), constraints=sp.Interval(1, 3)
    ) == ((y >= 1) & (y <= 2))
    assert fp.range(x, x, y, domain=sp.Interval(0, 1), constraints=x > 2) is sp.S.false


@pytest.mark.parametrize(
    "expr,variables,weights,degree",
    [
        (sp.Abs(x), x, None, 1),
        (sp.Abs(x * y), (x, y), None, 2),
        (sp.Abs(x) + sp.Abs(y), (x, y), None, 1),
        (sp.Abs(x) + sp.Abs(y) ** 2, (x, y), (2, 1), 2),
        (sp.Abs(a * x), x, None, 1),
        (sp.Abs(x * x + y * y), (x, y), None, 2),
    ],
)
def test_basic_abs_positive_scaling_homogeneity(expr, variables, weights, degree):
    result = fp.homogeneity(expr, variables, weights=weights, return_result=True)
    assert result.classification is Homogeneity.HOMOGENEOUS
    assert result.degree == degree
    assert fp.verify_certificate(result, expr=expr)


@pytest.mark.parametrize(
    "assumptions,expected",
    [
        (sp.S.true, Homogeneity.UNKNOWN),
        (sp.Eq(a, 0), Homogeneity.HOMOGENEOUS),
        (sp.Ne(a, 0), Homogeneity.NOT_HOMOGENEOUS),
    ],
)
def test_abs_requested_degree_retains_zero_coefficient_case(assumptions, expected):
    result = fp.homogeneity(
        sp.Abs(a * x), x, degree=2, assumptions=assumptions, return_result=True
    )
    assert result.classification is expected
    if expected is not Homogeneity.UNKNOWN:
        assert fp.verify_certificate(result, expr=sp.Abs(a * x))


def test_isolated_cusp_does_not_prove_optimal_holder_exponent():
    d = sp.Union(sp.FiniteSet(0), sp.Interval(1, 2))
    r = fp.holder_regularity(sp.sqrt(x), x, domain=d, return_result=True)
    assert r.exponent != sp.Rational(1, 2) or r.optimal is not TruthValue.TRUE
    r = fp.holder_regularity(
        sp.sqrt(x), x, domain=sp.Interval(-1, 0), return_result=True
    )
    assert r.exponent != sp.Rational(1, 2) or r.optimal is not TruthValue.TRUE
    assert fp.holder_regularity(
        sp.Abs(x) ** sp.Rational(1, 2), x, domain=sp.Interval(-1, 0)
    ) == sp.Rational(1, 2)


def test_finite_real_outputs_with_complex_intermediates():
    result = fp.lipschitz(
        sp.exp(sp.I * sp.pi * x), x, domain=sp.FiniteSet(0, 1), return_result=True
    )
    assert result.constant == 2 and result.optimal is TruthValue.TRUE


def test_metric_and_variation_consumers_use_restricted_simplification():
    assert fp.lipschitz(sp.Max(0, x), x, domain=sp.Interval(2, 3)) == 1
    assert fp.variation(sp.Max(0, x), x, domain=sp.Interval(2, 3)) == 1


def test_cusp_optimality_on_open_and_unbounded_domains():
    for support in (sp.Interval.open(0, 1), sp.Interval(0, sp.oo), sp.S.Reals):
        assert fp.holder_regularity(sp.sqrt(x), x, domain=support) == sp.Rational(1, 2)
