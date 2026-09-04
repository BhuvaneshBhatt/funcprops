import sympy as sp

from funcprops import (
    Convexity,
    Monotonicity,
    TruthValue,
    function_bijective,
    function_convexity,
    function_domain,
    function_injective,
    function_monotonicity,
    function_range,
    function_smoothness,
    function_surjective,
)


def test_domain_delegates_to_semialg():
    x = sp.Symbol("x", real=True)
    assert (
        sp.simplify_logic(sp.Xor(function_domain(sp.sqrt(x - 1), x), x >= 1))
        is sp.false
    )


def test_range_delegates_to_semialg():
    x, y = sp.symbols("x y", real=True)
    result = function_range(x**2, x, y)
    # semialg may simplify y>=0 to an equivalent formula.
    assert sp.simplify(sp.Equivalent(result, y >= 0)) is sp.true


def test_convexity_uses_semialg_adapter():
    x = sp.Symbol("x", real=True)
    assert function_convexity(x**2, x) in {
        Convexity.CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
    }


def test_semialg_adapter_targets_public_api():
    import semialg

    from funcprops import _semialg

    x, y = sp.symbols("x y", real=True)
    assert _semialg.function_domain(x**2, x) == semialg.function_domain(x**2, [x])
    assert _semialg.function_range(x**2, x, y) == semialg.function_range(
        x**2, True, [x], value_symbol=y, method="qe"
    )
    assert _semialg.function_convexity(x**2, x) == semialg.function_convexity(x**2, [x])


def test_project_requires_semialg_public_api_release():
    from pathlib import Path

    project = (Path(__file__).parents[1] / "pyproject.toml").read_text()
    assert '"semialg>=1.0.0"' in project


def test_monotonicity_delegates_semialgebraic_domain_to_semialg():
    x = sp.Symbol("x", real=True)
    result = function_monotonicity(sp.Abs(x), x, domain=x >= 0, details=True)
    assert result.primary is Monotonicity.STRICTLY_INCREASING


def test_smoothness_uses_semialg_for_semialgebraic_breakpoint():
    x = sp.Symbol("x", real=True)
    result = function_smoothness(sp.Abs(x), x)
    assert result.smooth is False
    assert result.differentiability_order == 0
    assert any(item[0] == "semialg" for item in result.evidence)


def test_stronger_funcprops_regular_domain_proof_is_not_weakened_by_backend():
    x = sp.Symbol("x", real=True)
    result = function_smoothness(sp.Abs(x), x, domain=x > 0)
    assert result.smooth is True
    assert result.differentiability_order is sp.oo
    assert result.evidence == ("analytic-implies-smooth",)


def test_mapping_properties_delegate_on_semialgebraic_domain():
    x = sp.Symbol("x", real=True)
    nonnegative = sp.Interval(0, sp.oo)
    assert function_injective(x**2, x, domain=x >= 0) is TruthValue.TRUE
    assert (
        function_surjective(x**2, x, domain=x >= 0, codomain=nonnegative)
        is TruthValue.TRUE
    )
    assert (
        function_bijective(x, x, domain=x >= 0, codomain=nonnegative) is TruthValue.TRUE
    )


def test_updated_semialg_public_backend_surface():
    import semialg

    from funcprops import _semialg

    x = sp.Symbol("x", real=True)
    assert _semialg.function_monotonicity(x**3, x) == semialg.function_monotonicity(
        x**3, x
    )
    smooth = _semialg.function_smoothness(sp.Abs(x), x)
    assert smooth == semialg.function_smoothness(sp.Abs(x), x)
    mapping = _semialg.function_mapping_properties(x**2, x, domain=x >= 0)
    expected = semialg.function_mapping_properties(x**2, x, domain=x >= 0)
    assert mapping.injective == expected.injective
    assert mapping.surjective == expected.surjective
    assert mapping.bijective == expected.bijective
