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
    assert fp.domain(sp.log(x), x) == (x > 0)
    assert fp.range(x**2, x, y) == (y >= 0)
    assert fp.branch_cuts(sp.log(x), x)
    assert fp.branch_points(sp.log(x), x) == sp.Eq(x, 0)
    assert fp.poles(1 / x, x)
    assert fp.singularities(1 / x, x) == sp.Eq(x, 0)
    assert fp.singularity_analysis(1 / x, x).complete
    assert isinstance(fp.discontinuities(1 / x, x), sp.Basic)
    assert fp.analytic(sp.exp(x), x) is Analyticity.ANALYTIC
    assert fp.meromorphic(1 / x, x) is Meromorphicity.MEROMORPHIC
    assert fp.continuous(sp.Abs(x), x) is Continuity.CONTINUOUS
    assert fp.differentiability(x**2, x) in (
        Differentiability.DIFFERENTIABLE,
        Differentiability.SMOOTH,
    )
    assert fp.monotonicity(x, x) is Monotonicity.STRICTLY_INCREASING
    assert fp.convexity(x**2, x) in (
        Convexity.STRONGLY_CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.CONVEX,
    )
    assert fp.sign(x**2, x) is Sign.NONNEGATIVE
    assert fp.zeros(x**2 - 1, x) == sp.FiniteSet(-1, 1)
    assert fp.boundedness(sp.sin(x), x) is Boundedness.BOUNDED
    assert fp.injective(x, x) is TruthValue.TRUE
    assert fp.surjective(x, x) is TruthValue.TRUE
    assert fp.bijective(x, x) is TruthValue.TRUE
    assert fp.smoothness(sp.Abs(x), x) == 0
    assert fp.oscillation(sp.sin(x), x) is Oscillation.OSCILLATORY
    assert fp.periodicity(sp.sin(x), x) is Periodicity.PERIODIC
    assert fp.symmetry(sp.sin(x), x) is Symmetry.ODD
    assert fp.homogeneity(x**2, (x,)) is Homogeneity.HOMOGENEOUS


def test_differentiability_contract_edge_cases():
    assert fp.differentiability(sp.exp(x), x) in (
        Differentiability.DIFFERENTIABLE,
        Differentiability.SMOOTH,
    )
    # Abs is not globally differentiable; smoothness is the stronger exact API.
    s = fp.smoothness(sp.Abs(x), x, return_result=True)
    assert s.differentiability_order == 0
    assert sp.Eq(x, 0) in s.exceptional_loci


def test_zero_contract_finite_periodic_and_indexed():
    assert fp.zeros(x**2 - 1, x) == sp.FiniteSet(-1, 1)
    z = fp.zeros(sp.sin(x), x, return_result=True)
    assert getattr(z, "complete", False)
    b = fp.zeros(sp.besselj(0, x), x, domain=x > 0, return_result=True)
    assert getattr(b, "geometry", ())


def test_smoothness_contract_analytic_and_exceptional():
    assert fp.smoothness(sp.exp(x), x) is sp.oo
    assert fp.smoothness(sp.Abs(x), x) == 0
    b = fp.smoothness(sp.Abs(x), x, return_result=True)
    assert b.smooth is False and sp.Eq(x, 0) in b.exceptional_loci


def test_oscillation_contract_three_classes():
    assert fp.oscillation(x, x) is Oscillation.NONOSCILLATORY
    assert (
        fp.oscillation(x**3 - 3 * x, x, domain=sp.Interval(-2, 2))
        is Oscillation.FINITELY_OSCILLATORY
    )
    assert fp.oscillation(sp.sin(x), x) is Oscillation.OSCILLATORY


def test_mapping_contracts_and_codomain():
    assert fp.injective(x**3, x) is TruthValue.TRUE
    assert fp.injective(x**2, x) is TruthValue.FALSE
    assert fp.surjective(x, x, codomain=sp.S.Reals) is TruthValue.TRUE
    assert fp.bijective(x, x, codomain=sp.S.Reals) is TruthValue.TRUE


def test_new_periodicity_details_and_negative_proof():
    r = fp.periodicity(sp.sin(2 * x), x, return_result=True)
    assert r.classification is Periodicity.PERIODIC
    assert sp.simplify(r.period - sp.pi) == 0
    assert fp.periodicity(x**3 + x, x) is Periodicity.APERIODIC
    assert fp.periodicity(sp.Integer(7), x) is Periodicity.CONSTANT


def test_new_symmetry_about_zero_and_center():
    assert fp.symmetry(sp.cos(x), x) is Symmetry.EVEN
    assert fp.symmetry(sp.sin(x), x) is Symmetry.ODD
    assert fp.symmetry(x + 1, x) is Symmetry.NEITHER
    assert fp.symmetry((x - 2) ** 2, x, center=2) is Symmetry.EVEN


def test_new_homogeneity_degree_contract():
    r = fp.homogeneity(x**2 + y**2, (x, y), return_result=True)
    assert r.classification is Homogeneity.HOMOGENEOUS and r.degree == 2
    assert fp.homogeneity(x + y**2, (x, y)) is Homogeneity.NOT_HOMOGENEOUS
    assert (
        fp.homogeneity(sp.sqrt(x**2 + y**2), (x, y), degree=1)
        is Homogeneity.HOMOGENEOUS
    )


def test_smoothness_returns_regularity_order_and_smooth_is_predicate():
    x = sp.symbols("x", real=True)
    assert fp.smoothness(sp.Abs(x), x) == 0
    assert fp.smoothness(sp.exp(x), x) is sp.oo
    assert fp.smooth(sp.Abs(x), x) is TruthValue.FALSE
    assert fp.smooth(sp.exp(x), x) is TruthValue.TRUE
