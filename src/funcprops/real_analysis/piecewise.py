"""Shared branch-domain analysis for real piecewise expressions.

Property engines use the same effective-branch construction so branch guards,
user domains, and earlier Piecewise conditions are interpreted consistently.
The module contains only cheap exact combination rules; properties that need
interface derivatives or global image geometry remain responsible for those
additional proofs.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import sympy as sp
from sympy import S

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..results import Boundedness, Monotonicity, Sign
from .common import condition_to_set


@dataclass(frozen=True)
class PiecewiseBranch:
    """One expression branch together with its effective requested domain."""

    expression: sp.Expr
    condition: sp.Basic
    domain: sp.Set | None


def piecewise_branches(expr, var, domain=S.true):
    """Return nonempty effective branches of a ``Piecewise`` expression."""
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if not isinstance(expr, sp.Piecewise):
        return ()
    covered = S.false
    branches = []
    for value, condition in expr.args:
        try:
            effective = sp.simplify_logic(
                sp.And(sp.sympify(domain), condition, sp.Not(covered))
            )
        except SYMBOLIC_QUERY_ERRORS:
            effective = sp.And(sp.sympify(domain), condition, sp.Not(covered))
        covered = sp.Or(covered, condition)
        if effective is S.false:
            continue
        domain_set = condition_to_set(effective, var)
        if domain_set is S.EmptySet:
            continue
        branches.append(PiecewiseBranch(sp.sympify(value), effective, domain_set))
    return tuple(branches)


def _scalar_value(result):
    """Return an unconditional scalar result, or ``None`` for conditional data."""
    from ..results import PropertyResult

    if isinstance(result, PropertyResult):
        if result.primary is not None:
            return result.primary
        return None
    return result


def combine_piecewise_sign(values):
    """Combine exact branch sign classifications into a global sign class."""
    vals = tuple(_scalar_value(v) for v in values)
    if not vals or any(v is None or v is Sign.UNKNOWN for v in vals):
        return Sign.UNKNOWN
    if all(v is Sign.ZERO for v in vals):
        return Sign.ZERO
    if all(v is Sign.POSITIVE for v in vals):
        return Sign.POSITIVE
    if all(v is Sign.NEGATIVE for v in vals):
        return Sign.NEGATIVE
    nonneg = {Sign.POSITIVE, Sign.NONNEGATIVE, Sign.ZERO}
    nonpos = {Sign.NEGATIVE, Sign.NONPOSITIVE, Sign.ZERO}
    if all(v in nonneg for v in vals):
        return Sign.NONNEGATIVE
    if all(v in nonpos for v in vals):
        return Sign.NONPOSITIVE
    if any(v in {Sign.POSITIVE, Sign.NONNEGATIVE} for v in vals) and any(
        v in {Sign.NEGATIVE, Sign.NONPOSITIVE} for v in vals
    ):
        return Sign.SIGN_CHANGING
    return Sign.UNKNOWN


def combine_piecewise_boundedness(values):
    """Combine exact branch boundedness classes over a finite branch union."""
    vals = tuple(_scalar_value(v) for v in values)
    if not vals or any(v is None or v is Boundedness.UNKNOWN for v in vals):
        return Boundedness.UNKNOWN
    upper = {Boundedness.BOUNDED, Boundedness.BOUNDED_ABOVE}
    lower = {Boundedness.BOUNDED, Boundedness.BOUNDED_BELOW}
    above = all(v in upper for v in vals)
    below = all(v in lower for v in vals)
    if above and below:
        return Boundedness.BOUNDED
    if above:
        return Boundedness.BOUNDED_ABOVE
    if below:
        return Boundedness.BOUNDED_BELOW
    return Boundedness.UNBOUNDED


def combine_piecewise_monotonicity(values):
    """Combine branch directions before interface ordering is checked.

    A non-``UNKNOWN`` answer here means only that every branch has a compatible
    direction.  The caller must still prove that values do not jump in the
    opposite direction at branch interfaces.
    """
    vals = tuple(_scalar_value(v) for v in values)
    if not vals or any(v is None for v in vals):
        return Monotonicity.UNKNOWN
    inc = {Monotonicity.STRICTLY_INCREASING, Monotonicity.NONDECREASING}
    dec = {Monotonicity.STRICTLY_DECREASING, Monotonicity.NONINCREASING}
    if all(v is Monotonicity.CONSTANT for v in vals):
        return Monotonicity.CONSTANT
    if all(v in inc | {Monotonicity.CONSTANT} for v in vals):
        return Monotonicity.NONDECREASING
    if all(v in dec | {Monotonicity.CONSTANT} for v in vals):
        return Monotonicity.NONINCREASING
    if any(v in inc for v in vals) and any(v in dec for v in vals):
        return Monotonicity.NOT_MONOTONE
    return Monotonicity.UNKNOWN


def piecewise_interface_limits(branches, var, *, derivative_order=0):
    """Return exact one-sided values at contiguous branch interfaces.

    ``None`` is returned when branch domains are not ordered intervals, are not
    contiguous, or an endpoint limit cannot be computed exactly.
    """
    if not branches or any(not isinstance(b.domain, sp.Interval) for b in branches):
        return None
    ordered = tuple(sorted(branches, key=lambda b: sp.default_sort_key(b.domain.start)))
    from ..proof_cache import cached_derivative, cached_endpoint_limit

    out = []
    for left, right in pairwise(ordered):
        boundary = left.domain.end
        if sp.simplify(boundary - right.domain.start) != 0:
            return None
        left_expr = left.expression
        right_expr = right.expression
        if derivative_order:
            try:
                left_expr = cached_derivative(left_expr, var, order=derivative_order)
                right_expr = cached_derivative(right_expr, var, order=derivative_order)
            except SYMBOLIC_QUERY_ERRORS:
                return None
        left_value = cached_endpoint_limit(
            left_expr,
            var,
            boundary,
            direction="-",
            attained=not left.domain.right_open,
        )
        right_value = cached_endpoint_limit(
            right_expr,
            var,
            boundary,
            direction="+",
            attained=not right.domain.left_open,
        )
        if left_value is None or right_value is None:
            return None
        out.append((boundary, left_value, right_value))
    return tuple(out)
