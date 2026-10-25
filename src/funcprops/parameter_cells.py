"""Bounded parameter-cell refinement for conditional results."""

from __future__ import annotations

from dataclasses import replace

import sympy as sp
from sympy import S

from .assumption_closure import close_assumptions
from .exactness import certify_identity_equal
from .results import ConditionalExpression, PropertyResult
from .stratification import normalize_cases, semantic_condition


def minimize_strata(result):
    """Merge equivalent parameter cases while retaining their guards."""

    if not isinstance(result, PropertyResult) or not result.cases:
        return result
    cases = []
    for case in result.cases:
        cond = semantic_condition(case.condition)
        atoms = list(sp.And.make_args(cond))
        index = 0
        while index < len(atoms):
            atom = atoms[index]
            others = sp.And(*(atoms[:index] + atoms[index + 1 :]))
            if close_assumptions(others).entails(atom) is True:
                # Recompute against the remaining conjunction after each
                # deletion. Individually redundant equalities can form a cycle;
                # deleting all of them at once would erase the premise.
                atoms.pop(index)
                continue
            index += 1
        cases.append(ConditionalExpression(case.value, sp.And(*atoms)))
    normalized = normalize_cases(
        cases,
        source=result.source,
        primary=result.primary,
        all_properties=result.all_properties,
        evidence=result.evidence,
    )
    return replace(
        result,
        primary=normalized.primary,
        cases=normalized.cases,
        all_properties=normalized.all_properties,
    )


def specialize_cells(result, substitutions):
    """Specialize guards and symbolic conclusions simultaneously.

    Source-bound proof records are not rewritten by symbolic substitution.
    The returned mathematical cases have no inherited certification status;
    use the typed parameter-proof adapters when a replayable proof is required.
    """

    if not isinstance(result, PropertyResult):
        return result
    replacements = dict(substitutions)

    def substitute(value):
        if isinstance(value, sp.Basic):
            return value.subs(replacements, simultaneous=True)
        if isinstance(value, tuple):
            return tuple(substitute(v) for v in value)
        if isinstance(value, list):
            return [substitute(v) for v in value]
        if isinstance(value, dict):
            return {substitute(k): substitute(v) for k, v in value.items()}
        return value

    cases = []
    for c in result.cases:
        cond = sp.simplify(substitute(c.condition))
        if cond is not S.false:
            cases.append(ConditionalExpression(substitute(c.value), cond))
    normalized = normalize_cases(
        cases,
        source=result.source,
        primary=substitute(result.primary),
        all_properties=substitute(result.all_properties),
    )
    return replace(normalized, exceptions=substitute(result.exceptions))


def refine_parameter_cells(
    result, parameters=None, *, split_zero=True, split_sign=False, max_cells=32
):
    """Refine unresolved parameter cells by exact zero/sign partitions.

    This is bounded and purely symbolic.  It never samples parameter
    values and never labels a cell with a new conclusion; it only refines guards so
    existing conditional conclusions can specialize cleanly downstream.
    """
    if not isinstance(result, PropertyResult) or not result.cases:
        return result
    if parameters is None:
        parameters = sorted(
            set().union(*(c.condition.free_symbols for c in result.cases)),
            key=sp.default_sort_key,
        )
    if type(max_cells) is not int or max_cells < 0:
        raise ValueError("max_cells must be a nonnegative integer")
    guards = [S.true]
    for p in parameters:
        pieces = [sp.Eq(p, 0), sp.Ne(p, 0)] if split_zero else [S.true]
        if split_sign and p.is_real is True:
            pieces = [p < 0, sp.Eq(p, 0), p > 0]
        # Stop before a split would discard part of parameter space. The last
        # complete, coarser guard partition is still an exact refinement.
        if len(guards) * len(pieces) > max_cells:
            break
        new = []
        for g in guards:
            for q in pieces:
                h = sp.simplify_logic(sp.And(g, q))
                if h is not S.false:
                    new.append(h)
        guards = new or guards
    out = []
    for case in result.cases:
        for g in guards:
            h = sp.simplify_logic(sp.And(case.condition, g))
            if h is not S.false:
                out.append(ConditionalExpression(case.value, h))
    normalized = normalize_cases(
        out,
        source=result.source,
        primary=result.primary,
        all_properties=result.all_properties,
        evidence=result.evidence,
    )
    return replace(
        result,
        primary=normalized.primary,
        cases=normalized.cases,
        all_properties=normalized.all_properties,
    )


def exponential_affine_transition_cells(expr, variable, parameter):
    """Certified simple parameter strata for ``exp(x) + a``-type translations.

    This recognizes only a family whose transition is exact: exp(x)+a
    has one real root for a<0 and none for a>=0 (with a=0 approached only at -oo).
    """
    x = sp.sympify(variable)
    a = sp.sympify(parameter)
    from .domain_tracking import coordinate_domain_compatible
    from .parameter_checker import translation_source_regular

    raw = sp.sympify(expr)
    if (
        not isinstance(x, sp.Symbol)
        or not isinstance(a, sp.Symbol)
        or x == a
        or not coordinate_domain_compatible(x, S.Reals)
        or a.is_real is False
    ):
        return None
    if not translation_source_regular(raw, x, a, S.Reals, 30, 4096):
        return None
    f = sp.expand(raw)
    if certify_identity_equal(f, sp.exp(x) + a) is not True:
        return None
    real = sp.Contains(a, S.Reals)
    return PropertyResult(
        None,
        cases=(
            ConditionalExpression(1, sp.And(real, a < 0)),
            ConditionalExpression(0, sp.And(real, a >= 0)),
        ),
        source="exponential-translation-stratification",
        evidence=(real,),
        complete=a.is_real is True,
    )


def quadratic_discriminant_cells(expr, variable, parameter):
    """Exact parameter root-count strata for univariate quadratics in x."""
    x = sp.sympify(variable)
    p = sp.sympify(parameter)
    from .domain_tracking import coordinate_domain_compatible

    if (
        not isinstance(x, sp.Symbol)
        or not isinstance(p, sp.Symbol)
        or x == p
        or not coordinate_domain_compatible(x, S.Reals)
    ):
        return None
    try:
        poly = sp.Poly(expr, x)
    except sp.PolynomialError:
        return None
    if poly.degree() != 2 or p not in poly.as_expr().free_symbols:
        return None
    raw = sp.sympify(expr)

    def safe(node):
        if not node.free_symbols:
            return (
                not node.has(sp.Float)
                and node.is_real is True
                and node.is_finite is True
            )
        if isinstance(node, sp.Symbol):
            return True
        if node.is_Add or node.is_Mul:
            return all(safe(n) for n in node.args)
        return node.is_Pow and node.exp.is_Integer and node.exp >= 0 and safe(node.base)

    if not safe(raw):
        return None
    A, B, C = poly.all_coeffs()
    D = sp.factor(B**2 - 4 * A * C)
    real = sp.And(*(sp.Contains(c, sp.S.Reals) for c in (A, B, C)))
    if real is S.false:
        return None
    quad = sp.And(real, sp.Ne(A, 0))
    cases = (
        ConditionalExpression(2, sp.And(quad, D > 0)),
        ConditionalExpression(1, sp.And(quad, sp.Eq(D, 0))),
        ConditionalExpression(0, sp.And(quad, D < 0)),
        ConditionalExpression(1, sp.And(real, sp.Eq(A, 0), sp.Ne(B, 0))),
        ConditionalExpression(
            sp.oo, sp.And(real, sp.Eq(A, 0), sp.Eq(B, 0), sp.Eq(C, 0))
        ),
        ConditionalExpression(0, sp.And(real, sp.Eq(A, 0), sp.Eq(B, 0), sp.Ne(C, 0))),
    )
    return PropertyResult(
        None,
        cases=tuple(c for c in cases if c.condition is not S.false),
        source="quadratic-discriminant-stratification",
        evidence=(D, "leading-coefficient-degree-drop-guards"),
        complete=all(c.is_real is True for c in (A, B, C)),
    )
