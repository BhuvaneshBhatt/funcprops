"""Cross-property implication laws that every proof path must respect."""

import sympy as sp

import funcprops as fp
from funcprops.results import PropertyResult

x = sp.symbols("x", real=True)


def test_analytic_implies_smooth_differentiable_and_continuous():
    for expr in (sp.exp(x), sp.sin(x), x**4 + x + 1):
        assert fp.function_analytic(expr, x) is fp.Analyticity.ANALYTIC
        assert fp.function_smoothness(expr, x, return_result=True).smooth is True
        assert fp.function_differentiability(expr, x) is fp.Differentiability.SMOOTH
        assert fp.function_continuous(expr, x) is fp.Continuity.CONTINUOUS


def test_strong_convexity_reports_strict_and_ordinary_implications():
    result = fp.function_convexity(x**2, x, all_properties=True)
    assert isinstance(result, PropertyResult)
    assert result.primary is fp.Convexity.STRONGLY_CONVEX
    assert result.all_properties == (
        fp.Convexity.STRICTLY_CONVEX,
        fp.Convexity.CONVEX,
    )


def test_strict_monotonicity_implies_injectivity():
    for expr in (x, x**3, sp.exp(x), -sp.exp(x)):
        mono = fp.function_monotonicity(expr, x)
        assert mono in {
            fp.Monotonicity.STRICTLY_INCREASING,
            fp.Monotonicity.STRICTLY_DECREASING,
        }
        assert fp.function_injective(expr, x) is fp.TruthValue.TRUE


def test_bijectivity_requires_both_mapping_properties():
    for expr in (x, x**3):
        assert fp.function_bijective(expr, x) is fp.TruthValue.TRUE
        assert fp.function_injective(expr, x) is fp.TruthValue.TRUE
        assert fp.function_surjective(expr, x) is fp.TruthValue.TRUE


def test_exact_range_and_boundedness_agree():
    y = sp.symbols("y", real=True)
    assert fp.function_range(sp.sin(x), x, y) == ((y >= -1) & (y <= 1))
    assert fp.function_boundedness(sp.sin(x), x) is fp.Boundedness.BOUNDED
