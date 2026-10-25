"""Global mapping, discrete order and parameter-aware structural proofs."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import Homogeneity, Monotonicity, Periodicity, Symmetry, TruthValue
from funcprops.real_analysis.structural_properties import (
    PeriodicityResult,
    SymmetryResult,
)

x, y, a = sp.symbols("x y a", real=True)


@pytest.mark.parametrize("expr", [(sp.I * x, y), (x + sp.I, y), (a * x + sp.I, y)])
@pytest.mark.parametrize("query", [fp.injective, fp.surjective, fp.bijective])
def test_real_affine_rank_requires_real_outputs(expr, query):
    assert query(expr, (x, y)) is TruthValue.UNKNOWN


def test_affine_bijectivity_does_not_ignore_target():
    target = sp.ProductSet(sp.Interval(0, 1), sp.Interval(0, 1))
    assert fp.bijective((x, y), (x, y), codomain=target) is not TruthValue.TRUE
    assert fp.bijective((x, y), (x, y)) is TruthValue.TRUE


@pytest.mark.parametrize("expr", [sp.exp(sp.I * x), sp.I * sp.exp(sp.I * x)])
def test_real_injective_outer_rules_cannot_clip_complex_inner(expr):
    assert fp.injective(expr, x) is not TruthValue.TRUE


def test_composition_and_finite_images():
    assert fp.injective(sp.exp(x * x), x) is TruthValue.FALSE
    assert (
        fp.injective(sp.exp(sp.I * x), x, domain=sp.FiniteSet(0, sp.pi))
        is TruthValue.TRUE
    )


def test_constant_map_cardinality_must_be_proved():
    assert fp.injective(1, x, domain=sp.And(sp.Eq(x, 0), a > 0)) is not TruthValue.FALSE
    assert fp.injective(1, x, domain=sp.FiniteSet(0)) is TruthValue.TRUE
    assert fp.injective(1, x, domain=sp.FiniteSet(0, 1)) is TruthValue.FALSE
    assert fp.injective(1, x, domain=sp.FiniteSet(a, 0)) is not TruthValue.FALSE


@pytest.mark.parametrize(
    "expr,points,expected",
    [
        (x * x, sp.FiniteSet(-1, 1), Monotonicity.CONSTANT),
        (sp.sin(x), sp.FiniteSet(0, sp.pi), Monotonicity.CONSTANT),
        (
            sp.sin(x),
            sp.FiniteSet(-sp.pi / 2, sp.pi / 2),
            Monotonicity.STRICTLY_INCREASING,
        ),
        (x * x, sp.FiniteSet(-1, 0, 1), Monotonicity.NOT_MONOTONE),
        (a * x, sp.FiniteSet(0, 1), Monotonicity.UNKNOWN),
    ],
)
def test_finite_order_uses_values_not_derivatives(expr, points, expected):
    assert fp.monotonicity(expr, x, domain=points) is expected
    boolean = sp.Or(*(sp.Eq(x, p) for p in points))
    assert fp.monotonicity(expr, x, domain=boolean) is expected
    result = fp.monotonicity(expr, x, domain=points, return_result=True)
    assert result.primary is expected


@pytest.mark.parametrize(
    "assumptions,expected",
    [
        (sp.S.true, Periodicity.UNKNOWN),
        (sp.Eq(a, 0), Periodicity.CONSTANT),
        (sp.Ne(a, 0), Periodicity.APERIODIC),
    ],
)
def test_polynomial_periodicity_retains_zero_coefficient_cases(assumptions, expected):
    c = fp.periodicity(a * x, x, assumptions=assumptions, return_result=True)
    assert c.classification is expected
    assert fp.verify_certificate(c, expr=a * x, var=x)


def test_guarded_polynomial_aperiodicity():
    c = PeriodicityResult(Periodicity.APERIODIC)
    assert not fp.verify_certificate(c, expr=a * x, var=x)
    assert fp.verify_certificate(c, expr=x, var=x)


def test_incommensurate_period_premises():
    assert (
        fp.periodicity(a * sp.sin(x) + sp.sin(sp.sqrt(2) * x), x)
        is not Periodicity.APERIODIC
    )
    assert fp.periodicity(sp.sin(a * x) + sp.sin(x), x) is not Periodicity.APERIODIC
    assert (
        fp.periodicity(sp.sin(x) + sp.sin(sp.sqrt(2) * x), x) is Periodicity.APERIODIC
    )


def test_compact_periodicity_does_not_drop_real_frequency_guard():
    u = sp.Symbol("u")
    assert fp.periodicity(sp.sin(u * x), x) is Periodicity.UNKNOWN
    c = fp.periodicity(sp.sin(u * x), x, return_result=True)
    assert c.classification is Periodicity.PERIODIC
    assert c.conditions.has(sp.Q.real(u))
    assert fp.verify_certificate(c, expr=sp.sin(u * x), var=x)
    c = fp.periodicity(sp.sin(a * x), x, assumptions=sp.Eq(a, 0), return_result=True)
    assert c.classification is Periodicity.CONSTANT
    assert c.conditions == sp.Eq(a, 0)
    assert fp.verify_certificate(c, expr=sp.sin(a * x), var=x)


def test_negative_symmetry_does_not_ignore_parameter_stratum():
    assert fp.symmetry(a * x + x * x, x) is Symmetry.UNKNOWN
    c = SymmetryResult(Symmetry.NEITHER)
    assert not fp.verify_certificate(c, expr=a * x + x * x, var=x)
    assert fp.symmetry(x + x * x, x) is Symmetry.NEITHER


def test_real_symmetry_cannot_have_imaginary_center():
    c = fp.symmetry(sp.cos(x + sp.I), x, center=None, return_result=True)
    assert c.classification is Symmetry.UNKNOWN
    c = SymmetryResult(Symmetry.EVEN, center=-sp.I)
    assert not fp.verify_certificate(c, expr=sp.cos(x + sp.I), var=x)
    assert fp.symmetry(sp.cos(x + sp.I), x, center=-sp.I) is Symmetry.UNKNOWN


def test_discovered_symmetry_metadata_must_replay():
    c = fp.symmetry(sp.sin(3 * x + 1), x, center=None, return_result=True)
    assert fp.verify_certificate(c, expr=sp.sin(3 * x + 1), var=x)
    assert not fp.verify_certificate(
        replace(c, center_period=100), expr=sp.sin(3 * x + 1), var=x
    )
    families = ((Symmetry.ODD, c.center, 100),)
    assert not fp.verify_certificate(
        replace(c, center_families=families), expr=sp.sin(3 * x + 1), var=x
    )
    c = fp.symmetry((x - 2) ** 2, x, center=None, return_result=True)
    assert not fp.verify_certificate(
        replace(c, centers=(100,)), expr=(x - 2) ** 2, var=x
    )


@pytest.mark.parametrize(
    "assumptions,expected",
    [
        (sp.S.true, Homogeneity.UNKNOWN),
        (sp.Eq(a, 0), Homogeneity.HOMOGENEOUS),
        (sp.Ne(a, 0), Homogeneity.NOT_HOMOGENEOUS),
    ],
)
def test_nonpolynomial_homogeneity_keeps_zero_factor_cases(assumptions, expected):
    c = fp.homogeneity(
        a * sp.sqrt(x), x, degree=2, assumptions=assumptions, return_result=True
    )
    assert c.classification is expected
    assert c.requested_degree == 2
    assert fp.verify_certificate(c, expr=a * sp.sqrt(x))


def test_requested_homogeneity_degree():
    c = fp.homogeneity(sp.sqrt(x), x, degree=2, return_result=True)
    assert c.classification is Homogeneity.NOT_HOMOGENEOUS
    assert fp.verify_certificate(c, expr=sp.sqrt(x))
    assert not fp.verify_certificate(
        replace(c, requested_degree=sp.Rational(1, 2)), expr=sp.sqrt(x)
    )
    assert fp.homogeneity(x**a, x, degree=2) is not Homogeneity.NOT_HOMOGENEOUS


def test_finite_injectivity_uses_original_values_and_pole_exclusions():
    assert fp.injective(x * x, x, domain=sp.FiniteSet(-1, 1)) is TruthValue.FALSE
    assert fp.injective(1 / x, x, domain=sp.FiniteSet(0, 1)) is TruthValue.TRUE
    assert (
        fp.injective(sp.exp(sp.I * x), x, domain=sp.FiniteSet(0, sp.pi, 2 * sp.pi))
        is TruthValue.FALSE
    )
