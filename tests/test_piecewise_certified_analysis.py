import sympy as sp

import funcprops as fp

x, y = sp.symbols("x y", real=True)


def test_effective_conditions_respect_semantics():
    expr = sp.Piecewise((x, x < 1), (2 * x, x < 3), (3 * x, True))
    dec = fp.piecewise_decomposition(expr, x)
    assert dec.complete
    assert tuple(b.domain for b in dec.branches) == (
        sp.Interval.open(-sp.oo, 1),
        sp.Interval.Ropen(1, 3),
        sp.Interval(3, sp.oo),
    )
    assert tuple(b.source_index for b in dec.branches) == (0, 1, 2)


def test_boundary_ownership_captures_isolated_value():
    expr = sp.Piecewise((x, x < 0), (100, sp.Eq(x, 0)), (x, True))
    dec = fp.piecewise_decomposition(expr, x)
    assert dec.boundaries == (fp.PiecewiseBoundary(0, 0, 2, 1),)
    (cert,) = fp.certify_piecewise_boundaries(dec, max_order=1)
    assert cert.value == 100
    assert cert.left_limit == cert.right_limit == 0
    assert cert.continuous is False
    assert fp.continuous(expr, x) is fp.Continuity.DISCONTINUOUS
    assert fp.monotonicity(expr, x) is fp.Monotonicity.NOT_MONOTONE


def test_piecewise_derivative_seam_certifies():
    expr = sp.Piecewise((-x, x < 0), (x, True))
    (cert,) = fp.certify_piecewise_boundaries(
        fp.piecewise_decomposition(expr, x), max_order=2
    )
    assert cert.continuous is True
    assert cert.derivative_limits[0] == (-1, 1)
    assert cert.differentiability_order == 0
    assert fp.differentiability(expr, x) is fp.Differentiability.NOT_DIFFERENTIABLE
    detailed = fp.smoothness(expr, x, return_result=True)
    assert detailed.smooth is False
    assert detailed.differentiability_order == 0


def test_seam_smoothness():
    expr = sp.Piecewise((x**2, x < 0), (x**2, True), evaluate=False)
    detailed = fp.smoothness(expr, x, return_result=True)
    assert detailed.smooth is True
    assert detailed.differentiability_order is sp.oo


def test_piecewise_zero_sets_merged_branch_domains():
    expr = sp.Piecewise((x + 1, x < 0), (x - 2, True))
    assert fp.zeros(expr, x) == sp.FiniteSet(-1, 2)


def test_piecewise_range_images_endpoint_ownership():
    expr = sp.Piecewise((x, x < 0), (100, sp.Eq(x, 0)), (x + 2, True))
    result = fp.range(expr, x, y)
    expected = (y < 0) | sp.Eq(y, 100) | (y > 2)
    assert sp.simplify_logic(sp.Equivalent(result, expected)) is sp.S.true


def test_piecewise_convexity_checks_boundary_slope():
    upward = sp.Piecewise((x, x < 0), (2 * x, True))
    bad_value = sp.Piecewise((x, x < 0), (100, sp.Eq(x, 0)), (2 * x, True))
    bad_slope = sp.Piecewise((2 * x, x < 0), (x, True))
    assert fp.convexity(upward, x) is fp.Convexity.CONVEX
    assert fp.convexity(bad_value, x) is fp.Convexity.NEITHER
    assert fp.convexity(bad_slope, x) is fp.Convexity.NEITHER


def test_cached_derivative_coordinate():
    from funcprops.proof_cache import cached_derivative

    assert cached_derivative(x, x) == 1
