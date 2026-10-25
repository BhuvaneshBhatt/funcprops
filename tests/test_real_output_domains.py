"""Finite real outputs, complex intermediates and exact backend fallbacks."""

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.common import condition_to_set

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize("value", [sp.oo, -sp.oo, sp.zoo, sp.nan])
@pytest.mark.parametrize("mode", [sp.S.Reals, sp.S.Complexes])
def test_nonfinite_constants_have_no_domain(value, mode):
    assert fp.domain(value, x, domain=mode) is sp.S.false


def test_constant_parameter_domain_requires_membership():
    a = sp.Symbol("a")
    assert fp.domain(a, x) == sp.Contains(a, sp.S.Reals)
    assert fp.domain(a, x, domain=sp.S.Complexes) == sp.Contains(a, sp.S.Complexes)
    assert fp.domain(sp.I, x) is sp.S.false
    assert fp.domain(sp.I, x, domain=sp.S.Complexes) is sp.S.true


def test_imaginary_coefficient_real_locus():
    b = sp.Symbol("b", imaginary=True)
    assert fp.domain(b * x, x) == sp.Eq(x, 0)
    assert fp.sign(b * x, x) is fp.Sign.ZERO
    assert fp.range(b * x, x, y, constraints=sp.FiniteSet(0, 1)) == sp.Eq(y, 0)


def test_complex_parameter_domains_retain_reality():
    a = sp.Symbol("a")
    domain = fp.domain(a * x, x)
    assert domain.subs(a, sp.I) == sp.Eq(x, 0)
    assert domain.subs(a, 2) is sp.S.true
    assert fp.domain(a + x, x).subs(a, sp.I) is sp.S.false
    assert condition_to_set(fp.domain(1 / (a + x), x).subs(a, 2), x) == sp.Complement(
        sp.S.Reals, sp.FiniteSet(-2)
    )


def test_exponential_imaginary_frequency():
    b = sp.Symbol("b", imaginary=True)
    domain = fp.domain(sp.exp(b * x), x)
    assert domain.subs({b: sp.I, x: sp.pi}) is sp.S.true
    assert domain.subs({b: sp.I, x: sp.pi / 2}) is sp.S.false


def test_absolute_value_accepts_complex_inputs():
    expression = sp.Abs(sp.sqrt(x))
    assert fp.domain(expression, x) is sp.S.true
    result = fp.range(expression, x, y, constraints=sp.FiniteSet(-4, 0, 9))
    assert condition_to_set(result, y) == sp.FiniteSet(0, 2, 3)


def test_hidden_complex_exponential_values():
    expression = sp.exp(sp.sqrt(-x))
    source = sp.FiniteSet(-(sp.pi**2), 0, sp.pi**2)
    assert fp.domain(expression, x) == "unknown_domain"
    result = fp.range(expression, x, y, constraints=source)
    assert condition_to_set(result, y) == sp.FiniteSet(-1, 1, sp.exp(sp.pi))
    assert fp.sign(expression, x, domain=source) is fp.Sign.SIGN_CHANGING


def test_logarithm_composition_does_not_claim_real_inner_image():
    expression = sp.cos(sp.log(x))
    assert expression.subs(x, -1) == sp.cosh(sp.pi)
    assert fp.domain(expression, x) == "unknown_domain"
    result = fp.range(expression, x, y)
    assert result.func == sp.Function("UnknownRange")
    source = sp.FiniteSet(-sp.exp(sp.pi), -1, 1)
    result = fp.range(expression, x, y, constraints=source)
    assert condition_to_set(result, y) == sp.FiniteSet(
        -sp.cosh(sp.pi), 1, sp.cosh(sp.pi)
    )
    positive = sp.Symbol("positive", positive=True)
    assert condition_to_set(
        fp.range(sp.cos(sp.log(positive)), positive, y), y
    ) == sp.Interval(-1, 1)


def test_held_composition_preserves_logarithm_hole():
    expression = sp.exp(sp.log(x, evaluate=False), evaluate=False)
    assert fp.domain(expression, x) == sp.Ne(x, 0)
    result = fp.range(expression, x, y, constraints=sp.FiniteSet(-1, 0, 1))
    assert condition_to_set(result, y) == sp.FiniteSet(-1, 1)


def test_piecewise_nonfinite_branch_is_excluded():
    expression = sp.Piecewise((sp.zoo, x > 0), (0, True))
    assert fp.domain(expression, x) == (x <= 0)


@pytest.mark.parametrize("coefficient", [sp.sqrt(2), sp.pi, sp.E])
def test_exact_nonrational_sign_fallback(coefficient):
    assert fp.sign(coefficient * x, x) is fp.Sign.SIGN_CHANGING
    assert fp.sign(coefficient * x + 1, x) is fp.Sign.SIGN_CHANGING
    assert fp.sign(coefficient * x, x, domain=x > 0) is fp.Sign.POSITIVE
    assert fp.monotonicity(coefficient * x**4 + x**2, x) is fp.Monotonicity.NOT_MONOTONE
    assert fp.convexity(coefficient * x**4 + x**2, x) is fp.Convexity.STRONGLY_CONVEX


@pytest.mark.parametrize("outer", [sp.exp, sp.sin, sp.log])
def test_unknown_inner_domain_is_not_discarded(outer):
    unknown = sp.Function("unknown")
    assert fp.domain(outer(unknown(x)), x) == "unknown_domain"


def test_unknown_piecewise_domain_propagates():
    unknown = sp.Function("unknown")
    expression = sp.Piecewise((unknown(x), x < 0), (0, True))
    assert fp.domain(expression, x) == "unknown_domain"


@pytest.mark.parametrize("exponent", [sp.sqrt(2), sp.pi, sp.E])
def test_positive_nonrational_power_owns_zero(exponent):
    expression = x**exponent
    assert fp.domain(expression, x) == (x >= 0)
    image = fp.range(expression, x, y, constraints=sp.FiniteSet(0, 1))
    assert condition_to_set(image, y) == sp.FiniteSet(0, 1)
    assert fp.domain(x ** (-exponent), x) == (x > 0)
    closed = fp.range(expression, x, y, constraints=sp.Interval(0, 1))
    assert condition_to_set(closed, y) == sp.Interval(0, 1)
    opened = fp.range(expression, x, y, constraints=sp.Interval.open(0, 1))
    assert condition_to_set(opened, y) == sp.Interval.open(0, 1)


def test_held_power_accepts_complex_base_values():
    expression = sp.Pow(sp.sqrt(x), 2, evaluate=False)
    assert fp.domain(expression, x) is sp.S.true
    result = fp.range(expression, x, y, constraints=sp.FiniteSet(-1, 0, 1))
    assert condition_to_set(result, y) == sp.FiniteSet(-1, 0, 1)


def test_zero_power_retains_complex_source_hole():
    expression = sp.Pow(sp.log(x), 0, evaluate=False)
    assert fp.domain(expression, x) == sp.Ne(x, 0)
    result = fp.range(expression, x, y, constraints=sp.FiniteSet(-1, 0, 1))
    assert condition_to_set(result, y) == sp.FiniteSet(1)
    assert fp.range(expression, x, y, constraints=sp.FiniteSet(0)) is sp.S.false


def test_shared_domain_cannot_omit_a_root():
    expression = sp.Add(sp.Pow(sp.sqrt(x), 2, evaluate=False), 1, evaluate=False)
    source = sp.Interval(-2, 2)
    record = fp.track_domain(expression, x, source)
    assert record.complete and record.verify()
    assert record.natural == sp.S.Reals
    assert record.effective == source
    result = fp.solve(expression, x, domain=source, return_certificate=True)
    assert result.complete and result.verify()
    assert result.solutions == sp.FiniteSet(-1)


def test_shared_domain_preserves_canceled_complex_holes():
    square = sp.Pow(sp.sqrt(x), 2, evaluate=False)
    expression = sp.Mul(square, sp.Pow(x, -1, evaluate=False), evaluate=False)
    source = sp.Interval(-1, 1)
    record = fp.track_domain(expression, x, source)
    expected = sp.Union(sp.Interval.Ropen(-1, 0), sp.Interval.Lopen(0, 1))
    assert record.complete and record.verify()
    assert record.effective == expected
    equation = sp.Add(expression, -1, evaluate=False)
    result = fp.solve(equation, x, domain=source, return_certificate=True)
    assert result.complete and result.verify()
    assert result.solutions == expected


def test_complex_power_zero_product_has_full_real_domain():
    expression = sp.Mul(sp.S.Zero, sp.Pow(x, sp.pi, evaluate=False), evaluate=False)
    result = fp.solve(expression, x, domain=sp.S.Reals, return_certificate=True)
    assert result.complete and result.verify()
    assert result.solutions == sp.S.Reals


def test_negative_phase_cannot_prove_positive_tail():
    from funcprops.asymptotic_tails import TailSignCertificate, certify_tail_sign

    expression = sp.exp(x + sp.I * sp.pi, evaluate=False)
    assert expression.subs(x, 0) == -1
    forged = TailSignCertificate(
        expression, x, 1, sp.S.Zero, 1, "exp-polynomial-dominance"
    )
    assert not forged.verify()
    assert certify_tail_sign(expression, x, threshold=0) is None


def test_held_constant_cannot_hide_undefined_operand():
    expression = sp.exp(sp.log(0, evaluate=False), evaluate=False)
    assert fp.domain(expression, x) is sp.S.false
    assert fp.domain(expression, x, domain=sp.S.Complexes) is sp.S.false
    record = fp.track_domain(expression, x)
    assert record.complete and record.verify()
    assert record.effective is sp.S.EmptySet
    result = fp.solve(expression, x, domain=sp.S.Reals, return_certificate=True)
    assert result.complete and result.verify()
    assert result.solutions is sp.S.EmptySet


def test_held_constant_accepts_defined_complex_intermediate():
    expression = sp.exp(sp.log(-1, evaluate=False), evaluate=False)
    assert fp.domain(expression, x) is sp.S.true
    assert fp.range(expression, x, y, constraints=sp.FiniteSet(0)) == sp.Eq(y, -1)
