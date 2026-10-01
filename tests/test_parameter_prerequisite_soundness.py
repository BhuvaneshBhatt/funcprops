import sympy as sp

import funcprops as fp
from funcprops.results import Boundedness, Convexity, Monotonicity, PropertyResult, Sign

x = sp.symbols("x", real=True)
a, b = sp.symbols("a b")
ar, br = sp.symbols("ar br", real=True)
y = sp.symbols("y", real=True)


def _conditions(result):
    assert isinstance(result, PropertyResult)
    return tuple(c.condition for c in result.cases)


def test_nonreal_affine_exponential_has_no_real_sign_or_order_certificate():
    expr = sp.exp(sp.I * x)
    assert fp.sign(expr, x) is Sign.UNKNOWN
    assert fp.monotonicity(expr, x) is Monotonicity.UNKNOWN
    assert fp.convexity(expr, x) is Convexity.UNKNOWN


def test_affine_exponential_parameter_theorems_carry_realness_guards():
    expr = sp.exp(a * x + b)
    s = fp.sign(expr, x, return_result=True)
    m = fp.monotonicity(expr, x, return_result=True)
    c = fp.convexity(expr, x, return_result=True)
    r = fp.range(expr, x, y, return_result=True)
    for result in (s, m, c, r):
        conds = _conditions(result)
        assert conds
        assert all(
            sp.simplify(sp.Implies(cond, sp.And(sp.Q.real(a), sp.Q.real(b))))
            is sp.S.true
            for cond in conds
            if not cond.has(sp.Eq(a, 0))
        )
    # The zero-slope range only needs the offset to be real.
    assert any(
        sp.simplify(sp.Implies(cond, sp.Q.real(b))) is sp.S.true
        for cond in _conditions(r)
    )


def test_real_affine_exponential_retains_existing_classifications():
    expr = sp.exp(ar * x + br)
    assert fp.sign(expr, x) is Sign.POSITIVE
    m = fp.monotonicity(expr, x, return_result=True)
    c = fp.convexity(expr, x, return_result=True)
    assert isinstance(m, PropertyResult)
    assert isinstance(c, PropertyResult)


def test_constant_parameter_sign_strata_are_guarded_by_realness():
    result = fp.sign(a, x, return_result=True)
    assert isinstance(result, PropertyResult)
    assert all(
        cond.has(sp.Q.real(a)) or cond is sp.S.false for cond in _conditions(result)
    )


def test_nonreal_power_is_not_given_a_real_sign():
    assert fp.sign(x**sp.I, x, domain=x > 0) is Sign.UNKNOWN


def test_boundedness_structural_theorems_require_real_arguments():
    for head in (sp.sin, sp.cos, sp.tanh, sp.atan):
        result = fp.boundedness(head(a * x), x, return_result=True)
        assert isinstance(result, PropertyResult)
        assert all(cond.has(sp.Q.real(a)) for cond in _conditions(result))
    assert (
        fp.boundedness(sp.sin(sp.I * x), x, return_result=True)
        is not Boundedness.BOUNDED
    )


def test_exponential_boundedness_requires_real_exponent():
    result = fp.boundedness(sp.exp(a * x + b), x, return_result=True)
    assert isinstance(result, PropertyResult)
    assert all(
        sp.simplify(sp.Implies(cond, sp.And(sp.Q.real(a), sp.Q.real(b)))) is sp.S.true
        for cond in _conditions(result)
    )
