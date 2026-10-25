"""Exact real images under restricted transcendental substitutions."""

import pytest
import sympy as sp

from funcprops import range as function_range
from funcprops.real_analysis.common import condition_to_set
from funcprops.transcendental.algebraize import algebraize

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        (sp.Interval(0, 1), sp.Interval(1, sp.E)),
        (sp.Interval.open(0, 1), sp.Interval.open(1, sp.E)),
        (sp.Interval.Ropen(0, 1), sp.Interval.Ropen(1, sp.E)),
        (sp.Interval.Lopen(0, 1), sp.Interval.Lopen(1, sp.E)),
        (sp.Interval(0, sp.oo), sp.Interval(1, sp.oo)),
        (sp.Interval.open(-sp.oo, 0), sp.Interval.open(0, 1)),
        (
            sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2)),
            sp.Union(
                sp.Interval(sp.exp(-2), sp.exp(-1)),
                sp.Interval(sp.E, sp.exp(2)),
            ),
        ),
        (sp.FiniteSet(0, 1), sp.FiniteSet(1, sp.E)),
        (sp.S.EmptySet, sp.S.EmptySet),
    ],
)
def test_exponential_restricted_range(domain, expected):
    result = function_range(sp.exp(x), x, y, constraints=domain)
    assert condition_to_set(result, y) == expected


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        (sp.Interval(0, 1), sp.Interval(-sp.Rational(1, 4), sp.E**2 - 3 * sp.E + 2)),
        (
            sp.Interval.open(0, 1),
            sp.Interval.Ropen(-sp.Rational(1, 4), sp.E**2 - 3 * sp.E + 2),
        ),
        (sp.Interval(0, sp.oo), sp.Interval(-sp.Rational(1, 4), sp.oo)),
    ],
)
def test_polynomial_in_exponentials(domain, expected):
    expr = sp.exp(2 * x) - 3 * sp.exp(x) + 2
    result = function_range(expr, x, y, constraints=domain)
    assert condition_to_set(result, y) == expected


def test_boolean_interval_constraints_are_preserved():
    cond = (x >= 0) & (x <= 1)
    assert condition_to_set(
        function_range(sp.exp(x), x, y, constraints=cond), y
    ) == sp.Interval(1, sp.E)


def test_negative_exponent_reverses_output_endpoints():
    result = function_range(sp.exp(-x), x, y, constraints=sp.Interval(0, 1))
    assert condition_to_set(result, y) == sp.Interval(sp.exp(-1), 1)


def test_transformed_auxiliary_domain_carries_input_restriction():
    domain = sp.Interval.open(0, 1)
    transformed = algebraize(sp.exp(2 * x) - 3 * sp.exp(x) + 2, x, domain=domain)
    assert transformed.changed and transformed.exact
    u, generator = transformed.substitutions[0]
    assert generator == sp.exp(x)
    assert condition_to_set(transformed.constraints, u) == sp.Interval.open(1, sp.E)
    assert transformed.source_domain == domain


def test_integer_domain_is_not_broadened_to_positive_reals():
    result = function_range(sp.exp(x), x, y, constraints=sp.S.Integers)
    assert result != (y > 0)


def test_nonreal_inputs_are_excluded_from_real_range():
    result = function_range(sp.exp(x), x, y, constraints=sp.FiniteSet(sp.I))
    assert result is sp.S.false


def test_affine_exponential_restriction():
    result = function_range(sp.exp(3 * x + 2), x, y, constraints=sp.Interval(0, 1))
    assert condition_to_set(result, y) == sp.Interval(sp.exp(2), sp.exp(5))


def test_hyperbolic_half_infinite_restriction():
    result = function_range(sp.tanh(x), x, y, constraints=sp.Interval(0, sp.oo))
    assert condition_to_set(result, y) == sp.Interval.Ropen(0, 1)


def test_pole_excluded_by_natural_domain():
    result = function_range(1 / (sp.exp(x) - 1), x, y, constraints=sp.Interval(0, 1))
    expected = sp.Interval(1 / (sp.E - 1), sp.oo)
    assert condition_to_set(result, y) == expected


def test_unmappable_domains_decline_exact_algebraization():
    noninterval = sp.ConditionSet(x, sp.sin(x) > 0, sp.S.Reals)
    transformed = algebraize(sp.exp(x), x, domain=noninterval)
    assert not transformed.changed
    assert transformed.expression == sp.exp(x)


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        (sp.Interval(1, sp.E), sp.Interval(0, 1)),
        (sp.Interval.open(1, sp.E), sp.Interval.open(0, 1)),
        (sp.Interval(0, 1), sp.Interval(-sp.oo, 0)),
    ],
)
def test_logarithm_restricted_range(domain, expected):
    result = function_range(sp.log(x), x, y, constraints=domain)
    assert condition_to_set(result, y) == expected


def test_logarithm_disconnected_domain():
    result = function_range(
        sp.log(x),
        x,
        y,
        constraints=sp.Union(sp.Interval(1, 2), sp.Interval(3, 4)),
    )
    # Check exact gaps and endpoint membership in the Boolean image.
    for value in (0, sp.log(2), sp.log(3), sp.log(4)):
        assert sp.simplify(result.subs(y, value)) is sp.S.true
    assert sp.simplify(result.subs(y, sp.log(sp.Rational(5, 2)))) is sp.S.false


def test_monotone_log_exponential_composition():
    expr = sp.log(1 + sp.exp(x))
    domain = sp.Interval(0, 1)
    result = function_range(expr, x, y, constraints=domain)
    assert condition_to_set(result, y) == sp.Interval(sp.log(2), sp.log(1 + sp.E))


def test_exponential_of_periodic_composition():
    result = function_range(sp.exp(sp.sin(x)), x, y, constraints=sp.Interval(0, sp.pi))
    assert condition_to_set(result, y) == sp.Interval(1, sp.E)


def test_hyperbolic_disconnected_domain_keeps_closed_endpoints():
    domain = sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2))
    result = function_range(sp.cosh(x), x, y, constraints=domain)
    for value in (sp.cosh(1), sp.cosh(2)):
        assert sp.simplify(result.subs(y, value)) is sp.S.true
    for value in (0, sp.Rational(3, 2), 4):
        assert sp.simplify(result.subs(y, value)) is sp.S.false
