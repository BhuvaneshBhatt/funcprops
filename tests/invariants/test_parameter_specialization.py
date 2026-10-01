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
    stratified = fp.sign(a * x, x, domain=x > 0, return_result=True)
    for value in (-2, 0, 3):
        expected = fp.sign((a * x).subs(a, value), x, domain=x > 0)
        assert _active_value(stratified, value) is expected


def test_monotonicity_strata_specialize_to_direct_queries():
    stratified = fp.monotonicity(a * x, x, return_result=True)
    for value in (-2, 0, 3):
        expected = fp.monotonicity((a * x).subs(a, value), x)
        assert _active_value(stratified, value) is expected


def test_convexity_strata_specialize_to_direct_queries():
    stratified = fp.convexity(a * x**2, x, return_result=True)
    for value in (-2, 0, 3):
        expected = fp.convexity((a * x**2).subs(a, value), x)
        assert _active_value(stratified, value) is expected
