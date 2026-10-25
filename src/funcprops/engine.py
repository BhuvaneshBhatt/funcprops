"""Conditional property-rule evaluation for funcprops.

This module turns the declarative catalogue-derived registry into an actual
rule engine.  It is limited to sufficient conditions: unknown parameter conditions
remain symbolic.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

import sympy as sp
from sympy import S
from sympy.assumptions import Q, ask
from sympy.logic.boolalg import And, BooleanFunction, Not, Or
from sympy.sets.contains import Contains

from .conditions import (
    AlgebraicCondition,
    AssumedCondition,
    AssumedInequalityCondition,
    EqualCondition,
    EvenCondition,
    IntegerCondition,
    NegativeCondition,
    NonintegerCondition,
    NonnegativeCondition,
    NonpositiveCondition,
    NonterminatingCondition,
    OddCondition,
    PositiveCondition,
    RationalCondition,
    RealCondition,
    RealIfDefinedCondition,
    UnequalCondition,
)
from .exactness import certify_equal
from .results import ConditionalExpression, PropertyResult


class ConditionTruth(str, Enum):
    """Distinguish true, false and unresolved symbolic conditions."""

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


def _bool_from(value: bool | None):
    if value is True:
        return S.true
    if value is False:
        return S.false
    return None


def _ask_predicate(arg, attr: str, predicate=None):
    direct = getattr(arg, attr, None)
    if direct is not None:
        return _bool_from(bool(direct))
    if predicate is not None:
        try:
            q = ask(predicate(arg))
        except (TypeError, ValueError):
            q = None
        return _bool_from(q)
    return None


def _semantic_predicate(node):
    """Best-effort evaluation of catalogue assumption predicates."""
    if not isinstance(node, BooleanFunction):
        return None
    args = node.args
    if not args:
        return None
    a = args[0]
    cls = node.func
    if cls is IntegerCondition:
        return _ask_predicate(a, "is_integer", Q.integer)
    if cls is RationalCondition:
        return _ask_predicate(a, "is_rational", Q.rational)
    if cls is RealCondition:
        return _ask_predicate(a, "is_real", Q.real)
    if cls is RealIfDefinedCondition:
        # The source predicate allows undefined/infinite values.  Real is a
        # sufficient proof; otherwise retain the predicate.
        return _ask_predicate(a, "is_real", Q.real)
    if cls is AlgebraicCondition:
        return _ask_predicate(a, "is_algebraic", Q.algebraic)
    if cls is NonintegerCondition:
        v = _ask_predicate(a, "is_integer", Q.integer)
        return Not(IntegerCondition(a)) if v is None else Not(v)
    if cls is PositiveCondition:
        return _ask_predicate(a, "is_positive", Q.positive)
    if cls is NegativeCondition:
        return _ask_predicate(a, "is_negative", Q.negative)
    if cls is NonpositiveCondition:
        return _ask_predicate(a, "is_nonpositive", Q.nonpositive)
    if cls is NonnegativeCondition:
        return _ask_predicate(a, "is_nonnegative", Q.nonnegative)
    if cls is EvenCondition:
        return _ask_predicate(a, "is_even", Q.even)
    if cls is OddCondition:
        return _ask_predicate(a, "is_odd", Q.odd)
    if cls is UnequalCondition and len(args) == 2:
        equal = certify_equal(args[0], args[1])
        if equal is True:
            return S.false
        if equal is False:
            return S.true
        return None
    if cls is EqualCondition and len(args) == 2:
        equal = certify_equal(args[0], args[1])
        if equal is True:
            return S.true
        if equal is False:
            return S.false
        return None
    if cls in (AssumedCondition, AssumedInequalityCondition):
        return simplify_condition(a)
    if cls is NonterminatingCondition:
        # The catalogue normally passes a Tuple of upper parameters.  A
        # hypergeometric series terminates when at least one upper parameter
        # is a nonpositive integer.
        seq = tuple(a) if isinstance(a, (sp.Tuple, tuple, list)) else tuple(args)
        unknown = False
        for p in seq:
            is_int = getattr(-p, "is_integer", None)
            is_nonneg = getattr(-p, "is_nonnegative", None)
            if is_int is True and is_nonneg is True:
                return S.false
            if is_int is None or is_nonneg is None:
                unknown = True
        return None if unknown else S.true
    return None


def simplify_condition(condition, *, assumptions=S.true):
    """Simplify a registry guard while preserving genuinely unknown facts."""
    c = sp.sympify(condition)
    assumptions = sp.sympify(assumptions)

    if c in (S.true, S.false):
        return c

    # Bottom-up semantic reduction of custom predicates and membership tests.
    def walk(node):
        if node in (S.true, S.false):
            return node
        if isinstance(node, Contains):
            item, dom = node.args
            if dom == S.Integers:
                v = _ask_predicate(item, "is_integer", Q.integer)
                if v is not None:
                    return v
            elif dom == S.Reals:
                v = _ask_predicate(item, "is_real", Q.real)
                if v is not None:
                    return v
            elif dom == S.Rationals:
                v = _ask_predicate(item, "is_rational", Q.rational)
                if v is not None:
                    return v
            elif dom == S.Complexes:
                # Every finite ordinary SymPy number/expression is intended as
                # complex-valued unless explicitly non-complex.
                if getattr(item, "is_complex", None) is True:
                    return S.true
        pred = _semantic_predicate(node)
        if pred is not None:
            return pred
        if not getattr(node, "args", None):
            return node
        new_args = tuple(walk(a) for a in node.args)
        try:
            return node.func(*new_args)
        except (TypeError, ValueError):
            return node

    c = walk(c)
    has_semantic = isinstance(c, sp.Basic) and any(
        c.has(cls)
        for cls in (
            IntegerCondition,
            RationalCondition,
            RealCondition,
            RealIfDefinedCondition,
            AlgebraicCondition,
            NonintegerCondition,
            PositiveCondition,
            NegativeCondition,
            NonpositiveCondition,
            NonnegativeCondition,
            EvenCondition,
            OddCondition,
            UnequalCondition,
            EqualCondition,
            AssumedCondition,
            AssumedInequalityCondition,
            NonterminatingCondition,
        )
    )
    if not has_semantic:
        with contextlib.suppress(TypeError, ValueError):
            c = sp.refine(c, assumptions)
        with contextlib.suppress(TypeError, ValueError):
            c = sp.simplify(c)
    if c is True:
        return S.true
    if c is False:
        return S.false
    return c


def truth_bool(condition):
    """Return True/False for cheaply decidable Boolean expressions, else None."""
    if condition in (True, S.true):
        return True
    if condition in (False, S.false):
        return False
    try:
        value = sp.simplify(condition)
    except (TypeError, ValueError, NotImplementedError, ZeroDivisionError):
        return None
    if value is S.true:
        return True
    if value is S.false:
        return False
    return None


def truth_value(condition, *, assumptions=S.true) -> ConditionTruth:
    """Reduce a symbolic condition to true, false or unresolved under assumptions."""

    c = simplify_condition(condition, assumptions=assumptions)
    if c is S.true:
        return ConditionTruth.TRUE
    if c is S.false:
        return ConditionTruth.FALSE
    # If the user's assumptions directly imply or refute the guard, refine
    # often handles it.  A final logical simplification is safe for Boolean
    # combinations but does not solve arbitrary inequalities.
    has_semantic = isinstance(c, sp.Basic) and any(
        c.has(cls)
        for cls in (
            IntegerCondition,
            RationalCondition,
            RealCondition,
            RealIfDefinedCondition,
            AlgebraicCondition,
            NonintegerCondition,
            PositiveCondition,
            NegativeCondition,
            NonpositiveCondition,
            NonnegativeCondition,
            EvenCondition,
            OddCondition,
            UnequalCondition,
            EqualCondition,
            AssumedCondition,
            AssumedInequalityCondition,
            NonterminatingCondition,
        )
    )
    if not has_semantic:
        try:
            both = sp.simplify_logic(And(assumptions, Not(c)))
            if both is S.false:
                return ConditionTruth.TRUE
            both = sp.simplify_logic(And(assumptions, c))
            if both is S.false:
                return ConditionTruth.FALSE
        except (TypeError, ValueError, NotImplementedError):
            pass
    return ConditionTruth.UNKNOWN


@dataclass(frozen=True)
class EvaluatedCase:
    """Retain a registry case after its condition has been evaluated."""

    value: Any
    condition: sp.Basic
    rule_id: str | None
    specificity: int


def evaluate_property(
    expr, prop: str, *, var=None, mode=None, assumptions=S.true
) -> PropertyResult:
    """Evaluate all applicable registry cases for one concrete expression.

    More-specific catalogue definitions shadow generic definitions when their
    guards are proved true.  If a guard cannot be decided, the result remains
    conditional and the generic rule is retained as the fallback case.
    """
    from .registry import registry

    expr = sp.sympify(expr)
    fam = registry().get(getattr(expr.func, "__name__", str(expr.func)))
    if fam is None:
        return PropertyResult(primary=None, source="registry:no-family")

    candidates = []
    for rule in fam.cases(prop):
        if not rule.matches(expr, var=var, mode=mode):
            continue
        value, guard = rule.instantiate(expr)
        if mode in ("real", "complex"):
            repl_mode = {sp.Symbol("real"): S.true if mode == "real" else S.false}
            if isinstance(value, sp.Basic):
                value = value.xreplace(repl_mode)
            if isinstance(guard, sp.Basic):
                guard = guard.xreplace(repl_mode)
        guard = simplify_condition(guard, assumptions=assumptions)
        if guard is S.false:
            continue
        candidates.append(
            EvaluatedCase(value, guard, rule.rule_id, rule.specificity(mode=mode))
        )

    if not candidates:
        return PropertyResult(primary=None, source="registry:no-case")

    candidates.sort(key=lambda c: c.specificity, reverse=True)
    out = []
    covered = S.false
    for c in candidates:
        effective = simplify_condition(
            And(c.condition, Not(covered)), assumptions=assumptions
        )
        if effective is S.false:
            continue
        out.append(ConditionalExpression(c.value, effective))
        covered = simplify_condition(Or(covered, c.condition), assumptions=assumptions)
        if effective is S.true:
            # An unconditional rule at this precedence level shadows every
            # less-specific definition exactly as catalogue precedence does.
            break

    if not out:
        return PropertyResult(primary=None, source="registry:no-case")
    primary = out[0].value if out[0].condition is S.true else None
    return PropertyResult(primary=primary, cases=tuple(out), source="registry")
