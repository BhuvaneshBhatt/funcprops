import sympy as sp

import funcprops as fp
from funcprops.results import (
    Analyticity,
    Boundedness,
    Continuity,
    Convexity,
    Differentiability,
    Homogeneity,
    Meromorphicity,
    Monotonicity,
    Oscillation,
    Periodicity,
    Sign,
    Symmetry,
    TruthValue,
)

x, y = sp.symbols("x y", real=True)


def test_every_public_function_property_has_direct_contract():
    assert fp.function_domain(sp.log(x), x) == (x > 0)
    assert fp.function_range(x**2, x, y) == (y >= 0)
    assert fp.function_branchcuts(sp.log(x), x)
    assert fp.function_branchpoints(sp.log(x), x)
    assert fp.function_poles(1 / x, x)
    assert "poles" in fp.function_singularities(1 / x, x)
    assert fp.function_singularity_analysis(1 / x, x).complete
    assert isinstance(fp.function_discontinuities(1 / x, x), tuple)
    assert fp.function_analytic(sp.exp(x), x) is Analyticity.ANALYTIC
    assert fp.function_meromorphic(1 / x, x) is Meromorphicity.MEROMORPHIC
    assert fp.function_continuous(sp.Abs(x), x) is Continuity.CONTINUOUS
    assert fp.function_differentiability(x**2, x) in (
        Differentiability.DIFFERENTIABLE,
        Differentiability.SMOOTH,
    )
    assert fp.function_monotonicity(x, x) is Monotonicity.STRICTLY_INCREASING
    assert fp.function_convexity(x**2, x) in (
        Convexity.STRONGLY_CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.CONVEX,
    )
    assert fp.function_sign(x**2, x) is Sign.NONNEGATIVE
    assert fp.function_zeros(x**2 - 1, x) == sp.FiniteSet(-1, 1)
    assert fp.function_boundedness(sp.sin(x), x) is Boundedness.BOUNDED
    assert fp.function_injective(x, x) is TruthValue.TRUE
    assert fp.function_surjective(x, x) is TruthValue.TRUE
    assert fp.function_bijective(x, x) is TruthValue.TRUE
    assert fp.function_smoothness(sp.Abs(x), x).differentiability_order == 0
    assert fp.function_oscillation(sp.sin(x), x) is Oscillation.OSCILLATORY
    assert fp.function_periodicity(sp.sin(x), x) is Periodicity.PERIODIC
    assert fp.function_symmetry(sp.sin(x), x) is Symmetry.ODD
    assert fp.function_homogeneity(x**2, (x,)) is Homogeneity.HOMOGENEOUS


def test_differentiability_contract_edge_cases():
    assert fp.function_differentiability(sp.exp(x), x) in (
        Differentiability.DIFFERENTIABLE,
        Differentiability.SMOOTH,
    )
    # Abs is not globally differentiable; smoothness is the stronger exact API.
    s = fp.function_smoothness(sp.Abs(x), x)
    assert s.differentiability_order == 0
    assert sp.Eq(x, 0) in s.exceptional_loci


def test_zero_contract_finite_periodic_and_indexed():
    assert fp.function_zeros(x**2 - 1, x) == sp.FiniteSet(-1, 1)
    z = fp.function_zeros(sp.sin(x), x, return_result=True)
    assert getattr(z, "complete", False)
    b = fp.function_zeros(sp.besselj(0, x), x, domain=x > 0, return_result=True)
    assert getattr(b, "geometry", ())


def test_smoothness_contract_analytic_and_exceptional():
    a = fp.function_smoothness(sp.exp(x), x)
    assert a.smooth is True
    b = fp.function_smoothness(sp.Abs(x), x)
    assert b.smooth is False and sp.Eq(x, 0) in b.exceptional_loci


def test_oscillation_contract_three_classes():
    assert fp.function_oscillation(x, x) is Oscillation.NONOSCILLATORY
    assert (
        fp.function_oscillation(x**3 - 3 * x, x, domain=sp.Interval(-2, 2))
        is Oscillation.FINITELY_OSCILLATORY
    )
    assert fp.function_oscillation(sp.sin(x), x) is Oscillation.OSCILLATORY


def test_mapping_contracts_and_codomain():
    assert fp.function_injective(x**3, x) is TruthValue.TRUE
    assert fp.function_injective(x**2, x) is TruthValue.FALSE
    assert fp.function_surjective(x, x, codomain=sp.S.Reals) is TruthValue.TRUE
    assert fp.function_bijective(x, x, codomain=sp.S.Reals) is TruthValue.TRUE


def test_new_periodicity_details_and_negative_proof():
    r = fp.function_periodicity(sp.sin(2 * x), x, details=True)
    assert r.classification is Periodicity.PERIODIC
    assert sp.simplify(r.period - sp.pi) == 0
    assert fp.function_periodicity(x**3 + x, x) is Periodicity.APERIODIC
    assert fp.function_periodicity(sp.Integer(7), x) is Periodicity.CONSTANT


def test_new_symmetry_about_zero_and_center():
    assert fp.function_symmetry(sp.cos(x), x) is Symmetry.EVEN
    assert fp.function_symmetry(sp.sin(x), x) is Symmetry.ODD
    assert fp.function_symmetry(x + 1, x) is Symmetry.NEITHER
    assert fp.function_symmetry((x - 2) ** 2, x, center=2) is Symmetry.EVEN


def test_new_homogeneity_degree_contract():
    r = fp.function_homogeneity(x**2 + y**2, (x, y), details=True)
    assert r.classification is Homogeneity.HOMOGENEOUS and r.degree == 2
    assert fp.function_homogeneity(x + y**2, (x, y)) is Homogeneity.NOT_HOMOGENEOUS
    assert (
        fp.function_homogeneity(sp.sqrt(x**2 + y**2), (x, y), degree=1)
        is Homogeneity.HOMOGENEOUS
    )
