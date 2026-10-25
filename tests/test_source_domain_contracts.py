"""Raw operand definitions survive value normalization and consumer proofs."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.local_analyticity import (
    complex_definition_domain,
    complex_meromorphic_germ,
)
from funcprops.piecewise_proofs import complex_source_defined
from funcprops.proof_cache import cached_derivative
from funcprops.real_analysis.common import condition_to_set
from funcprops.transcendental.analytic import holomorphic_on_rectangle
from funcprops.transcendental.real_sign import robust_real_sign

x, y = sp.symbols("x y", real=True)
bad = sp.exp(sp.log(0, evaluate=False), evaluate=False)
undefined = (
    sp.Add(x, bad, evaluate=False),
    sp.Mul(x, bad, evaluate=False),
    sp.Pow(x, bad, evaluate=False),
    sp.Pow(bad, x, evaluate=False),
    sp.Pow(bad, 0, evaluate=False),
    sp.exp(sp.Add(x, bad, evaluate=False), evaluate=False),
    sp.sin(sp.Mul(x, bad, evaluate=False), evaluate=False),
    sp.log(x, bad, evaluate=False),
    sp.log(x, 0, evaluate=False),
    sp.log(x, 1, evaluate=False),
)


@pytest.mark.parametrize("expression", undefined)
@pytest.mark.parametrize("mode", [sp.S.Reals, sp.S.Complexes])
def test_undefined_operands_have_empty_domain(expression, mode):
    assert fp.domain(expression, x, domain=mode) is sp.S.false


@pytest.mark.parametrize("expression", undefined)
def test_undefined_sources_cannot_gain_solutions(expression):
    support = sp.Interval(-1, 1)
    record = fp.track_domain(expression, x, support)
    assert record.complete and record.verify()
    assert record.natural is sp.S.EmptySet
    assert record.effective is sp.S.EmptySet
    assert not replace(record, natural=sp.S.Reals, effective=support).verify()
    result = fp.solve(expression, x, domain=support, return_certificate=True)
    assert result.complete and result.verify()
    assert result.solutions is sp.S.EmptySet
    for requested in (support, sp.FiniteSet(-1, 0, 1)):
        assert fp.range(expression, x, y, constraints=requested) is sp.S.false


@pytest.mark.parametrize("base", [2, sp.Rational(1, 2), sp.E])
def test_logarithm_base_retains_image(base):
    expression = sp.log(x, base, evaluate=False)
    assert fp.domain(expression, x) == (x > 0)
    assert fp.domain(expression, x, domain=sp.S.Complexes) == sp.Ne(x, 0)
    actual = fp.range(expression, x, y, constraints=sp.FiniteSet(0, 1, base))
    assert condition_to_set(actual, y) == sp.FiniteSet(0, 1)


def test_logarithm_self_base_preserves_both_holes():
    expression = sp.log(x, x, evaluate=False)
    support = sp.FiniteSet(-1, 0, 1, 2)
    record = fp.track_domain(expression, x, support)
    assert record.complete and record.verify()
    assert record.effective == sp.FiniteSet(-1, 2)
    assert fp.range(expression, x, y, constraints=support) == sp.Eq(y, 1)


@pytest.mark.parametrize("expression", [bad, *undefined])
def test_complex_path_definition_keeps_operands(expression):
    assert not complex_source_defined(expression, x, sp.Interval(0, 1))


def test_continuation_rejects_undefined_path():
    z = sp.Symbol("z")
    unit = sp.Pow(sp.oo, 0, evaluate=False)
    gamma = sp.Mul(unit, sp.exp(2 * sp.pi * sp.I * x), evaluate=False)
    path = fp.ParametricContour(gamma, (x, 0, 1))
    assert fp.analytic_continue(sp.log(z), z, path, return_certificate=True) is None


def test_zero_exponent_with_defined_base_remains_valid():
    z = sp.Symbol("z")
    unit = sp.Pow(0, 0, evaluate=False)
    gamma = sp.Mul(unit, sp.exp(2 * sp.pi * sp.I * x), evaluate=False)
    path = fp.ParametricContour(gamma, (x, 0, 1))
    result = fp.analytic_continue(sp.log(z), z, path, return_certificate=True)
    assert result.verify() and result.complete
    assert sp.simplify(result.continued - sp.log(z) - 2 * sp.pi * sp.I) == 0


def test_finite_metric_retains_effective_domain():
    unit = sp.Pow(sp.log(x), 0, evaluate=False)
    expression = sp.Mul(unit, x**2, evaluate=False)
    result = fp.lipschitz(expression, x, domain=sp.FiniteSet(0, 1), return_result=True)
    assert result.value is fp.TruthValue.TRUE
    assert result.domain == sp.FiniteSet(1)
    assert result.constant == 0 and result.optimal is fp.TruthValue.TRUE
    assert fp.holder_regularity(expression, x, domain=sp.FiniteSet(0, 1)) == 1


def test_defined_complex_constants_survive():
    constant = sp.exp(sp.log(-1, evaluate=False), evaluate=False)
    expression = sp.Add(x, constant, evaluate=False)
    assert fp.domain(expression, x) is sp.S.true
    assert fp.range(expression, x, y, constraints=sp.FiniteSet(0, 1)) == sp.Or(
        sp.Eq(y, -1), sp.Eq(y, 0)
    )
    assert complex_source_defined(expression, x, sp.Interval(0, 1))


def test_inactive_undefined_branch_stays_inactive():
    expression = sp.Piecewise((bad, x < 0), (x, True), evaluate=False)
    assert fp.domain(expression, x) == (x >= 0)
    assert complex_source_defined(expression, x, sp.Interval(0, 1))
    result = fp.solve(expression, x, domain=sp.Interval(0, 1), return_certificate=True)
    assert result.complete and result.verify() and result.solutions == sp.FiniteSet(0)


def test_complex_relations_preserve_negative_axis():
    base = sp.log(x) ** 2 + sp.pi**2
    assert condition_to_set(sp.Eq(base, 0), x) == sp.FiniteSet(-1)
    assert condition_to_set(sp.Ne(base, 0), x) == sp.S.Reals - sp.FiniteSet(-1, 0)
    unit = sp.Mul(base, sp.Pow(base, -1, evaluate=False), evaluate=False)
    equation = sp.Add(unit, -1, evaluate=False)
    result = fp.solve(equation, x, domain=sp.S.Reals, return_certificate=True)
    assert result.complete and result.verify()
    assert result.solutions == sp.S.Reals - sp.FiniteSet(-1, 0)


@pytest.mark.parametrize("base", [0, 1, bad])
def test_complex_definition_rejects_invalid_logarithm_base(base):
    z = sp.Symbol("z")
    expression = sp.log(z, base, evaluate=False)
    assert complex_definition_domain(expression, z, sp.S.Complexes) is None
    assert not complex_meromorphic_germ(expression, z, 2)
    assert fp.residue(expression, z, 2, return_certificate=True) is None


def test_essential_residue_keeps_constant_source_holes():
    z = sp.Symbol("z")
    unit = sp.Pow(sp.log(0, evaluate=False), 0, evaluate=False)
    expression = sp.Mul(unit, sp.exp(1 / z), evaluate=False)
    assert fp.residue(expression, z, 0, return_certificate=True) is None


@pytest.mark.parametrize("base", [2, sp.Rational(1, 2)])
def test_logarithm_enclosure_retains_base(base):
    expression = sp.log(x, base, evaluate=False)
    ball = fp.certified_real_ball(expression, x, sp.Interval(2, 4))
    assert ball.verify()
    values = (1, 2) if base == 2 else (-1, -2)
    for value in values:
        assert ball.lower <= value <= ball.upper
    model = fp.taylor_model(expression, x, sp.Interval(2, 3), order=2, center=2)
    assert model.verify()
    assert (
        sp.simplify(sp.expand(model.polynomial).coeff(x, 2) + 1 / (8 * sp.log(base)))
        == 0
    )


@pytest.mark.parametrize("base", [2, sp.Rational(1, 2)])
def test_logarithm_derivative_consumers_retain_base(base):
    expression = sp.log(x, base, evaluate=False)
    derivative = cached_derivative(expression, x)
    assert sp.simplify(derivative - 1 / (x * sp.log(base))) == 0
    expected = (
        fp.Monotonicity.STRICTLY_INCREASING
        if base == 2
        else fp.Monotonicity.STRICTLY_DECREASING
    )
    assert fp.monotonicity(expression, x, domain=sp.Interval(2, 4)) is expected


def test_nested_variable_base_differentiation():
    expression = sp.sin(sp.log(x, x, evaluate=False))
    assert cached_derivative(expression, x) == 0


def test_based_logarithm_continuation_retains_source():
    z = sp.Symbol("z")
    expression = sp.log(z, 2, evaluate=False)
    circle = fp.ParametricContour(sp.exp(2 * sp.pi * sp.I * x), (x, 0, 1))
    result = fp.analytic_continue(expression, z, circle, return_certificate=True)
    assert result.expression == expression
    assert result.verify() and result.complete
    expected = (sp.log(z) + 2 * sp.pi * sp.I) / sp.log(2)
    assert sp.simplify(result.continued - expected) == 0
    assert not replace(result, continued=sp.log(z) + 2 * sp.pi * sp.I).verify()


def test_logarithm_base_domain_in_complex_chart():
    z = sp.Symbol("z")
    rectangle = (1 - sp.I, 2 + sp.I)
    valid = holomorphic_on_rectangle(sp.log(z, 2, evaluate=False), z, rectangle)
    assert valid.holomorphic is True
    invalid = holomorphic_on_rectangle(sp.log(z, 0, evaluate=False), z, rectangle)
    assert invalid.holomorphic is None


@pytest.mark.parametrize("base,expected", [(2, 1), (sp.Rational(1, 2), -1)])
def test_numeric_sign_retains_logarithm_base(base, expected):
    assert robust_real_sign(sp.log(2, base, evaluate=False)) == expected
    assert robust_real_sign(bad) is None


def test_constant_piecewise_retains_branch_domains():
    a = sp.Symbol("a", real=True)
    expression = sp.Piecewise((bad, a > 0), (1, True), evaluate=False)
    assert fp.domain(expression, x) == (a <= 0)


def test_undefined_piecewise_guard_has_no_domain():
    guard = sp.Gt(sp.log(0, evaluate=False), 0, evaluate=False)
    expression = sp.Piecewise((1, guard), (2, True), evaluate=False)
    assert fp.domain(expression, x) is sp.S.false


def test_piecewise_ordering_guard_requires_real_operands():
    expression = sp.Piecewise((1, sp.log(x) > 0), (0, True))
    assert fp.domain(expression, x) == (x > 0)


def test_inactive_piecewise_guard_is_not_evaluated():
    expression = sp.Piecewise((1, x <= 0), (2, sp.log(x) > 0), (3, True))
    assert fp.domain(expression, x) is sp.S.true
