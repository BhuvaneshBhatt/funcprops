"""Specializing a conditional result must agree with a direct specialized query."""

import sympy as sp

import funcprops as fp
from funcprops.results import PropertyResult

x, a = sp.symbols("x a", real=True)


def _active_value(result, value):
    assert isinstance(result, PropertyResult)
    active = [
        case.value
        for case in result.cases
        if sp.simplify(case.condition.subs(a, value)) is sp.true
    ]
    assert len(active) == 1
    return active[0]


def test_sign_strata_specialize_to_direct_queries():
    stratified = fp.function_sign(a * x, x, domain=x > 0)
    for value in (-2, 0, 3):
        expected = fp.function_sign((a * x).subs(a, value), x, domain=x > 0)
        assert _active_value(stratified, value) is expected


def test_monotonicity_strata_specialize_to_direct_queries():
    stratified = fp.function_monotonicity(a * x, x)
    for value in (-2, 0, 3):
        expected = fp.function_monotonicity((a * x).subs(a, value), x)
        assert _active_value(stratified, value) is expected


def test_convexity_strata_specialize_to_direct_queries():
    stratified = fp.function_convexity(a * x**2, x)
    for value in (-2, 0, 3):
        expected = fp.function_convexity((a * x**2).subs(a, value), x)
        assert _active_value(stratified, value) is expected
