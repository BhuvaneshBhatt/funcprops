"""Replayable eventual-sign certificates for conservative dominance families."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .source_syntax import differentiate


@dataclass(frozen=True)
class ExponentialSumBound:
    """Store exponential-sum dominance bounds on a real tail."""

    dominant_rate: sp.Expr
    constant_lower: sp.Expr
    remainder_upper: sp.Expr
    groups: tuple


def _exponential_sum_bound(expression, variable, direction, threshold, sign):
    """Bound slower exponentials via y**k*exp(-d*y) <= k!/d**k."""
    y = sp.Dummy("sum_tail_coordinate", nonnegative=True)
    shifted = sp.expand(
        sign * expression.subs(variable, direction * (sp.Abs(threshold) + y))
    )
    groups = {}
    for term in sp.Add.make_args(shifted):
        rate = sp.S.Zero
        polynomial = sp.S.One
        for factor in sp.Mul.make_args(term):
            if factor.func is sp.exp and factor.has(y):
                exponent = sp.Poly(factor.args[0], y)
                if exponent.degree() > 1:
                    return None
                slope, offset = exponent.nth(1), exponent.nth(0)
                if (
                    slope.is_Rational is not True
                    or offset.is_real is not True
                    or offset.is_finite is not True
                ):
                    return None
                rate += slope
                polynomial *= sp.exp(offset)
            else:
                polynomial *= factor
        p = sp.Poly(polynomial, y)
        if any(
            c.is_real is not True or c.is_finite is not True for c in p.all_coeffs()
        ):
            return None
        groups[rate] = groups.get(rate, sp.S.Zero) + p.as_expr()
    groups = {
        r: sp.Poly(sp.expand(p), y) for r, p in groups.items() if sp.expand(p) != 0
    }
    if len(groups) < 2:
        return None
    rate = max(groups)
    dominant = groups[rate]
    if (
        any(c.is_nonnegative is not True for c in dominant.all_coeffs())
        or dominant.TC().is_positive is not True
    ):
        return None
    bound = sp.S.Zero
    for slower, polynomial in groups.items():
        if slower == rate:
            continue
        delta = rate - slower
        for (power,), coefficient in polynomial.terms():
            if coefficient.is_nonnegative is True:
                continue
            if coefficient.is_negative is not True:
                return None
            bound += -coefficient * sp.factorial(power) / delta**power
    lower, bound = sp.simplify(dominant.TC()), sp.simplify(bound)
    if sp.simplify(lower - bound).is_positive is not True:
        return None
    data = tuple((r, tuple(p.all_coeffs())) for r, p in sorted(groups.items()))
    return ExponentialSumBound(rate, lower, bound, data)


@dataclass(frozen=True)
class TailSignCertificate:
    """Bind a tail sign to exact source data and dominance inequalities."""

    expression: sp.Expr
    variable: sp.Symbol
    direction: int
    threshold: sp.Expr
    sign: int
    source: str
    dominance: ExponentialSumBound | None = None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "strict-real-sign-on-entire-supported-closed-tail"

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
            sp.PolynomialError,
        ):
            return False

    def _verify(self):
        from .domain_tracking import track_domain

        x = self.variable
        f = sp.sympify(self.expression)
        T = sp.sympify(self.threshold)
        if (
            not isinstance(x, sp.Symbol)
            or type(self.direction) is not int
            or type(self.sign) is not int
            or self.direction not in (-1, 1)
            or self.sign not in (-1, 1)
            or T.is_real is not True
            or T.is_finite is not True
        ):
            return False
        support = (
            sp.Interval(sp.Abs(T), sp.oo)
            if self.direction == 1
            else sp.Interval(-sp.oo, -sp.Abs(T))
        )
        record = track_domain(f, x, support)
        if not record.complete or record.effective != support:
            return False
        if self.source == "exponential-polynomial-sum":
            evidence = _exponential_sum_bound(f, x, self.direction, T, self.sign)
            return evidence is not None and evidence == self.dominance
        if self.dominance is not None:
            return False
        y = sp.Dummy("tail_y", nonnegative=True)
        xx = self.direction * (sp.Abs(T) + y)
        if self.source in {"polynomial-leading-term", "rational-leading-term"}:
            num, den = sp.fraction(sp.cancel(f))
            try:
                _pn, _pd = sp.Poly(num, x), sp.Poly(den, x)
            except sp.PolynomialError:
                return False
            qn = sp.Poly(sp.expand(num.subs(x, xx)), y)
            qd = sp.Poly(sp.expand(den.subs(x, xx)), y)

            def signed(p, s):
                cs = p.all_coeffs()
                return (
                    all((c * s).is_nonnegative is True for c in cs)
                    and (p.TC() * s).is_positive is True
                )

            # denominator must have a fixed nonzero sign on the tail.
            ds = 1 if signed(qd, 1) else -1 if signed(qd, -1) else 0
            return ds != 0 and signed(qn, self.sign * ds)
        if self.source == "exp-polynomial-dominance":
            terms = sp.Mul.make_args(f)
            ex = [t for t in terms if t.func is sp.exp]
            if len(ex) != 1:
                return False
            a = sp.simplify(differentiate(ex[0].args[0], x))
            if a.has(x) or (a * self.direction).is_positive is not True:
                return False
            offset = sp.simplify(ex[0].args[0] - a * x)
            if (
                offset.has(x)
                or offset.is_real is not True
                or offset.is_finite is not True
            ):
                return False
            rest = sp.simplify(f / ex[0])
            try:
                sp.Poly(rest, x)
            except sp.PolynomialError:
                return False
            q = sp.Poly(sp.expand(rest.subs(x, xx)), y)
            return (
                all((c * self.sign).is_nonnegative is True for c in q.all_coeffs())
                and (q.TC() * self.sign).is_positive is True
            )
        return False


def certify_tail_sign(expr, var, *, direction=1, threshold=None):
    """Prove a supported tail sign using exact exponential dominance bounds."""

    f = sp.sympify(expr)
    x = sp.sympify(var)
    candidates = (
        [0, 1, 2, 4, 8, 16, 32, 64] if threshold is None else [sp.sympify(threshold)]
    )
    num, den = sp.fraction(sp.cancel(f))
    try:
        pn, pd = sp.Poly(num, x), sp.Poly(den, x)
    except sp.PolynomialError:
        pn = pd = None
    if (
        pn is not None
        and pd is not None
        and pn.LC().is_nonzero is True
        and pd.LC().is_nonzero is True
    ):
        s = (
            1
            if (pn.LC() / pd.LC()).is_positive
            else -1
            if (pn.LC() / pd.LC()).is_negative
            else None
        )
        if s is not None and direction < 0 and (pn.degree() - pd.degree()) % 2:
            s = -s
        if s is not None:
            src = (
                "polynomial-leading-term"
                if pd.degree() == 0
                else "rational-leading-term"
            )
            for T in candidates:
                c = TailSignCertificate(f, x, direction, sp.sympify(T), s, src)
                if c.verify():
                    return c
    # exp(a*x+b)*P(x), where exponential is positive and grows in the requested direction.
    for e in sp.Mul.make_args(f):
        if e.func is sp.exp:
            a = sp.simplify(differentiate(e.args[0], x))
            rest = sp.simplify(f / e)
            try:
                p = sp.Poly(rest, x)
            except sp.PolynomialError:
                continue
            if (
                a.has(x)
                or (a * direction).is_positive is not True
                or p.LC().is_nonzero is not True
            ):
                continue
            s = 1 if p.LC().is_positive else -1
            if direction < 0 and p.degree() % 2:
                s = -s
            for T in candidates:
                c = TailSignCertificate(
                    f, x, direction, sp.sympify(T), s, "exp-polynomial-dominance"
                )
                if c.verify():
                    return c
    # Finite exponential-polynomial sums with rational real rates.
    for T in candidates:
        for sign in (1, -1):
            try:
                evidence = _exponential_sum_bound(f, x, direction, sp.sympify(T), sign)
            except (sp.PolynomialError, TypeError, ValueError, NotImplementedError):
                evidence = None
            if evidence is not None:
                certificate = TailSignCertificate(
                    f,
                    x,
                    direction,
                    sp.sympify(T),
                    sign,
                    "exponential-polynomial-sum",
                    evidence,
                )
                if certificate.verify():
                    return certificate
    return None
