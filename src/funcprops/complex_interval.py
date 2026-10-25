"""Outward complex rectangles for an explicitly entire source grammar.

The grammar is structural: raw divisions, powers with branches, and conjugation
are rejected before any normalization. Arithmetic uses pairs of real intervals.
"""

import sympy as sp
from mpmath.ctx_iv import MPIntervalContext

from .transcendental.real_interval import _const_iv, _endpoint

ENTIRE_PRIMITIVES = (sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.erf, sp.erfc)


def entire_source(f, z):
    """Test membership in the exact parameter-free entire-function grammar."""

    if f == z or isinstance(f, sp.Rational) or f in (sp.I, sp.pi, sp.E):
        return True
    if f.is_Add or f.is_Mul:
        return all(entire_source(a, z) for a in f.args)
    if f.is_Pow:
        return isinstance(f.exp, sp.Integer) and f.exp >= 0 and entire_source(f.base, z)
    return f.func in ENTIRE_PRIMITIVES and entire_source(f.args[0], z)


def valid_box(box):
    """Check plain rational complex-box data and endpoint ordering."""

    return (
        type(box) is tuple
        and len(box) == 4
        and all(isinstance(a, sp.Rational) for a in box)
        and box[0] <= box[2]
        and box[1] <= box[3]
    )


def valid_taylor_coefficients(coefficients, order):
    """Require data-only outward boxes before comparing recomputed jets."""
    return (
        type(order) is int
        and order >= 0
        and type(coefficients) is tuple
        and len(coefficients) == order + 1
        and all(valid_box(row) for row in coefficients)
    )


def _mul(a, b):
    x, y = a
    u, v = b
    return x * u - y * v, x * v + y * u


def _power(a, n, ctx):
    value = ctx.mpf(1), ctx.mpf(0)
    while n:
        if n % 2:
            value = _mul(value, a)
        n //= 2
        if n:
            a = _mul(a, a)
    return value


def _erf(a, ctx, max_terms):
    # Absolute geometric majorant for the omitted entire Maclaurin series.
    # For k >= N, |t[k+1]/t[k]| <= r^2/(N+1), where |w| <= r.
    r = sum(max(abs(_endpoint(v._mpi_[0])), abs(_endpoint(v._mpi_[1]))) for v in a)
    term, total = a, (ctx.mpf(0), ctx.mpf(0))
    absolute = r
    tolerance = sp.Rational(1, 10 ** (ctx.dps + 3))
    square = _mul(a, a)
    for k in range(max_terms):
        total = total[0] + term[0], total[1] + term[1]
        n = k + 1
        absolute *= r * r * sp.Rational(2 * k + 1, n * (2 * k + 3))
        ratio = r * r / (n + 1)
        if ratio < 1:
            tail = absolute / (1 - ratio)
            if tail <= tolerance:
                scale = 2 / ctx.sqrt(ctx.pi)
                error = _const_iv(tail, ctx)
                error = ctx.mpf([-error.b, error.b])
                return (total[0] + error) * scale, (total[1] + error) * scale
        term = _mul(term, square)
        factor = _const_iv(-sp.Rational(2 * k + 1, n * (2 * k + 3)), ctx)
        term = term[0] * factor, term[1] * factor
    raise ValueError("complex-erf-series-budget")


def _eval(f, z, box, ctx, max_terms):
    zero = ctx.mpf(0)
    if f == z:
        return box
    if f == sp.I:
        return zero, ctx.mpf(1)
    if isinstance(f, sp.Rational) or f in (sp.pi, sp.E):
        return _const_iv(f, ctx), zero
    if f.is_Add:
        out = zero, zero
        for a in f.args:
            value = _eval(a, z, box, ctx, max_terms)
            out = out[0] + value[0], out[1] + value[1]
        return out
    if f.is_Mul:
        out = ctx.mpf(1), zero
        for a in f.args:
            out = _mul(out, _eval(a, z, box, ctx, max_terms))
        return out
    if f.is_Pow:
        return _power(_eval(f.base, z, box, ctx, max_terms), int(f.exp), ctx)
    return _apply(f.func, _eval(f.args[0], z, box, ctx, max_terms), ctx, max_terms)


def _apply(function, value, ctx, max_terms):
    x, y = value
    if function is sp.exp:
        scale = ctx.exp(x)
        return scale * ctx.cos(y), scale * ctx.sin(y)
    if function in (sp.sin, sp.cos):
        ch, sh = (ctx.exp(y) + ctx.exp(-y)) / 2, (ctx.exp(y) - ctx.exp(-y)) / 2
        return (
            (ctx.sin(x) * ch, ctx.cos(x) * sh)
            if function is sp.sin
            else (ctx.cos(x) * ch, -ctx.sin(x) * sh)
        )
    if function in (sp.sinh, sp.cosh):
        ch, sh = (ctx.exp(x) + ctx.exp(-x)) / 2, (ctx.exp(x) - ctx.exp(-x)) / 2
        return (
            (sh * ctx.cos(y), ch * ctx.sin(y))
            if function is sp.sinh
            else (ch * ctx.cos(y), sh * ctx.sin(y))
        )
    value = _erf((x, y), ctx, max_terms)
    return value if function is sp.erf else (1 - value[0], -value[1])


def _add(a, b):
    return a[0] + b[0], a[1] + b[1]


def _jet(f, z, box, ctx, max_terms):
    """Forward-mode complex derivative, preserving the entire source grammar."""
    zero = (ctx.mpf(0), ctx.mpf(0))
    one = (ctx.mpf(1), ctx.mpf(0))
    if f == z:
        return box, one
    if isinstance(f, sp.Rational) or f in (sp.I, sp.pi, sp.E):
        return _eval(f, z, box, ctx, max_terms), zero
    if f.is_Add:
        value, derivative = zero, zero
        for arg in f.args:
            v, d = _jet(arg, z, box, ctx, max_terms)
            value, derivative = _add(value, v), _add(derivative, d)
        return value, derivative
    if f.is_Mul:
        value, derivative = one, zero
        for arg in f.args:
            v, d = _jet(arg, z, box, ctx, max_terms)
            derivative = _add(_mul(derivative, v), _mul(value, d))
            value = _mul(value, v)
        return value, derivative
    if f.is_Pow:
        v, d = _jet(f.base, z, box, ctx, max_terms)
        n = int(f.exp)
        value = _power(v, n, ctx)
        derivative = (
            zero
            if n == 0
            else _mul(_mul((ctx.mpf(n), ctx.mpf(0)), _power(v, n - 1, ctx)), d)
        )
        return value, derivative
    v, d = _jet(f.args[0], z, box, ctx, max_terms)
    value = _apply(f.func, v, ctx, max_terms)
    if f.func is sp.exp:
        prime = value
    elif f.func in (sp.sin, sp.cos, sp.sinh, sp.cosh):
        companion = {
            sp.sin: sp.cos,
            sp.cos: sp.sin,
            sp.sinh: sp.cosh,
            sp.cosh: sp.sinh,
        }[f.func]
        prime = _apply(companion, v, ctx, max_terms)
        if f.func is sp.cos:
            prime = (-prime[0], -prime[1])
    else:
        square = _mul(v, v)
        prime = _apply(sp.exp, (-square[0], -square[1]), ctx, max_terms)
        scale = (2 if f.func is sp.erf else -2) / ctx.sqrt(ctx.pi)
        prime = (prime[0] * scale, prime[1] * scale)
    return value, _mul(prime, d)


def complex_box_jet(f, z, box, *, precision=30, max_series_terms=4096):
    """Outward value and first holomorphic derivative boxes, or None.

    Differentiation uses structural chain/product rules. Derivatives of erf/erfc
    use outward 2/sqrt(pi), without extending the accepted source grammar.
    """
    if (
        not isinstance(z, sp.Symbol)
        or z.assumptions0 != {"commutative": True}
        or f.free_symbols - {z}
        or f.has(sp.Float)
        or not valid_box(box)
        or type(precision) is not int
        or precision < 2
        or type(max_series_terms) is not int
        or max_series_terms < 0
        or not entire_source(f, z)
    ):
        return None
    try:
        ctx = MPIntervalContext()
        ctx.dps = precision
        a, b, c, d = [_const_iv(v, ctx) for v in box]
        values = _jet(
            f, z, (ctx.mpf([a.a, c.b]), ctx.mpf([b.a, d.b])), ctx, max_series_terms
        )
        result = []
        for value in values:
            re, im = [tuple(map(_endpoint, v._mpi_)) for v in value]
            result.append((re[0], im[0], re[1], im[1]))
        return tuple(result) if all(valid_box(r) for r in result) else None
    except (
        AttributeError,
        ValueError,
        TypeError,
        ArithmeticError,
        NotImplementedError,
    ):
        return None


def complex_box_evaluate(f, z, box, *, precision=30, max_series_terms=4096):
    """Return exact rational outward bounds (real low, imag low, real high, imag high)."""
    if (
        not isinstance(z, sp.Symbol)
        or z.assumptions0 != {"commutative": True}
        or f.free_symbols - {z}
        or f.has(sp.Float)
        or not valid_box(box)
        or type(precision) is not int
        or precision < 2
        or type(max_series_terms) is not int
        or max_series_terms < 0
        or not entire_source(f, z)
    ):
        return None

    try:
        ctx = MPIntervalContext()
        ctx.dps = precision
        a, b, c, d = [_const_iv(v, ctx) for v in box]
        value = _eval(
            f, z, (ctx.mpf([a.a, c.b]), ctx.mpf([b.a, d.b])), ctx, max_series_terms
        )
        re, im = [tuple(map(_endpoint, v._mpi_)) for v in value]
        result = re[0], im[0], re[1], im[1]
        return result if valid_box(result) else None
    except (
        AttributeError,
        ValueError,
        TypeError,
        ArithmeticError,
        NotImplementedError,
    ):
        return None


def _series_product(a, b, order, ctx):
    zero = (ctx.mpf(0), ctx.mpf(0))
    out = []
    for n in range(order + 1):
        value = zero
        for k in range(n + 1):
            value = _add(value, _mul(a[k], b[n - k]))
        out.append(value)
    return tuple(out)


def _series_exp(a, order, ctx, max_terms):
    out = [_apply(sp.exp, a[0], ctx, max_terms)]
    for n in range(1, order + 1):
        value = (ctx.mpf(0), ctx.mpf(0))
        for k in range(1, n + 1):
            v = _mul(a[k], out[n - k])
            value = _add(value, (k * v[0], k * v[1]))
        out.append((value[0] / n, value[1] / n))
    return tuple(out)


def _taylor(f, z, box, order, ctx, max_terms):
    zero = (ctx.mpf(0), ctx.mpf(0))
    one = (ctx.mpf(1), ctx.mpf(0))
    if f == z:
        return (box,) + ((one,) + (zero,) * (order - 1) if order else ())
    if isinstance(f, sp.Rational) or f in (sp.I, sp.pi, sp.E):
        return (_eval(f, z, box, ctx, max_terms),) + (zero,) * order
    if f.is_Add:
        out = (zero,) * (order + 1)
        for arg in f.args:
            out = tuple(
                _add(a, b)
                for a, b in zip(
                    out, _taylor(arg, z, box, order, ctx, max_terms), strict=True
                )
            )
        return out
    if f.is_Mul:
        out = (one,) + (zero,) * order
        for arg in f.args:
            out = _series_product(
                out, _taylor(arg, z, box, order, ctx, max_terms), order, ctx
            )
        return out
    if f.is_Pow:
        value = _taylor(f.base, z, box, order, ctx, max_terms)
        out = (one,) + (zero,) * order
        n = int(f.exp)
        while n:
            if n % 2:
                out = _series_product(out, value, order, ctx)
            n //= 2
            if n:
                value = _series_product(value, value, order, ctx)
        return out
    a = _taylor(f.args[0], z, box, order, ctx, max_terms)
    if f.func is sp.exp:
        return _series_exp(a, order, ctx, max_terms)
    if f.func in (sp.sin, sp.cos, sp.sinh, sp.cosh):
        circular = f.func in (sp.sin, sp.cos)
        sine = sp.sin if circular else sp.sinh
        cosine = sp.cos if circular else sp.cosh
        sv = [_apply(sine, a[0], ctx, max_terms)]
        cv = [_apply(cosine, a[0], ctx, max_terms)]
        for n in range(1, order + 1):
            s, c = zero, zero
            for k in range(1, n + 1):
                u, v = _mul(a[k], cv[n - k]), _mul(a[k], sv[n - k])
                s = _add(s, (k * u[0], k * u[1]))
                c = _add(c, (k * v[0], k * v[1]))
            sv.append((s[0] / n, s[1] / n))
            cv.append((-c[0] / n, -c[1] / n) if circular else (c[0] / n, c[1] / n))
        return tuple(sv if f.func in (sp.sin, sp.sinh) else cv)
    square = _series_product(a, a, order, ctx)
    e = _series_exp(tuple((-v[0], -v[1]) for v in square), order, ctx, max_terms)
    out = [_apply(f.func, a[0], ctx, max_terms)]
    scale = (2 if f.func is sp.erf else -2) / ctx.sqrt(ctx.pi)
    for n in range(1, order + 1):
        value = zero
        for k in range(1, n + 1):
            v = _mul(a[k], e[n - k])
            value = _add(value, (k * v[0], k * v[1]))
        out.append((value[0] * scale / n, value[1] * scale / n))
    return tuple(out)


def complex_box_taylor(f, z, box, order, *, precision=30, max_series_terms=4096):
    """Outward normalized Taylor coefficients f^(k)/k! on a complex box."""
    if (
        type(order) is not int
        or order < 0
        or not isinstance(z, sp.Symbol)
        or z.assumptions0 != {"commutative": True}
        or f.free_symbols - {z}
        or f.has(sp.Float)
        or not valid_box(box)
        or not entire_source(f, z)
        or type(precision) is not int
        or precision < 2
        or type(max_series_terms) is not int
        or max_series_terms < 0
    ):
        return None
    try:
        ctx = MPIntervalContext()
        ctx.dps = precision
        a, b, c, d = [_const_iv(v, ctx) for v in box]
        values = _taylor(
            f,
            z,
            (ctx.mpf([a.a, c.b]), ctx.mpf([b.a, d.b])),
            order,
            ctx,
            max_series_terms,
        )
        out = []
        for value in values:
            re, im = [tuple(map(_endpoint, v._mpi_)) for v in value]
            out.append((re[0], im[0], re[1], im[1]))
        return tuple(out) if all(valid_box(v) for v in out) else None
    except (
        AttributeError,
        ValueError,
        TypeError,
        ArithmeticError,
        NotImplementedError,
        RecursionError,
    ):
        return None
