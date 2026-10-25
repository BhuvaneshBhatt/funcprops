import sympy as sp

from funcprops import (
    Convexity,
    Monotonicity,
    TruthValue,
    bijective,
    convexity,
    domain,
    injective,
    monotonicity,
    range,
    smoothness,
    surjective,
)


def test_domain_delegates_to_semialg():
    x = sp.Symbol("x", real=True)
    assert sp.simplify_logic(sp.Xor(domain(sp.sqrt(x - 1), x), x >= 1)) is sp.false


def test_range_delegates_to_semialg():
    x, y = sp.symbols("x y", real=True)
    result = range(x**2, x, y)
    # semialg may simplify y>=0 to an equivalent formula.
    assert sp.simplify(sp.Equivalent(result, y >= 0)) is sp.true


def test_convexity_uses_semialg_adapter():
    x = sp.Symbol("x", real=True)
    assert convexity(x**2, x) in {
        Convexity.CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
    }


def test_semialg_adapter_targets_public_api():
    import semialg

    from funcprops import _semialg

    x, y = sp.symbols("x y", real=True)
    assert _semialg.domain(x**2, x) == semialg.function_domain(x**2, [x])
    assert _semialg.range(x**2, x, y) == semialg.function_range(
        x**2, True, [x], value_symbol=y, method="qe"
    )
    assert _semialg.convexity(x**2, x) == semialg.function_convexity(x**2, [x])


def test_project_requires_semialg_public_api_release():
    import tomllib
    from pathlib import Path

    project_path = Path(__file__).parents[1] / "pyproject.toml"
    with project_path.open("rb") as stream:
        project = tomllib.load(stream)

    assert "semialg>=1.3.2" in project["project"]["dependencies"]


def test_monotonicity_delegates_semialgebraic_domain_to_semialg():
    x = sp.Symbol("x", real=True)
    result = monotonicity(sp.Abs(x), x, domain=x >= 0, return_result=True)
    assert result.primary is Monotonicity.STRICTLY_INCREASING


def test_smoothness_uses_semialg_for_semialgebraic_breakpoint():
    x = sp.Symbol("x", real=True)
    result = smoothness(sp.Abs(x), x, return_result=True)
    assert result.smooth is False
    assert result.differentiability_order == 0
    assert any(item[0] == "semialg" for item in result.evidence)


def test_backend_preserves_stronger_domain_proof():
    x = sp.Symbol("x", real=True)
    result = smoothness(sp.Abs(x), x, domain=x > 0, return_result=True)
    assert result.smooth is True
    assert result.differentiability_order is sp.oo
    assert result.evidence == ("analytic-implies-smooth",)


def test_mapping_properties_delegate_on_semialgebraic_domain():
    x = sp.Symbol("x", real=True)
    nonnegative = sp.Interval(0, sp.oo)
    assert injective(x**2, x, domain=x >= 0) is TruthValue.TRUE
    assert surjective(x**2, x, domain=x >= 0, codomain=nonnegative) is TruthValue.TRUE
    assert bijective(x, x, domain=x >= 0, codomain=nonnegative) is TruthValue.TRUE


def test_updated_semialg_public_backend_surface():
    import semialg

    from funcprops import _semialg

    x = sp.Symbol("x", real=True)
    assert _semialg.monotonicity(x**3, x) == semialg.function_monotonicity(x**3, x)
    smooth = _semialg.smoothness(sp.Abs(x), x)
    assert smooth == semialg.function_smoothness(sp.Abs(x), x)
    mapping = _semialg.function_mapping_properties(x**2, x, domain=x >= 0)
    expected = semialg.function_mapping_properties(x**2, x, domain=x >= 0)
    assert mapping.injective == expected.injective
    assert mapping.surjective == expected.surjective
    assert mapping.bijective == expected.bijective
