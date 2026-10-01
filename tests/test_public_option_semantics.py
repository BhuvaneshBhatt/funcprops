import sympy as sp

from funcprops import monotonicity, sign
from funcprops.branchcuts import branch_cut_conditions
from funcprops.real_analysis.structural_properties import (
    periodicity as periodicity,
)
from funcprops.results import Monotonicity, Periodicity, PropertyResult, Sign


def test_monotonicity_weakens_strict_results():
    x = sp.symbols("x", real=True)
    assert monotonicity(x, x, strict_inequalities=False) is Monotonicity.NONDECREASING
    assert monotonicity(-x, x, strict_inequalities=False) is Monotonicity.NONINCREASING


def test_monotonicity_all_properties_reports_implications():
    x = sp.symbols("x", real=True)
    result = monotonicity(x, x, all_properties=True, return_result=True)
    assert isinstance(result, PropertyResult)
    assert result.primary is Monotonicity.STRICTLY_INCREASING
    assert result.all_properties == (Monotonicity.NONDECREASING,)

    constant = monotonicity(sp.Integer(3), x, all_properties=True, return_result=True)
    assert constant.primary is Monotonicity.CONSTANT
    assert set(constant.all_properties) == {
        Monotonicity.NONDECREASING,
        Monotonicity.NONINCREASING,
    }


def test_sign_all_properties_reports_weak_implications():
    x = sp.symbols("x", real=True)
    result = sign(sp.exp(x), x, all_properties=True, return_result=True)
    assert isinstance(result, PropertyResult)
    assert result.primary is Sign.POSITIVE
    assert result.all_properties == (Sign.NONNEGATIVE,)

    zero = sign(sp.Integer(0), x, all_properties=True, return_result=True)
    assert zero.primary is Sign.ZERO
    assert set(zero.all_properties) == {Sign.NONNEGATIVE, Sign.NONPOSITIVE}


def test_periodicity_uses_parameter_assumptions():
    x, a = sp.symbols("x a", real=True)
    constant = periodicity(
        sp.sin(a * x), x, assumptions=sp.Eq(a, 0), return_result=True
    )
    assert constant.classification is Periodicity.CONSTANT
    assert constant.period is None

    periodic = periodicity(
        sp.sin(a * x), x, assumptions=sp.Ne(a, 0), return_result=True
    )
    assert periodic.classification is Periodicity.PERIODIC
    assert periodic.conditions is sp.S.true
    assert sp.simplify(periodic.period - 2 * sp.pi / sp.Abs(a)) == 0


def test_branch_cut_conditions_use_assumptions():
    x = sp.symbols("x", real=True)
    assert branch_cut_conditions(sp.log(x), x) == (x < 0,)
    assert branch_cut_conditions(sp.log(x), x, assumptions=x > 0) == ()
