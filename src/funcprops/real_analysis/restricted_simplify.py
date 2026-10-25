"""Exact local rewrites with original natural-domain exclusions retained."""

from __future__ import annotations

import sympy as sp
from sympy import S

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from .common import combine_domain_condition, condition_to_set
from .domain import domain as real_domain


def simplify_on_domain(expr, var, requested):
    """Simplify an expression using proved restrictions and retain its effective domain."""

    expr = sp.sympify(expr)
    if not isinstance(var, sp.Symbol) or not expr.has(
        sp.Abs, sp.Min, sp.Max, sp.Piecewise
    ):
        return expr, requested
    support = condition_to_set(requested, var)
    if support is None or support is S.EmptySet:
        return expr, requested

    def holds(condition):
        if condition is S.true:
            return True
        truth = condition_to_set(condition, var)
        return truth is not None and support.is_subset(truth) is True

    def rewrite(node):
        if not isinstance(node, sp.Expr):
            return node
        if isinstance(node, sp.Piecewise):
            covered = S.false
            for value, condition in node.args:
                effective = sp.And(condition, sp.Not(covered))
                if holds(effective):
                    return rewrite(value)
                covered = sp.Or(covered, condition)
            return node
        if node.func is sp.Abs:
            arg = node.args[0]
            if arg.is_real is True:
                if holds(arg >= 0):
                    return rewrite(arg)
                if holds(arg <= 0):
                    return -rewrite(arg)
        if node.func in (sp.Min, sp.Max):
            for candidate in node.args:
                if all(
                    holds(
                        candidate <= other
                        if node.func is sp.Min
                        else candidate >= other
                    )
                    for other in node.args
                ):
                    return rewrite(candidate)
        if not node.args:
            return node
        return node.func(*(rewrite(arg) for arg in node.args))

    try:
        result = rewrite(expr)
        if result == expr:
            return expr, requested
        natural = real_domain(expr, var)
        if hasattr(natural, "primary"):
            return expr, requested
        return result, combine_domain_condition(natural, requested, var)
    except SYMBOLIC_QUERY_ERRORS:
        return expr, requested
