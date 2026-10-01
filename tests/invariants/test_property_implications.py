"""Cross-property implication laws that every proof path must respect."""

import sympy as sp

import funcprops as fp
from funcprops.results import PropertyResult

x = sp.symbols("x", real=True)


def test_analytic_implies_smooth_differentiable_and_continuous():
    for expr in (sp.exp(x), sp.sin(x), x**4 + x + 1):
        assert fp.analytic(expr, x) is fp.Analyticity.ANALYTIC
        assert fp.smoothness(expr, x, return_result=True).smooth is True
        assert fp.differentiability(expr, x) is fp.Differentiability.SMOOTH
        assert fp.continuous(expr, x) is fp.Continuity.CONTINUOUS


def test_strong_convexity_reports_strict_and_ordinary_implications():
    result = fp.convexity(x**2, x, all_properties=True, return_result=True)
    assert isinstance(result, PropertyResult)
    assert result.primary is fp.Convexity.STRONGLY_CONVEX
    assert result.all_properties == (
        fp.Convexity.STRICTLY_CONVEX,
        fp.Convexity.CONVEX,
    )


def test_strict_monotonicity_implies_injectivity():
    for expr in (x, x**3, sp.exp(x), -sp.exp(x)):
        mono = fp.monotonicity(expr, x)
        assert mono in {
            fp.Monotonicity.STRICTLY_INCREASING,
            fp.Monotonicity.STRICTLY_DECREASING,
        }
        assert fp.injective(expr, x) is fp.TruthValue.TRUE


def test_bijectivity_requires_both_mapping_properties():
    for expr in (x, x**3):
        assert fp.bijective(expr, x) is fp.TruthValue.TRUE
        assert fp.injective(expr, x) is fp.TruthValue.TRUE
        assert fp.surjective(expr, x) is fp.TruthValue.TRUE


def test_exact_range_and_boundedness_agree():
    y = sp.symbols("y", real=True)
    assert fp.range(sp.sin(x), x, y) == ((y >= -1) & (y <= 1))
    assert fp.boundedness(sp.sin(x), x) is fp.Boundedness.BOUNDED
