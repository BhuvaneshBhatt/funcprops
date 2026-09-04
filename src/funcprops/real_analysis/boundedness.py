from __future__ import annotations

import sympy as sp
from sympy import S

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..results import Boundedness, ConditionalValue, PropertyResult
from ..stratification import normalize_cases
from .common import combine_natural_domain_condition, condition_to_set
from .domain import function_domain
from .piecewise import (
    combine_piecewise_boundedness,
    piecewise_branches,
)
from .range import function_range


def _boundedness_from_range_condition(cond, y):
    """Infer two-sided boundedness from an exact range representation.

    Indexed extremum ranges already carry exact endpoint objects, so boundedness
    depends only on whether either endpoint is infinite; no envelope reduction
    is required here.
    """
    try:
        from ..transcendental.extrema import ExtremumRange

        if isinstance(cond, ExtremumRange):
            if not cond.complete:
                return Boundedness.UNKNOWN
            lo, hi = cond.lower, cond.upper
            below = lo is not S.NegativeInfinity and lo != S.NegativeInfinity
            above = hi is not S.Infinity and hi != S.Infinity
            if below and above:
                return Boundedness.BOUNDED
            if below:
                return Boundedness.BOUNDED_BELOW
            if above:
                return Boundedness.BOUNDED_ABOVE
            return Boundedness.UNBOUNDED
    except SYMBOLIC_QUERY_ERRORS:
        pass
    # Parameter-dependent endpoints often cannot be converted by SymPy's
    # ``as_set`` (e.g. 0 < y < gamma(a)).  Infer one-/two-sided boundedness
    # directly from exact relational structure before falling back to Sets.
    c = sp.sympify(cond)
    rels = c.args if isinstance(c, sp.And) else (c,)
    lower = False
    upper = False
    for r in rels:
        if not isinstance(r, sp.core.relational.Relational):
            continue
        try:
            if r.lhs == y and not r.rhs.has(y):
                if isinstance(r, (sp.StrictGreaterThan, sp.GreaterThan)):
                    lower = True
                elif isinstance(r, (sp.StrictLessThan, sp.LessThan)):
                    upper = True
            elif r.rhs == y and not r.lhs.has(y):
                if isinstance(r, (sp.StrictLessThan, sp.LessThan)):
                    lower = True
                elif isinstance(r, (sp.StrictGreaterThan, sp.GreaterThan)):
                    upper = True
        except SYMBOLIC_QUERY_ERRORS:
            pass
    if lower and upper:
        return Boundedness.BOUNDED
    if lower:
        return Boundedness.BOUNDED_BELOW
    if upper:
        return Boundedness.BOUNDED_ABOVE
    s = condition_to_set(cond, y)
    if s is None:
        return Boundedness.UNKNOWN
    if s is S.EmptySet:
        # The empty-domain convention is vacuously bounded in both directions.
        return Boundedness.BOUNDED
    try:
        lo = s.inf
        hi = s.sup
    except SYMBOLIC_QUERY_ERRORS:
        return Boundedness.UNKNOWN
    below = lo != S.NegativeInfinity
    above = hi != S.Infinity
    if below and above:
        return Boundedness.BOUNDED
    if below:
        return Boundedness.BOUNDED_BELOW
    if above:
        return Boundedness.BOUNDED_ABOVE
    return Boundedness.UNBOUNDED


def _structural_boundedness(expr, var, domain):
    """Apply cheap closure rules before invoking a full range computation."""
    if not expr.has(var):
        return Boundedness.BOUNDED
    if expr.func in (sp.sin, sp.cos, sp.tanh, sp.atan):
        return Boundedness.BOUNDED
    if isinstance(expr, sp.Piecewise):
        branches = piecewise_branches(expr, var, domain)
        if branches:
            values = [
                function_boundedness(branch.expression, var, domain=branch.condition)
                for branch in branches
            ]
            return combine_piecewise_boundedness(values)
    if expr.func is sp.Abs:
        inner = function_boundedness(expr.args[0], var, domain=domain)
        if inner is Boundedness.BOUNDED:
            return Boundedness.BOUNDED
        return Boundedness.BOUNDED_BELOW
    if expr.func is sp.exp:
        inner = function_boundedness(expr.args[0], var, domain=domain)
        if inner in (Boundedness.BOUNDED, Boundedness.BOUNDED_ABOVE):
            return Boundedness.BOUNDED
        return Boundedness.BOUNDED_BELOW
    if expr.is_Add:
        values = [function_boundedness(a, var, domain=domain) for a in expr.args]
        if not any(isinstance(v, PropertyResult) for v in values):
            upper = {Boundedness.BOUNDED, Boundedness.BOUNDED_ABOVE}
            lower = {Boundedness.BOUNDED, Boundedness.BOUNDED_BELOW}
            above = all(v in upper for v in values)
            below = all(v in lower for v in values)
            if above and below:
                return Boundedness.BOUNDED
            if above:
                return Boundedness.BOUNDED_ABOVE
            if below:
                return Boundedness.BOUNDED_BELOW
    if expr.is_Mul:
        values = [function_boundedness(a, var, domain=domain) for a in expr.args]
        if values and all(v is Boundedness.BOUNDED for v in values):
            return Boundedness.BOUNDED
    return Boundedness.UNKNOWN


def function_boundedness(expr, var, *, domain=True):
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    y = sp.Dummy("_y", real=True)
    structural = _structural_boundedness(expr, var, domain)
    if structural is not Boundedness.UNKNOWN:
        return structural
    natural = function_domain(expr, var)
    # function_range owns natural-domain intersection.  Passing an already
    # combined mixed parameter/domain formula can obscure a simple user domain
    # (e.g. x>=0) and prevent endpoint-aware special-function rules from firing.
    constraints = combine_natural_domain_condition(natural, domain, var)
    try:
        cond = function_range(expr, var, y, constraints=constraints)
    except SYMBOLIC_QUERY_ERRORS:
        return Boundedness.UNKNOWN
    if isinstance(cond, PropertyResult):
        out = normalize_cases(
            (
                ConditionalValue(
                    _boundedness_from_range_condition(c.value, y), c.condition
                )
                for c in cond.cases
            ),
            primary=_boundedness_from_range_condition(cond.primary, y)
            if cond.primary is not None
            else None,
            source="range-boundedness-stratification",
        )
        return out if out.cases else Boundedness.UNKNOWN
    return _boundedness_from_range_condition(cond, y)
