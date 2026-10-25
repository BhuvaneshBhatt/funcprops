import sympy as sp
from sympy import S

from funcprops import (
    bijective,
    convexity,
    injective,
    sign,
    surjective,
)
from funcprops.results import (
    ConditionalExpression,
    Convexity,
    PropertyResult,
    Sign,
    TruthValue,
)
from funcprops.stratification import normalize_cases


def _specialize(result, symbol, value):
    assert isinstance(result, PropertyResult)
    matches = []
    for case in result.cases:
        cond = sp.simplify(case.condition.subs(symbol, value))
        if cond is S.true:
            matches.append(case.value)
    assert len(matches) == 1
    return matches[0]


def test_nonsemialgebraic_domain_is_not_sent_to_semialg_sign_backend():
    x = sp.symbols("x", real=True)
    assert sign(x, x, domain=sp.sin(x) > 0) is Sign.UNKNOWN


def test_parameterized_multivariate_affine_mapping_is_stratified():
    x, y, a = sp.symbols("x y a", real=True)
    f = (a * x, y)
    for query in (injective, surjective, bijective):
        result = query(f, (x, y), return_result=True)
        assert _specialize(result, a, 2) is TruthValue.TRUE
        assert _specialize(result, a, 0) is TruthValue.FALSE


def test_truth_conflicts_are_order_independent_and_explicitly_unknown():
    a = sp.symbols("a", real=True)
    first = normalize_cases(
        (
            ConditionalExpression(TruthValue.TRUE, a >= 0),
            ConditionalExpression(TruthValue.FALSE, a <= 0),
        )
    )
    second = normalize_cases(
        (
            ConditionalExpression(TruthValue.FALSE, a <= 0),
            ConditionalExpression(TruthValue.TRUE, a >= 0),
        )
    )
    assert _specialize(first, a, 0) is TruthValue.UNKNOWN
    assert _specialize(second, a, 0) is TruthValue.UNKNOWN
    assert _specialize(first, a, 1) is TruthValue.TRUE
    assert _specialize(first, a, -1) is TruthValue.FALSE


def test_unresolved_curvature_domain():
    x = sp.symbols("x", real=True)
    assert convexity(x**2, x, domain=sp.sin(x) > 0) is Convexity.UNKNOWN


def test_disconnected_semialgebraic_domain_is_not_globally_convex():
    x = sp.symbols("x", real=True)
    domain = (x < -1) | (x > 1)
    assert convexity(x**2, x, domain=domain) is Convexity.NEITHER


def test_semialg_sign_partition_detects_disconnected_sign_change():
    x = sp.symbols("x", real=True)
    assert sign(x, x, domain=sp.Ne(x, 0)) is Sign.SIGN_CHANGING


def test_backend_smoothness_claim_is_validated_at_boundary():
    from funcprops import differentiability
    from funcprops.results import Differentiability

    x = sp.symbols("x", real=True)
    expr = x ** sp.Rational(3, 2)
    assert (
        differentiability(expr, x, domain=x >= 0, order=1)
        is Differentiability.DIFFERENTIABLE
    )
