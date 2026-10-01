import sympy as sp

from funcprops.certified_optimization import certify_global_minimum
from funcprops.parameter_discriminants import polynomial_transition_locus
from funcprops.results import Monotonicity, Sign
from funcprops.special_theorems import executable_special_theorems


def test_guarded_special_facts():
    x = sp.symbols("x", real=True)
    nu = sp.symbols("nu", real=True)
    fs = executable_special_theorems(sp.besselk(nu, x), x)
    assert any(t.property == "sign" and t.value is Sign.POSITIVE for t in fs)
    assert not next(t for t in fs if t.property == "sign").applicable(sp.S.true)
    assert next(t for t in fs if t.property == "sign").applicable(
        sp.And(x > 0, nu >= 0)
    )
    assert (
        next(
            t
            for t in executable_special_theorems(sp.erf(x), x)
            if t.property == "monotonicity"
        ).value
        is Monotonicity.STRICTLY_INCREASING
    )


def test_global_minimum_nonconstant_second_derivative():
    x = sp.symbols("x", real=True)
    c = certify_global_minimum(x**4 + x**2, x)
    assert c is not None and c.point == 0 and c.unique and c.verify()


def test_polynomial_transition_locus():
    x, a, b = sp.symbols("x a b", real=True)
    c = polynomial_transition_locus(x**3 + a * x + b, x)
    assert c is not None and c.verify()
    assert sp.simplify(c.locus / (-4 * a**3 - 27 * b**2)) in (1, -1)
