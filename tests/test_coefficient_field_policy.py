"""Larger coefficient fields are explicit, bounded and independently replayable."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import _semialg

x = sp.Symbol("x", real=True)
c = sp.sqrt(2) + sp.sqrt(3) + sp.sqrt(5)


def test_degree_eight():
    assert fp.encode_algebraic_coefficients((c * x,), (x,)) is None
    policy = fp.CoefficientFieldPolicy(max_degree=8)
    proof = fp.encode_algebraic_coefficients((c * x,), (x,), policy=policy)
    assert proof.verify() and sp.degree(proof.polynomial, proof.generator) == 8
    assert _semialg.eligible_problem(c * x, x, coefficient_policy=policy)
    assert not _semialg.eligible_problem(c * x, x)
    assert not replace(proof, transformed=(proof.generator * x + 1,)).verify()


def test_field_caps():
    assert (
        fp.encode_algebraic_coefficients(
            (c * x,),
            (x,),
            policy=fp.CoefficientFieldPolicy(max_degree=8, max_operations=1),
        )
        is None
    )
    with pytest.raises(ValueError):
        fp.CoefficientFieldPolicy(max_degree=True)
    with pytest.raises(ValueError):
        fp.CoefficientFieldPolicy(max_degree=0)


def test_degree_eight_range():
    y = sp.Symbol("y", real=True)
    condition = _semialg.range(
        c * x,
        x,
        y,
        constraints=sp.Eq(x, 1),
        coefficient_policy=fp.CoefficientFieldPolicy(max_degree=8),
    )
    image = fp.condition_to_real_set(condition, y)
    assert isinstance(image, sp.FiniteSet) and len(image) == 1
    from sympy.polys.numberfields import to_number_field

    assert to_number_field(next(iter(image)) - c).as_expr() == 0
