import sympy as sp
from sympy import S

from funcprops.assumption_closure import close_assumptions
from funcprops.complex_certification import rouche_polynomial_circle
from funcprops.explanations import explain
from funcprops.global_multivariate import affine_global_mapping
from funcprops.parameter_cells import minimize_strata, refine_parameter_cells
from funcprops.proof_budget import ProofBudget, route_proofs
from funcprops.results import (
    ConditionalExpression,
    Monotonicity,
    PropertyResult,
    TruthValue,
)
from funcprops.theorem_closure import TheoremFact, close_theorems
from funcprops.transcendental.root_geometry import derivative_cell_root_count


def test_assumption_closure_positive_implies_real_nonzero():
    a = sp.symbols("a")
    c = close_assumptions(a > 0)
    assert c.entails(sp.Contains(a, S.Reals)) is True
    assert c.entails(sp.Ne(a, 0)) is True


def test_theorem_closure_strict_monotone_implies_injective():
    facts = close_theorems(
        [TheoremFact("monotonicity", Monotonicity.STRICTLY_INCREASING)]
    )
    assert any(f.property == "injective" and f.value is TruthValue.TRUE for f in facts)


def test_stratum_minimization_removes_implied_realness():
    a = sp.symbols("a")
    r = PropertyResult(
        None,
        (
            ConditionalExpression(
                TruthValue.TRUE, sp.And(a > 0, sp.Contains(a, S.Reals))
            ),
        ),
    )
    q = minimize_strata(r)
    assert len(q.cases) == 1
    assert sp.simplify_logic(sp.Equivalent(q.cases[0].condition, a > 0)) is S.true


def test_explanation_unknown_has_reason():
    r = PropertyResult(TruthValue.UNKNOWN, source="budget-exhausted")
    e = explain(r)
    assert "budget exhausted" in str(e)


def test_budget_is_deterministic_and_bounded():
    x = sp.symbols("x")
    b = ProofBudget(max_cost=3)
    routes, b = route_proofs(x + 1, [("structural", 1), ("semialg", 3)], budget=b)
    assert routes == ("structural",) and b.skipped == ["semialg"]


def test_affine_global_bijection_and_rank_failure():
    x, y = sp.symbols("x y")
    c = affine_global_mapping((x + y, x - y), (x, y))
    assert c.classification is TruthValue.TRUE and c.verify()
    d = affine_global_mapping((x + y, 2 * x + 2 * y), (x, y))
    assert d.classification is TruthValue.FALSE and d.verify()


def test_rouche_polynomial_circle_replays():
    z = sp.symbols("z")
    c = rouche_polynomial_circle(
        z**3 + sp.Rational(1, 10) * z + sp.Rational(1, 10), z, radius=1
    )
    assert c is not None and c.count == 3 and c.verify()


def test_derivative_cell_root_count_transcendental():
    x = sp.symbols("x", real=True)
    c = derivative_cell_root_count(sp.exp(x) - 2, x, sp.Interval(-2, 2))
    assert c is not None and c.complete and c.count == 1


def test_parameter_cell_refinement_preserves_values():
    a = sp.symbols("a")
    r = PropertyResult(
        None,
        (
            ConditionalExpression(TruthValue.TRUE, a >= 0),
            ConditionalExpression(TruthValue.FALSE, a < 0),
        ),
    )
    q = refine_parameter_cells(r, (a,), split_sign=True)
    assert {c.value for c in q.cases} == {TruthValue.TRUE, TruthValue.FALSE}


def test_argument_principle_rectangle_exact_polynomial_count():
    from funcprops.complex_certification import argument_principle_rectangle

    z = sp.symbols("z")
    c = argument_principle_rectangle(
        (z - 1) * (z**2 + 1) * (z - 5), z, -2 - 2 * sp.I, 2 + 2 * sp.I
    )
    assert c is not None and c.count == 3 and c.verify()
