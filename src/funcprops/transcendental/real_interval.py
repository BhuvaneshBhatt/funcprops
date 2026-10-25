from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import sympy as sp
from mpmath.ctx_iv import MPIntervalContext

from ..source_syntax import logarithm_quotient


@dataclass(frozen=True)
class RealIntervalEvaluation:
    """Store an outward real interval evaluation and its arithmetic provenance."""

    expression: sp.Basic
    variable: sp.Symbol
    domain: sp.Interval
    lower: str
    upper: str
    excludes_zero: bool
    strict_sign: int
    source: str = "mpmath-outward-rounded-real-interval"


def _endpoint(raw):
    sign, mantissa, exponent, bits = raw
    if bits < 0:
        return sp.oo * (-1 if sign else 1) if bits in (-2, -3) else sp.nan
    return sp.Integer((-1 if sign else 1) * mantissa) * sp.Rational(2) ** exponent


def _const_iv(expr, ctx):
    if isinstance(expr, sp.Integer):
        n = int(expr)
        return ctx.mpf([n, n])
    if isinstance(expr, sp.Rational):
        return ctx.mpf([int(expr.p), int(expr.p)]) / ctx.mpf([int(expr.q), int(expr.q)])
    if expr == sp.pi:
        return ctx.pi
    if expr == sp.E:
        return ctx.e
    raise ValueError


def _erf_point(point, ctx, max_terms):
    """Integral Maclaurin series with an exact alternating-tail bound.

    Once n+1 > t**2, subsequent absolute terms strictly decrease to zero.
    Consecutive partial sums then bracket the integral, without cancellation
    error: all series arithmetic below is rational.
    """
    q = Fraction(int(point.p), int(point.q))
    if q < 0:
        return -_erf_point(-point, ctx, max_terms)
    if not q:
        return ctx.mpf(0)
    term, total = q, Fraction(0)
    tolerance = Fraction(1, 10 ** (ctx.dps + 5))
    for n in range(max_terms):
        total += term
        following = -term * q * q * (2 * n + 1) / ((n + 1) * (2 * n + 3))
        if n + 1 > q * q and abs(following) <= tolerance:
            a, b = sorted((total, total + following))
            low = _const_iv(sp.Rational(a.numerator, a.denominator), ctx)
            high = _const_iv(sp.Rational(b.numerator, b.denominator), ctx)
            integral = ctx.mpf([low.a, high.b])
            return 2 * integral / ctx.sqrt(ctx.pi)
        term = following
    raise ValueError("erf-series-budget-exhausted")


def _eval(expr, var, x, ctx, max_terms=4096):
    """Evaluate the supported real grammar with outward interval arithmetic and branch checks."""

    expr = sp.sympify(expr)
    if isinstance(var, dict) and expr in var:
        return var[expr]
    if not isinstance(var, dict) and expr == var:
        return x
    if isinstance(expr, (sp.Integer, sp.Rational)) or expr in (sp.pi, sp.E):
        return _const_iv(expr, ctx)
    if expr.is_Add:
        out = ctx.mpf([0, 0])
        for arg in expr.args:
            out += _eval(arg, var, x, ctx, max_terms)
        return out
    if expr.is_Mul:
        out = ctx.mpf([1, 1])
        for arg in expr.args:
            out *= _eval(arg, var, x, ctx, max_terms)
        return out
    if expr.is_Pow:
        base, exponent = expr.args
        b = _eval(base, var, x, ctx, max_terms)
        if exponent.is_Integer:
            if exponent < 0 and b.a <= 0 <= b.b:
                raise ValueError("source-division-through-zero")
            return b ** int(exponent)
        if exponent == sp.S.Half and b.a >= 0:
            return ctx.sqrt(b)
        if (
            not exponent.free_symbols
            and exponent.is_real is True
            and exponent.is_finite is True
            and b.a > 0
        ):
            q = _eval(exponent, var, x, ctx, max_terms)
            return ctx.exp(q * ctx.log(b))
        raise ValueError
    if expr.func is sp.Abs:
        return abs(_eval(expr.args[0], var, x, ctx, max_terms))
    if expr.func is sp.exp:
        return ctx.exp(_eval(expr.args[0], var, x, ctx, max_terms))
    if expr.func is sp.log:
        if len(expr.args) == 2:
            return _eval(logarithm_quotient(expr), var, x, ctx, max_terms)
        a = _eval(expr.args[0], var, x, ctx, max_terms)
        if a.a <= 0:
            raise ValueError
        return ctx.log(a)
    if expr.func is sp.sin:
        return ctx.sin(_eval(expr.args[0], var, x, ctx, max_terms))
    if expr.func is sp.cos:
        return ctx.cos(_eval(expr.args[0], var, x, ctx, max_terms))
    if expr.func in (sp.asin, sp.acos, sp.atan):
        a = _eval(expr.args[0], var, x, ctx, max_terms)
        if expr.func is sp.atan:
            return ctx.atan2(a, ctx.mpf(1))
        if a.a < -1 or a.b > 1:
            raise ValueError("inverse-trigonometric-real-branch")
        # 1-t^2 is nonnegative on the proved input range. Intersect its
        # outward arithmetic bound with that exact mathematical constraint.
        squared = 1 - a**2
        squared = ctx.mpf([max(ctx.mpf(0), squared.a), squared.b])
        root = ctx.sqrt(squared)
        return ctx.atan2(a, root) if expr.func is sp.asin else ctx.atan2(root, a)
    if expr.func is sp.tan:
        return ctx.tan(_eval(expr.args[0], var, x, ctx, max_terms))
    if expr.func is sp.sinh:
        a = _eval(expr.args[0], var, x, ctx, max_terms)
        return (ctx.exp(a) - ctx.exp(-a)) / 2
    if expr.func is sp.cosh:
        a = _eval(expr.args[0], var, x, ctx, max_terms)
        return (ctx.exp(a) + ctx.exp(-a)) / 2
    if expr.func is sp.tanh:
        a = _eval(expr.args[0], var, x, ctx, max_terms)
        e = ctx.exp(2 * a)
        return (e - 1) / (e + 1)
    if expr.func in (sp.erf, sp.erfc):
        a = _eval(expr.args[0], var, x, ctx, max_terms)
        lo, hi = map(_endpoint, a._mpi_)
        if not isinstance(lo, sp.Rational) or not isinstance(hi, sp.Rational):
            raise ValueError
        # erf is increasing, since its real derivative is 2 exp(-t**2)/sqrt(pi).
        low = _erf_point(lo, ctx, max_terms)
        high = _erf_point(hi, ctx, max_terms)
        value = ctx.mpf([low.a, high.b])
        return value if expr.func is sp.erf else 1 - value
    raise ValueError


def certified_real_interval_evaluate(
    expr, var, domain, *, precision=None, max_series_terms=4096
):
    """Enclose ``expr(domain)`` for a finite exact real interval.

    The routine supports a bounded elementary vocabulary and returns
    ``None`` outside it.  Its purpose is a bounded root-isolation fallback:
    excluding zero proves a cell root-free, and excluding zero from a derivative
    enclosure proves strict monotonicity on that cell.
    """
    precision = 30 if precision is None else precision
    if type(precision) is not int or precision < 2:
        raise ValueError("precision must be an integer of at least 2 decimal digits")
    if type(max_series_terms) is not int or max_series_terms < 0:
        raise ValueError("max_series_terms must be a nonnegative integer")
    ctx = MPIntervalContext()
    ctx.dps = precision
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    singleton = isinstance(domain, sp.FiniteSet) and len(domain) == 1
    start = next(iter(domain)) if singleton else getattr(domain, "start", sp.nan)
    end = start if singleton else getattr(domain, "end", sp.nan)
    if (
        not isinstance(var, sp.Symbol)
        or not (isinstance(domain, sp.Interval) or singleton)
        or start.is_finite is not True
        or end.is_finite is not True
        or start.is_real is not True
        or end.is_real is not True
        or start.has(var)
        or end.has(var)
    ):
        return None
    try:
        a = _eval(start, var, ctx.mpf(0), ctx, max_series_terms)
        b = _eval(end, var, ctx.mpf(0), ctx, max_series_terms)
        x = ctx.mpf([a.a, b.b])
        value = _eval(expr, var, x, ctx, max_series_terms)
        lo = _endpoint(value._mpi_[0])
        hi = _endpoint(value._mpi_[1])
        if lo is sp.nan or hi is sp.nan:
            return None
        lower_text, upper_text = str(lo), str(hi)
    except (ValueError, TypeError, OverflowError, ZeroDivisionError):
        return None
    sign = 1 if lo > 0 else -1 if hi < 0 else 0
    return RealIntervalEvaluation(
        expr,
        var,
        domain,
        lower_text,
        upper_text,
        sign != 0,
        sign,
    )


def certified_real_box_evaluate(expr, domains, *, precision=30, max_series_terms=4096):
    """Outward value on an exact finite Cartesian box; no parameter sampling."""
    from ..domain_tracking import coordinate_domain_compatible

    if (
        type(precision) is not int
        or precision < 2
        or type(max_series_terms) is not int
        or max_series_terms < 0
    ):
        raise ValueError("invalid box enclosure effort")
    ctx = MPIntervalContext()
    ctx.dps = precision
    bindings = {}
    try:
        for symbol, domain in domains:
            if (
                not isinstance(symbol, sp.Symbol)
                or symbol in bindings
                or not coordinate_domain_compatible(symbol, domain)
            ):
                return None
            if isinstance(domain, sp.FiniteSet) and len(domain) == 1:
                a = b = next(iter(domain))
            elif isinstance(domain, sp.Interval):
                a, b = domain.start, domain.end
            else:
                return None
            if any(
                v.free_symbols
                or v.has(sp.Float)
                or v.is_finite is not True
                or v.is_real is not True
                for v in (a, b)
            ):
                return None
            lo, hi = (
                _eval(a, symbol, None, ctx, max_series_terms),
                _eval(b, symbol, None, ctx, max_series_terms),
            )
            bindings[symbol] = ctx.mpf([lo.a, hi.b])
        value = _eval(expr, bindings, None, ctx, max_series_terms)
        lower, upper = map(_endpoint, value._mpi_)
        if not isinstance(lower, sp.Rational) or not isinstance(upper, sp.Rational):
            return None
        return lower, upper
    except (AttributeError, ValueError, TypeError, ArithmeticError):
        return None


__all__ = ["RealIntervalEvaluation", "certified_real_interval_evaluate"]
