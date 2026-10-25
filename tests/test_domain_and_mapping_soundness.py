"""Adversarial proof-hypothesis and certificate-binding regressions."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import Homogeneity, Sign, TruthValue
from funcprops.real_analysis.structural_properties import (
    HomogeneityCase,
    HomogeneityResult,
)
from funcprops.statistical_special_functions import MittagLefflerE

x, y, a = sp.symbols("x y a", real=True)
gap = sp.Union(sp.Interval.open(-sp.oo, 0), sp.Interval.open(0, sp.oo))


@pytest.mark.parametrize(
    "expr,domain",
    [
        (sp.atan(1 / x), sp.S.Reals),
        (sp.atan(1 / x), gap),
        (sp.Piecewise((0, x < 0), (1, True)), gap),
    ],
)
def test_derivative_bound_cannot_cross_missing_seams(expr, domain):
    assert (
        fp.lipschitz(expr, x, domain=domain, return_result=True).value
        is not TruthValue.TRUE
    )
    assert fp.uniformly_continuous(expr, x, domain=domain) is not TruthValue.TRUE
    assert fp.holder_regularity(expr, x, domain=domain) is None


@pytest.mark.parametrize(
    "expr,domain,bound",
    [
        (sp.sin(x), sp.S.Reals, 1),
        (sp.atan(1 / x), sp.Interval(1, 2), sp.Rational(1, 2)),
        (3 * x + 2, sp.S.Reals, 3),
    ],
)
def test_valid_connected_derivative_bounds_survive(expr, domain, bound):
    assert fp.lipschitz(expr, x, domain=domain) == bound


def test_guarded_polynomial_uniform_continuity():
    assert fp.uniformly_continuous(a * x * x, x) is TruthValue.UNKNOWN
    assert fp.uniformly_continuous(x * x, x) is TruthValue.FALSE
    assert fp.uniformly_continuous(0 * x, x) is TruthValue.TRUE


@pytest.mark.parametrize(
    "expr", [sp.besselk(x, x), sp.besselk(x * x, x), MittagLefflerE(x, -x)]
)
def test_complete_monotonicity_requires_fixed_shape_parameter(expr):
    assert fp.complete_monotonicity(expr, x, domain=x > 0) is TruthValue.UNKNOWN


def test_fixed_shape_complete_monotonicity_survives():
    assert (
        fp.complete_monotonicity(sp.besselk(2, x), x, domain=x > 0) is TruthValue.TRUE
    )
    assert (
        fp.complete_monotonicity(
            MittagLefflerE(sp.Rational(1, 2), -x), x, domain=x >= 0
        )
        is TruthValue.TRUE
    )


@pytest.mark.parametrize("expr", [sp.Piecewise((x, x < 0), (x + 1, True)), sp.I * x])
def test_nonzero_jacobian_is_insufficient_for_real_inverse_theorem(expr):
    c = fp.local_invertibility(expr, x, return_result=True)
    assert c.classification is TruthValue.UNKNOWN
    assert c.verify()
    c = fp.change_of_variables(expr, x)
    assert c.classification is TruthValue.UNKNOWN
    assert c.verify()


def test_piecewise_map_restricted_to_smooth_region():
    expr = sp.Piecewise((x, x < 0), (x + 1, True))
    assert (
        fp.local_invertibility(expr, x, domain=sp.Interval(-2, -1)) is TruthValue.TRUE
    )


def test_transformation_replay_binds_all_nested_inputs():
    c = fp.local_invertibility(2 * x, x, return_result=True)
    assert c.verify()
    assert not replace(c, expressions=(3 * x,)).verify()
    assert not replace(c, variables=(y,)).verify()
    wrong = replace(c.nonvanishing, determinant=0)
    assert not replace(c, nonvanishing=wrong).verify()
    c = fp.change_of_variables(2 * x, x)
    assert c.verify()
    assert not replace(c, orientation=Sign.NEGATIVE).verify()
    assert not replace(c, determinant=-2).verify()
    assert not replace(c, domain=sp.Interval(0, 1)).verify()


def test_piecewise_euler_identity_is_not_global_homogeneity():
    expr = sp.Piecewise((1, x < 1), (2, True))
    assert fp.homogeneity(expr, x) is Homogeneity.UNKNOWN
    assert fp.homogeneity(x**2, x) is Homogeneity.HOMOGENEOUS


@pytest.mark.parametrize(
    "assumptions,expected",
    [
        (sp.S.true, Homogeneity.UNKNOWN),
        (sp.Eq(a, 0), Homogeneity.HOMOGENEOUS),
        (sp.Ne(a, 0), Homogeneity.NOT_HOMOGENEOUS),
    ],
)
def test_requested_polynomial_degree_retains_zero_coefficient_stratum(
    assumptions, expected
):
    c = fp.homogeneity(
        a * x * x, x, degree=1, assumptions=assumptions, return_result=True
    )
    assert c.classification is expected
    if expected is not Homogeneity.UNKNOWN:
        assert fp.verify_certificate(c, expr=a * x * x)


def test_fabricated_nonhomogeneity_cases_cannot_verify():
    c = HomogeneityResult(
        Homogeneity.NOT_HOMOGENEOUS,
        variables=(x,),
        weights=(sp.S.One,),
        cases=(HomogeneityCase(2, sp.S.false, (sp.S.One,)),),
    )
    assert not fp.verify_certificate(c, expr=x * x)


def test_pole_local_integrability():
    assert fp.integrability(1 / x, x).locally_integrable is not TruthValue.TRUE
    assert (
        fp.integrability(1 / x, x, domain=sp.Interval(1, 2)).locally_integrable
        is TruthValue.TRUE
    )


def test_derivatives_do_not_erase_piecewise_jump_variation():
    expr = sp.Piecewise((0, x < 0), (1, x < 1), (0, True))
    result = fp.variation(expr, x, domain=sp.Interval(-1, 2), return_result=True)
    assert result.total_variation != 0
    assert (
        result.bounded_variation is not TruthValue.TRUE or result.total_variation == 2
    )
    assert (
        fp.variation(sp.Piecewise((0, x < 0), (1, True)), x, domain=sp.Interval(-1, 1))
        == 1
    )
    assert fp.variation(x * x, x, domain=sp.Interval(-1, 2)) == 5


def test_separable_coercivity_premises():
    expr = x * x - 1 / x**2 + y * y
    assert fp.level_boundedness(expr, (x, y)) is not TruthValue.TRUE
    assert fp.level_boundedness(x**4 + y**6, (x, y)) is TruthValue.TRUE


def test_weierstrass_requires_function_defined_on_the_closed_domain():
    assert fp.mode_existence(x * x - 1 / x**2, x, sense="min") is not TruthValue.TRUE
    c = fp.mode_existence(x * x, x, sense="min", return_result=True)
    assert c.verify()
    assert not replace(c, expression=-x * x).verify()
    c = fp.level_boundedness(x * x, x, return_result=True)
    assert c.verify()
    assert not replace(c, expression=-x * x).verify()


def test_parameter_limit_is_not_a_definite_escape_counterexample():
    assert fp.level_boundedness(a * x * x, x) is TruthValue.UNKNOWN
    pos = sp.Symbol("pos", positive=True)
    neg = sp.Symbol("neg", negative=True)
    assert fp.level_boundedness(pos * x * x, x) is TruthValue.TRUE
    assert fp.level_boundedness(neg * x * x, x) is TruthValue.FALSE
    assert fp.level_boundedness(sp.sin(x), x) is TruthValue.FALSE
