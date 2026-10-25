"""Replayable one-dimensional Taylor-model enclosures."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .certified_balls import certified_real_ball
from .domain_tracking import smooth_domain_record
from .exactness import certify_identity_equal
from .source_syntax import differentiate


def _remainder_bounds(ball, domain, center, exponent):
    """Exact interval product for f^(n+1)(xi)*(x-c)^(n+1)/(n+1)!."""
    a = sp.simplify(domain.start - center)
    b = sp.simplify(domain.end - center)
    vals = [sp.simplify(a**exponent), sp.simplify(b**exponent)]
    if exponent % 2 == 0 and domain.contains(center) is sp.S.true:
        vals.append(sp.S.Zero)
    plo = sp.Min(*vals)
    phi = sp.Max(*vals)
    products = [
        sp.simplify(q * r / sp.factorial(exponent))
        for q in (ball.lower, ball.upper)
        for r in (plo, phi)
    ]
    return sp.Min(*products), sp.Max(*products)


@dataclass(frozen=True)
class TaylorModel:
    """Store a polynomial approximation and certified derivative remainder bound."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    center: sp.Expr
    order: int
    polynomial: sp.Expr
    remainder_lower: sp.Expr
    remainder_upper: sp.Expr
    source: str = "taylor-lagrange-interval"
    domain_record: object = None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "taylor-enclosure-on-domain"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return self._verify()
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False

    def _verify(self):
        if type(self.order) is not int or self.order < 0:
            return False
        record = smooth_domain_record(
            self.expression, self.variable, self.domain, self.order + 1
        )
        if record is None or (
            self.domain_record is not None and not self.domain_record.matches(record)
        ):
            return False
        if self.source != "taylor-lagrange-interval" or self.order < 0:
            return False
        x = self.variable
        c = self.center
        if self.domain.contains(c) is not sp.S.true:
            return False
        poly = sum(
            differentiate(self.expression, x, k).subs(x, c)
            / sp.factorial(k)
            * (x - c) ** k
            for k in range(self.order + 1)
        )
        if certify_identity_equal(poly, self.polynomial) is not True:
            return False
        d = differentiate(self.expression, x, self.order + 1)
        ball = certified_real_ball(d, x, self.domain)
        if ball is None:
            return False
        lo, hi = _remainder_bounds(ball, self.domain, c, self.order + 1)
        return (
            certify_identity_equal(lo, self.remainder_lower) is True
            and certify_identity_equal(hi, self.remainder_upper) is True
        )


def taylor_model(expr, var, domain, *, order=2, center=None):
    """Construct a Taylor polynomial with a certified derivative remainder bound."""

    if (
        not isinstance(domain, sp.Interval)
        or domain.start in (-sp.oo, sp.oo)
        or domain.end in (-sp.oo, sp.oo)
    ):
        return None
    x = sp.sympify(var)
    f = sp.sympify(expr)
    if type(order) is not int or order < 0:
        return None
    record = smooth_domain_record(f, x, domain, order + 1)
    if record is None:
        return None
    c = sp.sympify(center if center is not None else (domain.start + domain.end) / 2)
    if domain.contains(c) is not sp.S.true:
        return None
    poly = sp.expand(
        sum(
            differentiate(f, x, k).subs(x, c) / sp.factorial(k) * (x - c) ** k
            for k in range(order + 1)
        )
    )
    d = differentiate(f, x, order + 1)
    ball = certified_real_ball(d, x, domain)
    if ball is None:
        return None
    lo, hi = _remainder_bounds(ball, domain, c, order + 1)
    return TaylorModel(f, x, domain, c, order, poly, lo, hi, domain_record=record)
