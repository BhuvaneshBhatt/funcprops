"""Verified affine and nonlinear interval Krawczyk certificates."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .exactness import certify_zero


def _ival(expr, xs, box):
    e = sp.sympify(expr)
    if not e.has(*xs):
        return (e, e)
    if e in xs:
        interval = box[xs.index(e)]
        return (sp.sympify(interval.start), sp.sympify(interval.end))
    if e.is_Add:
        parts = [_ival(a, xs, box) for a in e.args]
        return (
            sp.simplify(sum(a for a, b in parts)),
            sp.simplify(sum(b for a, b in parts)),
        )
    if e.is_Mul:
        lo = hi = sp.Integer(1)
        for a in e.args:
            al, ah = _ival(a, xs, box)
            vals = [lo * al, lo * ah, hi * al, hi * ah]
            try:
                lo, hi = min(vals), max(vals)
            except TypeError:
                return None
        return (sp.simplify(lo), sp.simplify(hi))
    if e.is_Pow and e.exp.is_Integer and e.exp >= 0:
        base = _ival(e.base, xs, box)
        if base is None:
            return None
        lower, upper = base
        n = int(e.exp)
        vals = [lower**n, upper**n]
        if n % 2 == 0 and lower <= 0 <= upper:
            vals.append(sp.Integer(0))
        try:
            return (sp.simplify(min(vals)), sp.simplify(max(vals)))
        except TypeError:
            return None
    return None


def _add(A, B):
    return (sp.simplify(A[0] + B[0]), sp.simplify(A[1] + B[1]))


def _mul(A, B):
    vals = [A[0] * B[0], A[0] * B[1], A[1] * B[0], A[1] * B[1]]
    try:
        return (sp.simplify(min(vals)), sp.simplify(max(vals)))
    except TypeError:
        return None


def _polynomial_box_premises(expressions, xs, box):
    """The interval algebra supports real polynomials with exact coefficients."""
    if (
        not xs
        or len(set(xs)) != len(xs)
        or len(expressions) != len(xs)
        or len(box) != len(xs)
    ):
        return False
    if any(not isinstance(x, sp.Symbol) or x.is_real is False for x in xs):
        return False
    if any(
        not isinstance(D, sp.Interval)
        or D.left_open
        or D.right_open
        or D.start.is_real is not True
        or D.end.is_real is not True
        or D.start.is_finite is not True
        or D.end.is_finite is not True
        or D.has(sp.Float)
        for D in box
    ):
        return False
    for f in expressions:
        if f.has(sp.Float) or f.is_polynomial(*xs) is not True:
            return False
        if any(
            isinstance(n, sp.Pow) and n.exp.is_negative and n.base.has(*xs)
            for n in sp.preorder_traversal(f)
        ):
            return False
        try:
            coefficients = sp.Poly(f, *xs).coeffs()
        except sp.PolynomialError:
            return False
        if any(c.is_real is not True or c.is_finite is not True for c in coefficients):
            return False
    return True


def _krawczyk(expressions, xs, box):
    if not _polynomial_box_premises(expressions, xs, box):
        return None
    F = sp.Matrix(expressions)
    J = F.jacobian(xs)
    x0 = sp.Matrix([(interval.start + interval.end) / 2 for interval in box])
    sub = dict(zip(xs, x0, strict=False))
    J0 = J.subs(sub)
    if certify_zero(J0.det()) is not False:
        return None
    try:
        C = J0.inv()
    except (ValueError, ZeroDivisionError, NotImplementedError):
        return None
    f0 = F.subs(sub)
    base = x0 - C * f0
    n = len(xs)
    JI = [[_ival(J[i, j], xs, box) for j in range(n)] for i in range(n)]
    if any(v is None for row in JI for v in row):
        return None
    M = []
    for i in range(n):
        row = []
        for j in range(n):
            s = (sp.Integer(0), sp.Integer(0))
            for k in range(n):
                q = _mul((C[i, k], C[i, k]), JI[k][j])
                if q is None:
                    return None
                s = _add(s, q)
            delta = (sp.Integer(1) if i == j else sp.Integer(0),) * 2
            row.append((sp.simplify(delta[0] - s[1]), sp.simplify(delta[1] - s[0])))
        M.append(row)
    dx = [
        (interval.start - x0[j], interval.end - x0[j]) for j, interval in enumerate(box)
    ]
    K = []
    for i in range(n):
        s = (base[i], base[i])
        for j in range(n):
            q = _mul(M[i][j], dx[j])
            if q is None:
                return None
            s = _add(s, q)
        K.append(s)
    return tuple(K), tuple(x0)


@dataclass(frozen=True)
class KrawczykBoxCertificate:
    """Bind a multivariate polynomial root box to a checked contraction."""

    expressions: tuple
    variables: tuple
    box: tuple
    center: tuple
    unique: bool
    source: str = "interval-krawczyk"
    enclosure: tuple = ()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if self.unique is not True or not _polynomial_box_premises(
                self.expressions, self.variables, self.box
            ):
                return False
            if len(self.center) != len(self.variables):
                return False
            if self.source == "affine-krawczyk":
                F = sp.Matrix(self.expressions)
                J = F.jacobian(self.variables)
                if (
                    any(e.has(*self.variables) for e in J)
                    or certify_zero(J.det()) is not False
                ):
                    return False
                if any(sp.sympify(v).has(sp.Float) for v in self.center):
                    return False
                sub = dict(zip(self.variables, self.center, strict=True))
                return all(certify_zero(e.subs(sub)) is True for e in F) and all(
                    interval.contains(v) is sp.S.true
                    for interval, v in zip(self.box, self.center, strict=True)
                )
            if self.source != "interval-krawczyk":
                return False
            out = _krawczyk(self.expressions, self.variables, self.box)
            if out is None:
                return False
            K, x0 = out
            return (
                K == self.enclosure
                and tuple(x0) == self.center
                and all(
                    (D.start < k[0]) is sp.S.true and (k[1] < D.end) is sp.S.true
                    for D, k in zip(self.box, K, strict=True)
                )
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
            IndexError,
        ):
            return False


def krawczyk_box(expressions, variables, box):
    """Prove a unique multivariate polynomial root in a supported real box."""

    xs = tuple(map(sp.sympify, variables))
    box = tuple(box)
    F = tuple(map(sp.sympify, expressions))
    if (
        len(F) != len(xs)
        or len(box) != len(xs)
        or not all(
            isinstance(interval, sp.Interval)
            and not interval.left_open
            and not interval.right_open
            for interval in box
        )
    ):
        return None
    out = _krawczyk(F, xs, box)
    if out is None:
        return None
    K, x0 = out
    if not all(
        (interval.start < k[0]) is sp.S.true and (k[1] < interval.end) is sp.S.true
        for interval, k in zip(box, K, strict=False)
    ):
        return None
    c = KrawczykBoxCertificate(F, xs, box, x0, True, "interval-krawczyk", K)
    return c if c.verify() else None
