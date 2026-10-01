import sympy as sp

import funcprops as fp
from funcprops.results import Convexity, Homogeneity, Periodicity, Symmetry, TruthValue
from funcprops.verification import (
    verify_homogeneity_result,
    verify_periodicity_result,
    verify_symmetry_result,
)

x, y, a, b = sp.symbols("x y a b", real=True)


def test_commensurate_periods_and_composition_replay():
    e = sp.exp(sp.sin(2 * x) + sp.cos(3 * x))
    r = fp.periodicity(e, x, return_result=True)
    assert r.classification is Periodicity.PERIODIC
    assert sp.simplify(r.period - 2 * sp.pi) == 0
    assert verify_periodicity_result(e, x, r)


def test_incommensurate_visible_frequencies_are_aperiodic():
    assert (
        fp.periodicity(sp.sin(x) + sp.sin(sp.sqrt(2) * x), x) is Periodicity.APERIODIC
    )


def test_parameterized_affine_frequency_retains_condition():
    e = sp.sin(a * x)
    r = fp.periodicity(e, x, return_result=True)
    assert r.classification is Periodicity.PERIODIC
    assert sp.simplify(r.period - 2 * sp.pi / sp.Abs(a)) == 0
    assert r.conditions == sp.Ne(a, 0)
    assert verify_periodicity_result(e, x, r)


def test_parameterized_affine_frequency_replay_keeps_realness_prerequisite():
    u = sp.Symbol("u")
    e = sp.sin(u * x)
    r = fp.periodicity(e, x, return_result=True)
    assert r.classification is Periodicity.PERIODIC
    assert r.conditions.has(sp.Q.real(u))
    assert r.conditions.has(sp.Ne(u, 0))
    assert verify_periodicity_result(e, x, r)
    assert fp.verify_certificate(r, expr=e, var=x)


def test_discovered_polynomial_and_composed_reflection_centers():
    for e in ((x - 2) ** 2, sp.exp((x - 2) ** 2)):
        r = fp.symmetry(e, x, center=None, return_result=True)
        assert r.classification is Symmetry.EVEN and r.center == 2
        assert verify_symmetry_result(e, x, r)
        assert fp.verify_certificate(r, expr=e, var=x)


def test_central_symmetry_preserves_vertical_center():
    e = (x - 2) ** 3 + 5
    r = fp.symmetry(e, x, center=None, return_result=True)
    assert r.classification is Symmetry.CENTRAL
    assert r.center == 2 and r.central_value == 5
    assert verify_symmetry_result(e, x, r)


def test_affine_trigonometric_center_families():
    r = fp.symmetry(sp.sin(3 * x + 1), x, center=None, return_result=True)
    assert r.classification is Symmetry.ODD
    assert r.center == -sp.Rational(1, 3)
    assert sp.simplify(r.center_period - sp.pi / 3) == 0
    assert {q[0] for q in r.center_families} == {Symmetry.EVEN, Symmetry.ODD}


def test_weighted_multivariate_homogeneity_and_replay():
    e = x**2 + y**4
    r = fp.homogeneity(e, (x, y), weights=(2, 1), return_result=True)
    assert r.classification is Homogeneity.HOMOGENEOUS and r.degree == 4
    assert r.weights == (2, 1)
    assert verify_homogeneity_result(e, r)
    assert fp.verify_certificate(r, expr=e)


def test_parameterized_homogeneity_retains_all_strata():
    e = a * x + b * x**2
    r = fp.homogeneity(e, x, return_result=True)
    assert r.classification is Homogeneity.UNKNOWN
    by_degree = {c.degree: c.condition for c in r.cases}
    assert 1 in by_degree and 2 in by_degree and None in by_degree
    assert (
        fp.homogeneity(
            e, x, assumptions=sp.And(sp.Eq(b, 0), sp.Ne(a, 0)), return_result=True
        ).degree
        == 1
    )
    z = fp.homogeneity(
        e, x, assumptions=sp.And(sp.Eq(a, 0), sp.Eq(b, 0)), return_result=True
    )
    assert z.classification is Homogeneity.HOMOGENEOUS and z.degree is None
    nh = fp.homogeneity(
        e, x, assumptions=sp.And(sp.Ne(a, 0), sp.Ne(b, 0)), return_result=True
    )
    assert nh.classification is Homogeneity.NOT_HOMOGENEOUS
    assert fp.homogeneity(e, x) is Homogeneity.UNKNOWN


def test_zero_function_is_homogeneous_of_any_requested_degree():
    assert (
        fp.homogeneity(0, (x, y), degree=sp.Rational(7, 3)) is Homogeneity.HOMOGENEOUS
    )


def test_multivariate_constant_hessian_classification():
    assert fp.convexity(x**2 + y**2, (x, y)) is Convexity.STRONGLY_CONVEX
    assert fp.convexity(x**2 - y**2, (x, y)) is Convexity.NEITHER
    assert fp.convexity(x + y, (x, y)) is Convexity.AFFINE


def test_affine_is_accepted_as_convex_property():
    got = fp.convexity(x + y, (x, y))
    assert got in (
        Convexity.AFFINE,
        Convexity.CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
    )


def test_multivariate_mapping_affine_exactness():
    assert fp.bijective((x + y, -x + y), (x, y)) is TruthValue.TRUE
    assert fp.injective(x + y, (x, y)) is TruthValue.FALSE
    assert fp.surjective(x + y, (x, y)) is TruthValue.TRUE
    nonlinear = (x + y**3, y - x**5)
    assert fp.injective(nonlinear, (x, y)) is TruthValue.UNKNOWN
    assert fp.surjective(nonlinear, (x, y)) is TruthValue.UNKNOWN
    assert fp.bijective(nonlinear, (x, y)) is TruthValue.UNKNOWN


def test_multivariate_regularity_tuple_semantics():
    from funcprops.results import Analyticity, Continuity

    assert fp.analytic(x**2 + y**2, (x, y)) is Analyticity.ANALYTIC
    assert fp.analytic(sp.Abs(x) + y, (x, y)) is Analyticity.NOT_ANALYTIC
    assert fp.continuous(sp.Abs(x) + y, (x, y)) is Continuity.CONTINUOUS


def test_homogeneity_requires_nonzero_coefficient():
    c = sp.symbols("c", real=True)
    e = a * x + b * y + c * x**2
    r = fp.homogeneity(e, (x, y), return_result=True)
    degree1 = next(case for case in r.cases if case.degree == 1)
    # c=0 and either linear coefficient nonzero is enough; one coefficient may vanish.
    assert (
        sp.simplify(
            sp.Implies(sp.And(sp.Eq(c, 0), sp.Eq(a, 0), sp.Ne(b, 0)), degree1.condition)
        )
        is sp.S.true
    )
    got = fp.homogeneity(
        e,
        (x, y),
        assumptions=sp.And(sp.Eq(c, 0), sp.Eq(a, 0), sp.Ne(b, 0)),
        return_result=True,
    )
    assert got.classification is Homogeneity.HOMOGENEOUS and got.degree == 1


def test_strong_convexity_implies_weaker_classes():
    r = fp.convexity(x**2 + y**2, (x, y), all_properties=True, return_result=True)
    assert r.primary is Convexity.STRONGLY_CONVEX
    assert r.all_properties == (Convexity.STRICTLY_CONVEX, Convexity.CONVEX)


def test_symmetry_replay_does_not_turn_unknown_identity_into_neither(monkeypatch):
    import funcprops.verification as verification
    from funcprops.real_analysis.structural_properties import SymmetryResult

    cert = SymmetryResult(Symmetry.NEITHER, center=0)
    monkeypatch.setattr(verification, "certify_identity_equal", lambda *_args: None)
    assert not verification.verify_symmetry_result(sp.Function("f")(x), x, cert)


def test_periodicity_replay_does_not_trust_incommensurate_evidence_label():
    from funcprops.real_analysis.structural_properties import PeriodicityResult

    forged = PeriodicityResult(
        Periodicity.APERIODIC,
        evidence=("incommensurate-component-periods",),
    )
    assert not verify_periodicity_result(sp.sin(x), x, forged)
    genuine = fp.periodicity(sp.sin(x) + sp.sin(sp.sqrt(2) * x), x, return_result=True)
    assert verify_periodicity_result(sp.sin(x) + sp.sin(sp.sqrt(2) * x), x, genuine)
