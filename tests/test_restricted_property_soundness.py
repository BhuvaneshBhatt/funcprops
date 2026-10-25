"""Complex zero decisions and global order across disconnected real domains."""

import pytest
import sympy as sp

from funcprops import domain, monotonicity, sign
from funcprops import range as function_range
from funcprops.exactness import certify_equal, certify_identity_zero, certify_zero
from funcprops.real_analysis.monotonic_certificates import (
    MonotonicInterval,
    MonotonicPartition,
    injectivity_from_partition,
)
from funcprops.results import Monotonicity, Sign, TruthValue

x, y = sp.symbols("x y", real=True)
a = sp.Symbol("a", positive=True)


@pytest.mark.parametrize("expr", [sp.I * a, sp.I * sp.exp(x), x + sp.I])
def test_complex_expression_cannot_be_certified_zero(expr):
    assert certify_zero(expr) is False
    assert certify_equal(expr, 0) is False
    assert certify_identity_zero(expr) is False


def test_complex_pointwise_and_identity_zero_are_distinct():
    assert certify_zero(sp.I * x) is None
    assert certify_identity_zero(sp.I * x) is False
    assert certify_zero(sp.I * x, assumptions=sp.Eq(x, 0)) is True
    assert certify_zero(sp.I * x, assumptions=x > 0) is False


@pytest.mark.parametrize("coefficient", [1, 2, -3])
def test_complex_polynomial_real_domain_and_sign(coefficient):
    expr = (x + coefficient * sp.I) ** 2
    assert domain(expr, x) == sp.Eq(x, 0)
    assert sign(expr, x, domain=sp.Eq(x, 0)) is Sign.NEGATIVE
    assert sign(expr, x, domain=sp.FiniteSet(0)) in (Sign.NEGATIVE, Sign.UNKNOWN)
    assert function_range(expr, x, y, constraints=sp.FiniteSet(0)) == sp.Eq(
        y, -(coefficient**2)
    )
    assert function_range(expr, x, y, constraints=sp.FiniteSet(1)) is sp.S.false


@pytest.mark.parametrize("expr", [sp.I * sp.exp(x), (sp.exp(x) + sp.I) ** 2, sp.I])
def test_nonreal_output_has_no_real_sign_or_domain(expr):
    assert domain(expr, x) is sp.S.false
    assert sign(expr, x, domain=sp.FiniteSet(0)) is Sign.UNKNOWN


def test_complex_exponential_real_axis_domain_is_not_unrestricted():
    assert domain(sp.exp(sp.I * x), x) == sp.Eq(sp.sin(x), 0)
    assert domain(sp.exp(sp.I * x), x, domain=sp.S.Complexes) is sp.S.true
    assert domain(sp.exp(sp.I / x), x, domain=sp.S.Complexes) == sp.Ne(x, 0)


@pytest.mark.parametrize("expr", [sp.atan(1 / x), sp.atan(x) + 1 / x])
@pytest.mark.parametrize("detailed", [False, True])
def test_disconnected_global_order(expr, detailed):
    assert expr.subs(x, -2) > expr.subs(x, -1)
    assert expr.subs(x, -1) < expr.subs(x, 1)
    result = monotonicity(expr, x, return_result=detailed)
    value = result.primary if detailed else result
    assert value is Monotonicity.NOT_MONOTONE
    assert (
        monotonicity(expr, x, domain=sp.Interval(1, 2))
        is Monotonicity.STRICTLY_DECREASING
    )


def _two_cell_partition(second_start, second_end, second_direction):
    intervals = (sp.Interval(0, 1), sp.Interval(2, 3))
    return MonotonicPartition(
        sp.Union(*intervals),
        (
            MonotonicInterval(intervals[0], Monotonicity.STRICTLY_INCREASING, 0, 1),
            MonotonicInterval(intervals[1], second_direction, second_start, second_end),
        ),
        complete=True,
    )


def test_overlapping_component_images():
    partition = _two_cell_partition(0, 1, Monotonicity.STRICTLY_INCREASING)
    assert partition.same_strict_direction() is None
    assert injectivity_from_partition(partition) is TruthValue.UNKNOWN


def test_disconnected_direction_changes():
    partition = _two_cell_partition(3, 2, Monotonicity.STRICTLY_DECREASING)
    assert injectivity_from_partition(partition) is TruthValue.UNKNOWN


def test_ordered_component_images():
    partition = _two_cell_partition(2, 3, Monotonicity.STRICTLY_INCREASING)
    assert partition.same_strict_direction() is Monotonicity.STRICTLY_INCREASING
    assert injectivity_from_partition(partition) is TruthValue.TRUE


def test_missing_injectivity_seams():
    partition = (
        (sp.Interval(0, 1), Monotonicity.STRICTLY_INCREASING),
        (sp.Interval(2, 3), Monotonicity.STRICTLY_INCREASING),
    )
    assert injectivity_from_partition(partition) is TruthValue.UNKNOWN
    assert injectivity_from_partition(partition[:1]) is TruthValue.TRUE


def test_numeric_sign_candidates():
    from funcprops.real_analysis.sign import _sample_sign

    t = sp.Symbol("t", real=True)
    numeric_integral = sp.Integral(sp.exp(-(t**2)), (t, 0, 1))
    assert _sample_sign(numeric_integral) is None


@pytest.mark.parametrize("head", [sp.sin, sp.cos, sp.tan])
@pytest.mark.parametrize("phase", [sp.I, sp.Symbol("unrestricted_phase")])
def test_real_root_families_require_real_phase(head, phase):
    from funcprops.infinite_root_families import affine_trig_root_family
    from funcprops.transcendental.roots import _periodic
    from funcprops.transcendental.zero_geometry import zero_geometry

    expr = head(x + phase)
    assert affine_trig_root_family(expr, x) is None
    assert _periodic(expr, x, sp.S.Reals) is None
    assert not zero_geometry(expr, x)


def test_root_family_verification_rejects_nonreal_formula():
    from dataclasses import replace

    from funcprops.infinite_root_families import affine_trig_root_family

    family = affine_trig_root_family(sp.sin(x), x)
    assert family.verify()
    assert not replace(family, formula=family.formula + sp.I).verify()
    assert not replace(family, index_domain=sp.FiniteSet(0)).verify()


def test_parameter_constant_cannot_be_certified_root_free():
    from funcprops.transcendental.roots import transcendental_roots

    parameter = sp.Symbol("parameter")
    assert not transcendental_roots(parameter, x, allow_numerical=False).complete
    positive = transcendental_roots(a, x, allow_numerical=False)
    assert positive.complete and not positive.roots


@pytest.mark.parametrize("head", [sp.erf, sp.erfi])
def test_unique_real_zero_theorem_requires_real_affine_argument(head):
    from funcprops.transcendental.roots import _special

    assert _special(head(x + sp.I), x, sp.S.Reals) is None
    assert _special(head(2 * x + 1), x, sp.S.Reals).roots == (-sp.Rational(1, 2),)


@pytest.mark.parametrize("threshold", [0, 1])
def test_strict_outer_curvature_does_not_erase_inner_plateau(threshold):
    from funcprops import convexity
    from funcprops.results import Convexity

    expr = sp.exp(sp.Max(threshold, x))
    assert expr.subs(x, -2) == expr.subs(x, -1)
    assert convexity(expr, x) is Convexity.CONVEX
    assert convexity(sp.exp(x**2), x) in (
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
    )


def test_nonlinear_exponential_is_not_automatically_convex():
    from funcprops import convexity
    from funcprops.results import Convexity

    expr = sp.exp(x**3)
    assert sp.diff(expr, x, 2).subs(x, 1) > 0
    assert sp.diff(expr, x, 2).subs(x, -sp.Rational(1, 2)) < 0
    assert convexity(expr, x) in (Convexity.NEITHER, Convexity.UNKNOWN)
