from __future__ import annotations

import inspect

import sympy as sp

import funcprops
from funcprops import (
    TruthValue,
    clear_entailment_cache,
    decide,
    entails,
    function_determinant_nonvanishing,
    function_singularities,
    normalize_assumptions,
    require_decision,
)


def test_public_symbolic_property_queries_expose_neutral_assumptions():
    exempt = {"function_jacobian"}
    for name in sorted(item for item in dir(funcprops) if item.startswith("function_")):
        if name in exempt:
            continue
        function = getattr(funcprops, name)
        if not callable(function):
            continue
        signature = inspect.signature(function)
        parameter = signature.parameters.get("assumptions")
        assert parameter is not None, name
        assert parameter.default in (True, sp.S.true), name


def test_assumption_normalization_is_canonical_and_idempotent():
    a, b = sp.symbols("a b", real=True)
    first = normalize_assumptions(sp.And(b > 0, a > 0, a > 0))
    second = normalize_assumptions(first)
    assert first == second
    assert normalize_assumptions(True) is sp.S.true
    assert normalize_assumptions(False) is sp.S.false


def test_same_determinant_query_becomes_decisive_with_assumptions():
    x, a = sp.symbols("x a", real=True)
    unresolved = function_determinant_nonvanishing((a * x,), (x,), return_result=True)
    resolved = function_determinant_nonvanishing(
        (a * x,), (x,), assumptions=a > 0, return_result=True
    )
    assert unresolved.classification is TruthValue.UNKNOWN
    assert resolved.classification is TruthValue.TRUE


def test_affine_boolean_partition_is_proved_without_false_pruning():
    a = sp.symbols("a", real=True)
    partition = sp.Or(
        sp.Eq(a, -1),
        sp.Eq(a, -2),
        sp.And(sp.Ne(a, -1), sp.Ne(a, -2)),
    )
    assert entails(partition) is True
    assert entails(sp.Not(sp.And(sp.Eq(a, -1), sp.Eq(a, -2)))) is True


def test_dummy_singularity_query_does_not_leak_proxy_symbols():
    dummy = sp.Dummy("z")
    locus = function_singularities(sp.log(dummy), dummy, sp.S.Complexes)
    assert locus.free_symbols <= {dummy}


def test_exported_assumption_decision_helpers_have_direct_contracts():
    a = sp.symbols("a", positive=True)
    decision = decide(a > 0)
    assert decision.verdict is True
    assert require_decision(decision) is decision
    clear_entailment_cache()
    assert entails(a > 0) is True


def test_affine_equalities_do_not_create_false_contradictions():
    x, a, b = sp.symbols("x a b", real=True)
    assumptions = sp.And(sp.Eq(x, a), sp.Eq(x, b))
    assert entails(sp.Eq(a, b), assumptions) is True
    assert entails(sp.Eq(a, b + 1), assumptions) is False
    assert entails(a > 0, assumptions) is None


def test_parameter_assumptions_do_not_change_domain_output():
    x, a = sp.symbols("x a", real=True)
    assert funcprops.function_domain(sp.log(x), x, assumptions=a > 0) == (x > 0)
