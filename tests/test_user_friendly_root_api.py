import inspect

import pytest
import sympy as sp

import funcprops as fp
from funcprops.results import DetailedPropertyResult, PropertyResult

PROPERTY_NAMES = (
    "analytic",
    "bijective",
    "boundary_behavior",
    "boundedness",
    "branch_cuts",
    "branch_points",
    "change_of_variables",
    "complete_monotonicity",
    "complex_zeros",
    "continuous",
    "convexity",
    "determinant_nonvanishing",
    "differentiability",
    "discontinuities",
    "domain",
    "geometry",
    "homogeneity",
    "injective",
    "jacobian",
    "level_boundedness",
    "local_invertibility",
    "meromorphic",
    "mode_existence",
    "monotonicity",
    "oscillation",
    "periodicity",
    "poles",
    "range",
    "sign",
    "singularities",
    "singularity_analysis",
    "smoothness",
    "surjective",
    "symmetry",
    "transformation_geometry",
    "zeros",
)


def test_public_property_signatures():
    for name in PROPERTY_NAMES:
        signature = inspect.signature(getattr(fp, name))
        assert "return_result" in signature.parameters, name
        assert "var" not in signature.parameters, name
        assert "vars" not in signature.parameters, name


def test_scalar_keyword_is_variable():
    x = sp.symbols("x", real=True)
    assert fp.domain(x**2, variable=x) is sp.S.true
    assert fp.zeros(x**2 - 1, variable=x) == sp.FiniteSet(-1, 1)


def test_non_native_detailed_result_is_available_consistently():
    x = sp.symbols("x", real=True)
    detail = fp.domain(sp.sqrt(x), x, return_result=True)
    assert isinstance(detail, DetailedPropertyResult)
    assert detail.primary == (x >= 0)

    mapping = fp.injective(x, x, return_result=True)
    assert isinstance(mapping, DetailedPropertyResult)


def test_property_catalog_is_discoverable_and_filterable():
    all_properties = fp.properties()
    mapping = fp.properties(category="mapping")
    assert any(name == "convexity" for name, _, _ in all_properties)
    assert {name for name, _, _ in mapping} == {"injective", "surjective", "bijective"}
    with pytest.raises(ValueError, match="unknown property category"):
        fp.properties(category="not-a-category")


def test_parameter_strata_have_readable_text_and_html():
    a = sp.symbols("a", real=True)
    x = sp.symbols("x", real=True)
    result = fp.injective(a * x, x, return_result=True)
    assert isinstance(result, PropertyResult)
    text = str(result)
    assert "->" in text
    assert "<table>" in result._repr_html_()
    explanation = fp.explain_result(result)
    assert "Cases:" in explanation


def test_multiple_variables_get_actionable_scalar_error():
    x, y = sp.symbols("x y", real=True)
    with pytest.raises(TypeError, match="expected one analysis variable"):
        fp.monotonicity(x + y, (x, y))


def test_guarded_result_projection():
    a, x = sp.symbols("a x", real=True)
    compact = fp.injective(a * x, x)
    assert isinstance(compact, sp.Piecewise)
    assert compact == sp.Piecewise((sp.S.true, sp.Ne(a, 0)), (sp.S.false, True))
    rich = fp.injective(a * x, x, return_result=True)
    assert isinstance(rich, PropertyResult)
    assert rich.as_piecewise() == compact


def test_partial_property_strata_keep_explicit_unknown_fallback():
    a, b, x = sp.symbols("a b x")
    compact = fp.sign(sp.exp(a * x + b), x)
    assert isinstance(compact, sp.Piecewise)
    assert compact.args[-1].expr == sp.Symbol("unknown")
    assert compact.args[-1].cond is sp.S.true
