"""Bounded exact coefficient fields retain isolating roots and source restrictions."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import _semialg
from funcprops.real_analysis.common import condition_to_set

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    "constant", [sp.sqrt(2), -sp.sqrt(2), sp.real_root(2, 3), sp.sqrt(2) + sp.sqrt(3)]
)
def test_field_encoding(constant):
    proof = fp.encode_algebraic_coefficients((constant * x, x < constant), (x,))
    assert proof.verify() and fp.verify_certificate(proof)
    assert 1 < sp.degree(proof.polynomial, proof.generator) <= 4
    assert (
        sp.simplify(
            proof.transformed[0].subs(proof.generator, proof.root) - constant * x
        )
        == 0
    )


def test_multiple_coefficients():
    proof = fp.encode_algebraic_coefficients((sp.sqrt(2) * x + sp.sqrt(3),), (x,))
    assert proof.verify() and len(proof.representations) == 2
    assert sp.degree(proof.polynomial, proof.generator) == 4


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, root=-p.root),
        lambda p: replace(p, polynomial=p.generator * p.generator - 3),
        lambda p: replace(p, interval=(-sp.S(2), -sp.S.One)),
        lambda p: replace(p, transformed=(p.generator * x + 1,)),
        lambda p: replace(p, representations=()),
    ],
)
def test_field_mutations(mutate):
    proof = fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,))
    assert not mutate(proof).verify() and not fp.verify_certificate(mutate(proof))


def test_field_replay(monkeypatch):
    proof = fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,))

    def disabled(*args, **kwargs):
        raise AssertionError("encoding search called")

    monkeypatch.setattr("funcprops.algebraic_coefficients.to_number_field", disabled)
    assert proof.verify() and fp.verify_certificate(proof)


@pytest.mark.parametrize(
    "constant", [sp.pi, sp.I, sp.Float("1.25"), sp.sqrt(2) + sp.sqrt(3) + sp.sqrt(5)]
)
def test_unsupported_fields(constant, monkeypatch):
    def disabled(*args, **kwargs):
        raise AssertionError("rational backend loaded")

    monkeypatch.setattr(_semialg, "_public_function", disabled)
    assert fp.encode_algebraic_coefficients((constant * x,), (x,)) is None
    with pytest.raises(NotImplementedError):
        _semialg.sign(constant * x, x)


@pytest.mark.parametrize(
    "support,expected",
    [
        (sp.Interval(0, 1), sp.Interval(0, sp.sqrt(2))),
        (sp.Interval.open(0, 1), sp.Interval.open(0, sp.sqrt(2))),
    ],
)
def test_lifted_range(support, expected):
    actual = _semialg.range(sp.sqrt(2) * x, x, y, constraints=support.as_relational(x))
    assert condition_to_set(actual, y) == expected


def test_lifted_domain_and_shapes():
    assert condition_to_set(
        _semialg.domain(sp.sqrt(x - sp.sqrt(2)), x), x
    ) == sp.Interval(sp.sqrt(2), sp.oo)
    assert (
        _semialg.normalize_sign(_semialg.sign(sp.sqrt(2) * x, x, assumptions=x > 0))
        is fp.Sign.POSITIVE
    )
    assert (
        _semialg.normalize_monotonicity(_semialg.monotonicity(sp.sqrt(2) * x, x))
        is fp.Monotonicity.STRICTLY_INCREASING
    )
    assert (
        _semialg.normalize_convexity(_semialg.convexity(sp.sqrt(2) * x * x, x))
        is fp.Convexity.STRICTLY_CONVEX
    )


def test_lifted_source_hole():
    raw = sp.Mul(
        x - sp.sqrt(2), sp.Pow(x - sp.sqrt(2), -1, evaluate=False), evaluate=False
    )
    domain = _semialg.domain(raw, x)
    assert sp.simplify(domain.subs(x, sp.sqrt(2))) is sp.S.false
    assert _semialg.range(raw, x, y, constraints=sp.Eq(x, sp.sqrt(2))) is sp.S.false


def test_compound_condition_profile():
    condition = (x > 0) & (x < sp.sqrt(2))
    assert (
        _semialg.coefficient_profile(x, x, conditions=(condition,)).kind == "algebraic"
    )
    assert (
        _semialg.coefficient_profile(x, x, conditions=((x > 0) & (x < 1),)).kind
        == "rational"
    )


def test_encoding_cache():
    fp.clear_caches()
    first = fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,))
    second = fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,))
    assert first is second and fp.cache_info()["algebraic_coefficients"].hits == 1
    fp.clear_caches()
    assert fp.cache_info()["algebraic_coefficients"].currsize == 0


def test_coefficient_budget():
    result = fp.encode_algebraic_coefficients(
        (sp.sqrt(2) * x,), (x,), work_budget=sp.Rational(1, 1000000)
    )
    assert result.complete is False and result.certified is False
    assert result.operation == "encode_algebraic_coefficients"
