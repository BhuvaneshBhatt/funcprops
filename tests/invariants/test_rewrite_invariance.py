"""Equivalent expression forms should not change global property conclusions."""

import sympy as sp
from hypothesis import given
from hypothesis import strategies as st

import funcprops as fp

x = sp.symbols("x", real=True)


@given(c=st.integers(-5, 5), k=st.integers(1, 6))
def test_positive_quadratic_rewrites_preserve_sign_and_convexity(c, k):
    expr = (x + c) ** 2 + k
    forms = (expr, sp.expand(expr), sp.factor(sp.expand(expr)))
    assert {fp.function_sign(form, x) for form in forms} == {fp.Sign.POSITIVE}
    assert {fp.function_convexity(form, x) for form in forms} == {
        fp.Convexity.STRONGLY_CONVEX
    }


@given(a=st.integers(-4, 4).filter(bool), b=st.integers(-5, 5))
def test_nonzero_affine_rewrites_preserve_mapping_properties(a, b):
    expr = a * x + b
    forms = (expr, sp.expand(expr), sp.factor(expr))
    assert {fp.function_injective(form, x) for form in forms} == {fp.TruthValue.TRUE}
    assert {fp.function_surjective(form, x) for form in forms} == {fp.TruthValue.TRUE}
