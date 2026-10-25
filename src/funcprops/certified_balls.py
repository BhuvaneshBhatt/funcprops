"""Certified real-ball facade over outward interval evaluation."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .transcendental.real_interval import certified_real_interval_evaluate


@dataclass(frozen=True)
class RealBallCertificate:
    """Bound a real expression by outward rational arithmetic."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    lower: sp.Expr
    upper: sp.Expr
    backend: str = "outward-interval"
    precision: int | None = None

    @property
    def excludes_zero(self):
        return self.lower.is_positive is True or self.upper.is_negative is True

    @property
    def sign(self):
        return (
            1
            if self.lower.is_positive is True
            else -1
            if self.upper.is_negative is True
            else 0
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return bool(self._verify())
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            return False

    def _verify(self):
        if self.backend != "outward-interval":
            return False
        r = certified_real_interval_evaluate(
            self.expression, self.variable, self.domain, precision=self.precision
        )
        if r is None:
            return False
        try:
            lo = sp.sympify(r.lower)
            hi = sp.sympify(r.upper)
        except (TypeError, ValueError):
            return False
        return lo >= self.lower and hi <= self.upper


def _real_ball_once(expr, var, domain, *, precision=None):
    precision = 30 if precision is None else precision
    r = certified_real_interval_evaluate(expr, var, domain, precision=precision)
    if r is None:
        return None
    try:
        lo = sp.sympify(r.lower)
        hi = sp.sympify(r.upper)
    except (TypeError, ValueError):
        return None
    return RealBallCertificate(
        sp.sympify(expr), sp.sympify(var), domain, lo, hi, precision=precision
    )


def certified_real_ball(
    expr,
    var,
    domain,
    *,
    precision=None,
    max_precision=None,
    max_refinements=3,
    relation=None,
):
    """Enclose once, or refine a sign goal within explicit precision/work caps."""
    precision = 30 if precision is None else precision
    maximum = precision if max_precision is None else max_precision
    if (
        type(precision) is not int
        or precision < 2
        or type(maximum) is not int
        or maximum < precision
    ):
        raise ValueError(
            "precision bounds must be integers, 2 <= precision <= max_precision"
        )
    if type(max_refinements) is not int or max_refinements < 0:
        raise ValueError("max_refinements must be a nonnegative integer")
    if relation not in (None, ">", "<", ">=", "<="):
        raise ValueError("invalid refinement relation")
    ball = None
    for attempt in range(max_refinements + 1):
        ball = _real_ball_once(expr, var, domain, precision=precision)
        if ball is None or relation is None:
            break
        if relation == ">":
            proved = ball.lower.is_positive is True
        elif relation == "<":
            proved = ball.upper.is_negative is True
        elif relation == ">=":
            proved = ball.lower.is_nonnegative is True
        else:
            proved = ball.upper.is_nonpositive is True
        if proved or precision >= maximum or attempt == max_refinements:
            break
        precision = min(2 * precision, maximum)
    return ball
