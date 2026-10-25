"""Verified real root exclusion/uniqueness with source-domain premises."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .certified_balls import certified_real_ball
from .domain_tracking import smooth_domain_record, track_domain
from .source_syntax import differentiate


def _crossing(f, x, interval):
    fa = sp.simplify(f.subs(x, interval.start))
    fb = sp.simplify(f.subs(x, interval.end))
    return (
        (not interval.left_open and fa.is_zero is True)
        or (not interval.right_open and fb.is_zero is True)
        or (fa.is_positive is True and fb.is_negative is True)
        or (fa.is_negative is True and fb.is_positive is True)
    )


@dataclass(frozen=True)
class RealRootInterval:
    """Bind a zero or unique-root interval to its source domain and count method."""

    expression: sp.Expr
    variable: sp.Symbol
    interval: sp.Interval
    root_count: int | None
    unique: bool
    source: str
    domain_record: object = None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "root-count-on-interval"

    @property
    def certificate(self):
        return self if self.root_count in (0, 1) else None

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if type(self.root_count) is not int or type(self.unique) is not bool:
                return False
            actual = verify_real_root_interval(
                self.expression, self.variable, self.interval
            )
            # Recompute source definition before comparing any reported count.
            if self.domain_record is not None and not self.domain_record.matches(
                actual.domain_record
            ):
                return False
            return self.root_count in (0, 1) and (
                self.root_count,
                self.unique,
                self.source,
            ) == (actual.root_count, actual.unique, actual.source)
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def verify_real_root_interval(expr, var, interval):
    """Check the stored real root interval premises and report their replay outcome."""

    f, x = sp.sympify(expr), sp.sympify(var)
    if not isinstance(interval, sp.Interval):
        raise ValueError("root isolation requires an interval")
    record = track_domain(f, x, interval)
    if not record.complete or record.effective != interval:
        return RealRootInterval(
            f, x, interval, None, False, "unresolved-source-domain", record
        )
    b = certified_real_ball(f, x, interval)
    if b is not None and b.excludes_zero:
        return RealRootInterval(f, x, interval, 0, False, "interval-exclusion", record)
    if smooth_domain_record(f, x, interval, 1) is None:
        return RealRootInterval(
            f, x, interval, None, False, "unresolved-smoothness", record
        )
    db = certified_real_ball(differentiate(f, x), x, interval)
    if db is not None and db.excludes_zero and _crossing(f, x, interval):
        return RealRootInterval(f, x, interval, 1, True, "monotone-sign-change", record)
    return RealRootInterval(f, x, interval, None, False, "inconclusive", record)


def interval_newton_count(expr, var, interval):
    """Return a certified scalar Newton inclusion/exclusion count, or None.

    A derivative enclosure excluding zero proves uniqueness. Strict Newton
    inclusion proves existence; disjointness excludes every root by the mean
    value theorem. Endpoint ownership is never inferred from a rounded zero.
    """
    if (
        not isinstance(interval, sp.Interval)
        or interval.start.is_finite is not True
        or interval.end.is_finite is not True
        or interval.has(sp.Float)
        or smooth_domain_record(expr, var, interval.closure, 1) is None
    ):
        return None
    midpoint = (interval.start + interval.end) / 2
    derivative = certified_real_ball(
        differentiate(expr, var),
        var,
        interval.closure,
        precision=30,
        max_precision=240,
        max_refinements=3,
        relation=">",
    )
    if derivative is None or not derivative.excludes_zero:
        return None
    value = certified_real_ball(
        expr.subs(var, midpoint), var, interval.closure, precision=80
    )
    if value is None:
        return None
    quotients = [
        a / b
        for a in (value.lower, value.upper)
        for b in (derivative.lower, derivative.upper)
    ]
    lower = midpoint - sp.Max(*quotients)
    upper = midpoint - sp.Min(*quotients)
    if (upper < interval.start) is sp.S.true or (lower > interval.end) is sp.S.true:
        return 0
    if (lower > interval.start) is sp.S.true and (upper < interval.end) is sp.S.true:
        return 1
    return None
