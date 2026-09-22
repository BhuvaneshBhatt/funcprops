import sympy as sp

from funcprops import (
    Convexity,
    DetailedPropertyResult,
    Monotonicity,
    PropertyResult,
    TruthValue,
    as_detailed_result,
    function_convexity,
    function_monotonicity,
    function_range,
)
from funcprops.results import ConditionalExpression
from funcprops.stratification import stratify_boolean_by_parameters


def test_semialg_parameter_guard_satisfiability_removes_real_contradictions():
    x, a = sp.symbols("x a", real=True)
    condition = sp.Or(sp.And(a > 0, a < 0, x > 1), sp.And(a <= 0, x < 2))
    result = stratify_boolean_by_parameters(condition, x)
    assert result.cases
    assert all(
        sp.simplify_logic(case.condition) != sp.And(a > 0, a < 0)
        for case in result.cases
    )
    # No retained guard may actually be impossible over the reals.
    import semialg

    assert all(semialg.is_satisfiable(c.condition, (a,)) for c in result.cases)


def test_detailed_property_result_wraps_compact_and_property_results():
    compact = as_detailed_result(Convexity.CONVEX, domain=sp.S.Reals, source="test")
    assert isinstance(compact, DetailedPropertyResult)
    assert compact.primary is Convexity.CONVEX
    assert compact.domain is sp.S.Reals
    assert compact.source == "test"

    p = PropertyResult(
        TruthValue.TRUE,
        cases=(ConditionalExpression(TruthValue.TRUE, sp.S.true),),
        source="proof",
        evidence=("witness",),
    )
    detailed = p.as_detailed_result()
    assert detailed.primary is TruthValue.TRUE
    assert detailed.cases == p.cases
    assert detailed.source == "proof"
    assert detailed.evidence == ("witness",)


def test_staged_range_monotonicity_convexity_preserve_expected_results():
    x, y = sp.symbols("x y", real=True)
    assert function_range(x**2, x, y) == (y >= 0)
    assert function_monotonicity(x**2, x, domain=x >= 0) in {
        Monotonicity.STRICTLY_INCREASING,
        Monotonicity.NONDECREASING,
    }
    assert function_convexity(x**2, x) in {
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
    }
