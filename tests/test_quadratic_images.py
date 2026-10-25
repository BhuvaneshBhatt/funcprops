"""Exact quadratic images and bounded dispatch before general range solvers."""

import importlib
import random

import pytest
import semialg
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.common import condition_to_set, set_to_condition
from funcprops.real_analysis.image_rules import _quadratic_image
from tools.benchmark_routing import range_cases

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    ("name", "expression", "source", "expected", "group"), range_cases()[1]
)
def test_range_answers(name, expression, source, expected, group):
    result = fp.range(expression, x, y, constraints=source)
    assert condition_to_set(result, y) == expected


def test_general_solvers_unused(monkeypatch):
    ranges = importlib.import_module("funcprops.real_analysis.range")

    def fail(*args, **kwargs):
        pytest.fail("a supported quadratic reached a general range solver")

    monkeypatch.setattr(ranges, "_semialgebraic_range_stage", fail)
    monkeypatch.setattr(ranges, "_sympy_range", fail)
    monkeypatch.setattr(ranges, "algebraize", fail)
    for _, expression, source, expected, group in range_cases()[1]:
        if group == "quadratic":
            assert (
                condition_to_set(fp.range(expression, x, y, domain=source), y)
                == expected
            )


def test_backend_oracle():
    rng = random.Random(78231)
    for _ in range(60):
        a = rng.choice((-3, -2, -1, 1, 2, 3))
        b, c = (rng.randrange(-5, 6) for _ in range(2))
        lower = sp.Rational(rng.randrange(-8, 5), 2)
        upper = lower + sp.Rational(rng.randrange(1, 9), 2)
        source = sp.Interval(
            lower,
            upper,
            left_open=bool(rng.randrange(2)),
            right_open=bool(rng.randrange(2)),
        )
        expression = a * x**2 + b * x + c
        expected = semialg.quantifier_eliminate(
            sp.And(set_to_condition(source, x), sp.Eq(y, expression)),
            [("exists", x)],
        )
        assert _quadratic_image(expression, x, source) == condition_to_set(expected, y)


@pytest.mark.parametrize(
    ("expression", "source"),
    [
        ((x + 1) ** 2 - x**2, sp.S.Reals),
        (sp.Symbol("a", real=True) * x**2, sp.Interval(0, 1)),
        (sp.sqrt(2) * x**2, sp.Interval(0, 1)),
        (x**2 + sp.Float(1), sp.Interval(0, 1)),
        (x**3 + x, sp.Interval(0, 1)),
        ((x + 1) ** 100000, sp.Interval(0, 1)),
        (x**2, sp.Interval(0, sp.sqrt(2))),
        (x**2, sp.Interval(0, sp.Symbol("a", positive=True))),
        (x**2, sp.S.Integers),
        (x**2, sp.FiniteSet(*range(17))),
        (x**2, sp.Union(*(sp.Interval(3 * k, 3 * k + 1) for k in range(17)))),
        (sp.sin(x), sp.Interval(0, 1)),
    ],
)
def test_declined_forms(expression, source):
    assert _quadratic_image(expression, x, source) is None


@pytest.mark.parametrize("method", ("qe", "cad"))
def test_explicit_method(method, monkeypatch):
    ranges = importlib.import_module("funcprops.real_analysis.range")

    def fail(*args, **kwargs):
        pytest.fail("explicit solver selection reached automatic quadratic dispatch")

    monkeypatch.setattr(ranges, "_quadratic_image", fail)
    result = fp.range(x**2, x, y, constraints=(x >= 0) & (x <= 1), method=method)
    assert condition_to_set(result, y) == sp.Interval(0, 1)


def test_canceled_degree():
    result = fp.range((x + 1) ** 2 - x**2, x, y, domain=sp.Interval.open(0, 1))
    assert condition_to_set(result, y) == sp.Interval.open(1, 3)


def test_parameter_domain():
    a = sp.Symbol("a", positive=True)
    assert _quadratic_image(x**2, x, sp.Interval(0, a)) is None
    assert _quadratic_image(x**2, x, sp.ConditionSet(x, x > a, sp.S.Reals)) is None


def test_tied_qe_endpoint():
    source = (x > -sp.Rational(5, 2)) & (x <= sp.Rational(3, 2))
    result = fp.range(-3 * x**2 - 3 * x - 5, x, y, constraints=source)
    assert condition_to_set(result, y) == sp.Interval(
        -sp.Rational(65, 4), -sp.Rational(17, 4)
    )


def test_coordinate_premises():
    positive = sp.Symbol("p", positive=True)
    integer = sp.Symbol("n", integer=True)
    generic = sp.Symbol("u")
    assert _quadratic_image(positive**2, positive, sp.S.Reals) is None
    assert _quadratic_image(integer**2, integer, sp.S.Reals) is None
    assert _quadratic_image(positive**2, positive, sp.Interval(1, 2)) == sp.Interval(
        1, 4
    )
    assert _quadratic_image(generic**2, generic, sp.S.Reals) == sp.Interval(0, sp.oo)
