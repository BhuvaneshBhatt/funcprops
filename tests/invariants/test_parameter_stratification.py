import sympy as sp
from sympy import S

import funcprops as fp
from funcprops.real_analysis.range import _sympy_range
from funcprops.results import (
    Boundedness,
    Convexity,
    Monotonicity,
    PropertyResult,
    Sign,
    TruthValue,
)
from funcprops.stratification import exact_set_equal
from funcprops.transcendental.analytic import holomorphic_on_rectangle
from funcprops.transcendental.periodic import PeriodicSet
from funcprops.transcendental.reduce import reduce_univariate_condition


def _case_map(result):
    assert isinstance(result, PropertyResult)
    return {c.value: sp.simplify(c.condition) for c in result.cases}


def test_parameter_sign_range_boundedness_and_injectivity_propagate():
    x, a, y = sp.symbols("x a y", real=True)
    sign = _case_map(fp.sign(a * x, x, domain=x > 0, return_result=True))
    assert sign[Sign.POSITIVE] == (a > 0)
    assert sign[Sign.ZERO] == sp.Eq(a, 0)
    assert sign[Sign.NEGATIVE] == (a < 0)

    rng = _case_map(fp.range(a * x, x, y, constraints=x > 0, return_result=True))
    assert rng[y > 0] == (a > 0)
    assert rng[sp.Eq(y, 0)] == sp.Eq(a, 0)
    assert rng[y < 0] == (a < 0)

    bnd = _case_map(fp.boundedness(a * x, x, domain=x > 0, return_result=True))
    assert bnd[Boundedness.BOUNDED_BELOW] == (a > 0)
    assert bnd[Boundedness.BOUNDED] == sp.Eq(a, 0)
    assert bnd[Boundedness.BOUNDED_ABOVE] == (a < 0)

    inj = _case_map(fp.injective(a * x, x, domain=x > 0, return_result=True))
    assert inj[TruthValue.TRUE] == sp.Ne(a, 0)
    assert inj[TruthValue.FALSE] == sp.Eq(a, 0)


def test_exp_affine_parameter_strata_reach_mapping_properties():
    x, a, y = sp.symbols("x a y", real=True)
    rng = _case_map(fp.range(sp.exp(a * x), x, y, return_result=True))
    assert rng[y > 0] == sp.Ne(a, 0)
    assert rng[sp.Eq(y, 1)] == sp.Eq(a, 0)
    surj = _case_map(
        fp.surjective(
            sp.exp(a * x), x, codomain=sp.Interval.open(0, sp.oo), return_result=True
        )
    )
    assert surj[TruthValue.TRUE] == sp.Ne(a, 0)
    assert surj[TruthValue.FALSE] == sp.Eq(a, 0)
    bij = _case_map(
        fp.bijective(
            sp.exp(a * x), x, codomain=sp.Interval.open(0, sp.oo), return_result=True
        )
    )
    assert bij[TruthValue.TRUE] == sp.Ne(a, 0)
    assert bij[TruthValue.FALSE] == sp.Eq(a, 0)


def test_special_function_order_and_shape_strata():
    x, a, y = sp.symbols("x a y", real=True)
    nu = sp.Symbol("nu")
    ksign = _case_map(fp.sign(sp.besselk(nu, x), x, domain=x > 0, return_result=True))
    assert ksign[Sign.POSITIVE] == sp.Contains(nu, S.Reals)
    kmono = _case_map(
        fp.monotonicity(sp.besselk(nu, x), x, domain=x > 0, return_result=True)
    )
    assert kmono[Monotonicity.STRICTLY_DECREASING] == sp.Contains(nu, S.Reals)
    krange = _case_map(
        fp.range(sp.besselk(nu, x), x, y, constraints=x > 0, return_result=True)
    )
    assert krange[y > 0] == sp.Contains(nu, S.Reals)

    bsign = _case_map(fp.sign(sp.beta(a, x), x, domain=x > 0, return_result=True))
    assert bsign[Sign.POSITIVE] == (a > 0)
    bmono = _case_map(
        fp.monotonicity(sp.beta(a, x), x, domain=x > 0, return_result=True)
    )
    assert bmono[Monotonicity.STRICTLY_DECREASING] == (a > 0)
    bconv = _case_map(fp.convexity(sp.beta(a, x), x, domain=x > 0, return_result=True))
    assert bconv[Convexity.STRICTLY_CONVEX] == (a > 0)
    brange = _case_map(
        fp.range(sp.beta(a, x), x, y, constraints=x > 0, return_result=True)
    )
    assert brange[y > 0] == (a > 0)


def test_polygamma_order_parity_sign_strata():
    x = sp.symbols("x", real=True)
    n = sp.Symbol("n", integer=True, nonnegative=True)
    r = fp.sign(sp.polygamma(n, x), x, domain=x > 0, return_result=True)
    cases = _case_map(r)
    assert Sign.POSITIVE in cases and Sign.NEGATIVE in cases
    assert cases[Sign.POSITIVE].subs(n, 1) is S.true
    assert cases[Sign.NEGATIVE].subs(n, 2) is S.true


def test_symbolic_set_nonidentity_is_not_automatically_false():
    x = sp.symbols("x", real=True)
    a = sp.Symbol("a", real=True)
    A = sp.ConditionSet(x, x > a, S.Reals)
    B = sp.Interval.open(0, sp.oo)
    assert exact_set_equal(A, B) is TruthValue.UNKNOWN


def test_periodic_affine_pullback_handles_large_translation_exactly():
    x = sp.symbols("x", real=True)
    p = PeriodicSet(sp.FiniteSet(0), 2 * sp.pi, x)
    q = p.affine_pullback(2, 100 * sp.pi, x)
    assert sp.simplify(q.period - sp.pi) == 0
    assert q.base == sp.FiniteSet(0)
    assert q.contains(0) is S.true


def test_holomorphic_tristate_does_not_turn_unknown_into_false():
    z = sp.Symbol("z")
    r = holomorphic_on_rectangle(sp.exp(sp.gamma(z)), z, (1 - sp.I / 10, 2 + sp.I / 10))
    assert r.holomorphic is None
    assert (
        holomorphic_on_rectangle(
            sp.log(z), z, (-1 - sp.I / 10, 1 + sp.I / 10)
        ).holomorphic
        is False
    )
    assert (
        holomorphic_on_rectangle(
            sp.log(z + 2), z, (-1 - sp.I / 10, 1 + sp.I / 10)
        ).holomorphic
        is True
    )


def test_sympy_range_result_containing_input_variable_is_rejected():
    x, nu, y = sp.symbols("x nu y")
    # SymPy currently returns {besselk(nu, x)} here; that is not a range.
    assert _sympy_range(sp.besselk(nu, x), x, y, x > 0) is None


def test_reducer_does_not_claim_singularity_completeness_after_failure():
    x = sp.symbols("x", real=True)
    r = reduce_univariate_condition(sp.gamma(x) > 0, x, sp.Interval(-2, 2))
    assert r.complete is False


def test_restricted_nonsmooth_functions_can_be_analytic_and_smooth():
    x = sp.symbols("x", real=True)
    assert fp.analytic(sp.Abs(x), x) == fp.Analyticity.NOT_ANALYTIC
    assert fp.analytic(sp.Abs(x), x, domain=x > 0) == fp.Analyticity.ANALYTIC
    s = fp.smoothness(sp.Abs(x), x, domain=x > 0, return_result=True)
    assert s.analytic == fp.Analyticity.ANALYTIC
    assert s.smooth is True
    assert s.differentiability_order is sp.oo
    assert s.exceptional_loci == ()
