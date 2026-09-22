import sympy as sp

import funcprops as fp


def test_branchcuts_conditional_expression_restricts_cut():
    z = sp.symbols("z")
    expr = fp.ConditionalExpression(sp.log(z), sp.re(z) > 0)
    assert fp.function_branchcuts(expr, z) == ()


def test_nested_conditional_expression_conditions_are_conjoined():
    x = sp.symbols("x", real=True)
    expr = fp.ConditionalExpression(fp.ConditionalExpression(x, x > -2), x < 2)
    assert fp.function_sign(expr, x, domain=x > 0) is fp.Sign.POSITIVE


def test_conditional_expression_restricts_zero_query_domain():
    x = sp.symbols("x", real=True)
    expr = fp.ConditionalExpression((x - 1) * (x + 1), x > 0)
    assert fp.function_zeros(expr, x) == sp.FiniteSet(1)


def test_conditional_expression_restricts_natural_domain_result():
    x = sp.symbols("x", real=True)
    expr = fp.ConditionalExpression(1 / (x - 1), x > 0)
    result = fp.function_domain(expr, x)
    assert sp.simplify(sp.Equivalent(result, sp.And(x > 0, sp.Ne(x, 1)))) is sp.S.true
