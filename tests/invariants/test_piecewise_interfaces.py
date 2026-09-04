"""Global piecewise properties must respect branch interfaces."""

import sympy as sp

import funcprops as fp

x = sp.symbols("x", real=True)


def test_compatible_increasing_branches_combine_globally():
    expr = sp.Piecewise((x, x < 0), (2 * x, True))
    assert fp.function_monotonicity(expr, x) is fp.Monotonicity.NONDECREASING
    assert fp.function_convexity(expr, x) is fp.Convexity.CONVEX
    assert fp.function_continuous(expr, x) is fp.Continuity.CONTINUOUS


def test_downward_jump_blocks_global_monotonicity_and_convexity():
    expr = sp.Piecewise((x, x < 0), (x - 1, True))
    assert fp.function_monotonicity(expr, x) is fp.Monotonicity.NOT_MONOTONE
    assert fp.function_convexity(expr, x) is fp.Convexity.NEITHER
    assert fp.function_continuous(expr, x) is fp.Continuity.DISCONTINUOUS


def test_downward_slope_jump_blocks_convexity_even_when_continuous():
    expr = sp.Piecewise((2 * x, x < 0), (x, True))
    assert fp.function_continuous(expr, x) is fp.Continuity.CONTINUOUS
    assert fp.function_convexity(expr, x) is fp.Convexity.NEITHER
