from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.regularity_evidence import (
    discontinuity_at,
    piecewise_failure_witness,
    regularity_normal_form,
)
from funcprops.results import Analyticity, Continuity, Meromorphicity

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")


@pytest.mark.parametrize(
    "f",
    [
        sp.gamma(1 / z),
        sp.tan(1 / z),
        sp.polygamma(0, 1 / z),
        sp.zeta(1 / z),
        sp.log(sp.exp(z)),
        sp.exp(sp.Abs(z)),
        sp.sin(sp.re(z)),
    ],
)
def test_no_global_meromorphic_claim_from_local_or_outer_primitive(f):
    assert fp.meromorphic(f, z) is Meromorphicity.UNKNOWN


@pytest.mark.parametrize(
    "f",
    [
        sp.gamma(z * z + 1),
        sp.tan(sp.exp(z)),
        sp.exp(z) + sp.sin(z),
        1 / (z * z + 1),
        sp.besselj(sp.Symbol("n", integer=True), z),
    ],
)
def test_global_entire_inner_map_and_known_primitive_theorems_survive(f):
    assert fp.meromorphic(f, z) is Meromorphicity.MEROMORPHIC


@pytest.mark.parametrize("f", [sp.log(z), sp.sqrt(z), sp.exp(1 / z), sp.exp(1 / z) + z])
def test_whole_source_obstructions(f):
    assert fp.meromorphic(f, z) is Meromorphicity.NOT_MEROMORPHIC


@pytest.mark.parametrize("f", [sp.cos(sp.sqrt(z)), sp.sin(sp.sqrt(z)) ** 2])
def test_meromorphic_branch_cancellation(f):
    result = fp.meromorphic(f, z, return_result=True)
    assert result.primary is Meromorphicity.MEROMORPHIC
    assert result.source == "entire-even-series"
    assert fp.verify_certificate(result.evidence[0])


@pytest.mark.parametrize(
    "f",
    [
        sp.exp(sp.Abs(z)),
        sp.sin(sp.re(z)),
        sp.gamma(sp.Abs(z) + 1),
        sp.exp(sp.conjugate(z)),
    ],
)
def test_outer_entire_or_meromorphic_head_needs_holomorphic_argument(f):
    assert fp.analytic(f, z, domain=sp.S.Complexes) is Analyticity.UNKNOWN


@pytest.mark.parametrize(
    "f",
    [
        sp.re(z) + sp.I * sp.im(z),
        sp.sin(sp.re(z) + sp.I * sp.im(z)),
        z * sp.conjugate(z) - sp.Abs(z) ** 2,
    ],
)
def test_exact_complex_identities_are_checked_on_whole_defined_source(f):
    assert fp.analytic(f, z, domain=sp.S.Complexes) is Analyticity.ANALYTIC
    assert fp.meromorphic(f, z) is Meromorphicity.MEROMORPHIC


@pytest.mark.parametrize(
    "D", [x < 0, sp.Interval(-2, -1), sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2))]
)
def test_recursive_analyticity_preserves_requested_domain(D):
    assert fp.analytic(-sp.Abs(x), x, domain=D) is Analyticity.ANALYTIC
    assert fp.continuous(-sp.Abs(x), x, domain=D) is Continuity.CONTINUOUS
    assert fp.smoothness(-sp.Abs(x), x, domain=D) == sp.oo


@pytest.mark.parametrize(
    "f",
    [
        sp.sin(sp.Abs(x)) ** 2,
        sp.Piecewise((-sp.Abs(x), x < 0), (x, True)),
        sp.Piecewise((sp.sign(x), x < 0), (-1, True)),
        sp.Piecewise((x, sp.Ne(x, 0)), (0, True)),
    ],
)
def test_analytic_whole_function_despite_nonsmooth_children_or_seams(f):
    assert fp.analytic(f, x) is Analyticity.ANALYTIC
    assert fp.continuous(f, x) is Continuity.CONTINUOUS
    result = fp.smoothness(f, x, return_result=True)
    assert result.smooth is True and result.differentiability_order is sp.oo


@pytest.mark.parametrize("f", [x * sp.sign(x), x * x * sp.sign(x)])
def test_vanishing_factor_removes_inner_jump(f):
    assert fp.continuous(f, x) is Continuity.CONTINUOUS
    assert fp.discontinuities(f, x) is sp.S.false
    assert discontinuity_at(f, x, sp.S.Zero) is False


def test_unresolved_discontinuity_candidates():
    f = sp.sin(x) * sp.sign(x)
    assert fp.continuous(f, x) is Continuity.CONTINUOUS
    records = fp.discontinuities(f, x, return_result=True)
    assert not records
    assert discontinuity_at(f, x, sp.S.Zero) is False


def test_joint_variable_power_at_zero_has_no_continuity_theorem():
    f = (x + y) ** (x - y)
    t = sp.Symbol("t", positive=True)
    assert f.subs({x: t, y: t}, simultaneous=True) == 1
    assert f.subs({x: t, y: -t}, simultaneous=True) == 0
    assert f.subs({x: 0, y: 0}, simultaneous=True) == 1
    assert fp.continuous(f, (x, y)) is Continuity.UNKNOWN
    assert fp.continuous(x**y, (x, y)) is Continuity.UNKNOWN
    assert fp.continuous((x * x + y * y + 1) ** y, (x, y)) is Continuity.CONTINUOUS
    assert fp.continuous(sp.sqrt(x * x + y * y), (x, y)) is Continuity.CONTINUOUS


def test_unproved_piecewise_derivative_limit_is_not_a_failure_witness():
    from funcprops.real_analysis.piecewise import (
        PiecewiseBoundary,
        PiecewiseBoundaryCertificate,
    )

    c = PiecewiseBoundaryCertificate(
        PiecewiseBoundary(0, 0, 1, 1), 0, 0, 0, ((1, 1), (None, 0)), True, 1, True
    )
    assert not piecewise_failure_witness(c)
    assert piecewise_failure_witness(replace(c, derivative_limits=((1, 1), (-1, 1))))


@pytest.mark.parametrize("f", [sp.oo, -sp.oo, sp.zoo, sp.nan])
def test_nonfinite_constants_are_not_regular_functions(f):
    assert fp.analytic(f, x) is Analyticity.UNKNOWN
    assert fp.continuous(f, x) is Continuity.UNKNOWN
    assert fp.meromorphic(f, z) is Meromorphicity.UNKNOWN


def test_definition_holes_and_genuine_negative_evidence_are_retained():
    raw = sp.Mul(sp.S.Zero, sp.Pow(x, -1, evaluate=False), sp.Abs(x), evaluate=False)
    assert regularity_normal_form(raw, x, sp.S.Reals) == raw
    assert fp.analytic(sp.Abs(x), x) is Analyticity.NOT_ANALYTIC
    assert fp.analytic(sp.Abs(x) + y, (x, y)) is Analyticity.NOT_ANALYTIC
    assert fp.analytic(sp.sqrt(x), x) is Analyticity.NOT_ANALYTIC
    assert fp.continuous(sp.floor(x), x) is Continuity.DISCONTINUOUS
    kink = sp.Piecewise((-x, x < 0), (x, True))
    assert fp.smoothness(kink, x, return_result=True).smooth is False
    assert fp.analytic(kink, x) is Analyticity.NOT_ANALYTIC


def test_regularization_cache_obeys_public_cache_lifecycle():
    fp.clear_caches()
    assert fp.cache_info()["regularity_normal_form"].currsize == 0
    fp.analytic(sp.sin(sp.Abs(x)) ** 2, x)
    assert fp.cache_info()["regularity_normal_form"].currsize > 0
    fp.clear_caches()
    assert fp.cache_info()["regularity_normal_form"].currsize == 0


@pytest.mark.parametrize("variables", [x, (x, y)])
def test_nonfinite_source_factors(variables):
    raw = sp.Mul(0, sp.oo, x, evaluate=False)
    assert fp.analytic(raw, variables) is Analyticity.UNKNOWN
    assert fp.continuous(raw, variables) is Continuity.UNKNOWN
    assert fp.meromorphic(raw, x) is Meromorphicity.UNKNOWN


def test_accumulation_bounds_do_not_certify_a_piecewise_limit_or_jet():
    from funcprops.real_analysis.piecewise import (
        certify_piecewise_boundaries,
        piecewise_decomposition,
    )

    f = sp.Piecewise((sp.sin(1 / x), sp.Ne(x, 0)), (0, True))
    certificates = certify_piecewise_boundaries(
        piecewise_decomposition(f, x), max_order=2
    )
    assert certificates and all(c.continuous is None for c in certificates)
    assert all(not piecewise_failure_witness(c) for c in certificates)
    assert discontinuity_at(f, x, sp.S.Zero) is None


@pytest.mark.parametrize("f", [sp.Abs(sp.floor(x)), sp.Abs(sp.ceiling(x))])
def test_absolute_value_continuity_premises(f):
    assert fp.continuous(f, x) is not Continuity.CONTINUOUS
    assert fp.analytic(f, x) is not Analyticity.ANALYTIC


def test_degenerate_meromorphic_composition():
    u = sp.Add(-1, sp.Mul(0, z, evaluate=False), evaluate=False)
    raw = sp.gamma(u, evaluate=False)
    assert raw.subs(z, 0) is sp.zoo
    assert fp.meromorphic(raw, z) is Meromorphicity.UNKNOWN
    assert fp.analytic(raw, z, domain=sp.S.Complexes) is Analyticity.UNKNOWN
    a = sp.Symbol("a", real=True)
    assert fp.meromorphic(sp.gamma(a * z - 1), z) is Meromorphicity.UNKNOWN
    assert fp.meromorphic(sp.gamma(z * z + a), z) is Meromorphicity.MEROMORPHIC
    assert fp.meromorphic(sp.gamma(sp.sin(z)), z) is Meromorphicity.MEROMORPHIC


def test_fixed_argument_parameters():
    j = sp.Symbol("j", integer=True)
    assert fp.meromorphic(sp.besselj(j, j), j) is not Meromorphicity.MEROMORPHIC
    assert fp.meromorphic(j**j, j) is not Meromorphicity.MEROMORPHIC
    n = sp.Symbol("n", integer=True)
    assert fp.meromorphic(sp.besselj(n, sp.sin(z)), z) is Meromorphicity.MEROMORPHIC
    assert fp.meromorphic(z**n, z) is Meromorphicity.MEROMORPHIC
