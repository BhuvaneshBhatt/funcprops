"""Source-bound rational argument-principle counts on valid rectangles."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp
from sympy.polys.polyerrors import DomainError

_ERRORS = (
    sp.PolynomialError,
    DomainError,
    ValueError,
    TypeError,
    NotImplementedError,
    AttributeError,
)


def _boundary_clear(poly, lower_left, upper_right):
    x1, y1 = sp.re(lower_left), sp.im(lower_left)
    x2, y2 = sp.re(upper_right), sp.im(upper_right)
    corners = (x1 + sp.I * y1, x2 + sp.I * y1, x2 + sp.I * y2, x1 + sp.I * y2)
    try:
        return all(
            int(poly.count_roots(a, b)) == 0
            for a, b in zip(corners, corners[1:] + corners[:1], strict=False)
        )
    except _ERRORS:
        return False


def _rational_source_polynomials(expression, variable):
    """Return normalized divisor and every raw denominator boundary premise."""
    if (
        not isinstance(variable, sp.Symbol)
        or variable.assumptions0 != {"commutative": True}
        or expression.free_symbols - {variable}
        or expression.has(sp.Float, sp.oo, -sp.oo, sp.zoo, sp.nan)
    ):
        return None
    guards = []
    for node in sp.preorder_traversal(expression):
        if not node.has(variable):
            if node.is_finite is not True:
                return None
            continue
        if isinstance(node, sp.Function):
            return None
        if isinstance(node, sp.Pow):
            if node.exp.is_Integer is not True:
                return None
            if node.exp.is_negative is True:
                for base in sp.fraction(sp.cancel(node.base)):
                    polynomial = sp.Poly(base, variable)
                    if polynomial.is_zero:
                        return None
                    guards.append(polynomial)
    num, den = sp.fraction(sp.cancel(expression))
    pn, pd = sp.Poly(num, variable), sp.Poly(den, variable)
    return None if pn.is_zero or pd.is_zero else (pn, pd, tuple(guards))


def _rectangle_data(expression, variable, lower_left, upper_right):
    """Count only after proving geometry and raw-source boundary definition."""
    from .complex_coverage import CoverageRectangle

    if not CoverageRectangle(lower_left, upper_right).valid():
        return None
    source = _rational_source_polynomials(expression, variable)
    if source is None:
        return None
    pn, pd, guards = source
    if not all(_boundary_clear(p, lower_left, upper_right) for p in (pn, pd, *guards)):
        return None
    zeros = int(pn.count_roots(lower_left, upper_right))
    poles = int(pd.count_roots(lower_left, upper_right))
    return zeros, poles, zeros - poles


@dataclass(frozen=True)
class MeromorphicContourCertificate:
    """Record zeros, poles and winding of a source-preserving quotient."""

    expression: sp.Expr
    variable: sp.Symbol
    lower_left: sp.Expr
    upper_right: sp.Expr
    zeros: int
    poles: int
    winding: int
    source: str = "rational-argument-principle"

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "meromorphic-divisor-count-on-source-defined-rectangle-boundary"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return (
                self.source == "rational-argument-principle"
                and all(type(n) is int for n in (self.zeros, self.poles, self.winding))
                and _rectangle_data(
                    self.expression, self.variable, self.lower_left, self.upper_right
                )
                == (self.zeros, self.poles, self.winding)
            )
        except _ERRORS:
            return False


def meromorphic_rectangle_count(expr, var, lower_left, upper_right, *, policy=None):
    """Count extension zeros/poles, retaining original source exclusions.

    Rational sources use the existing exact divisor backend. Supported entire
    quotients use a replayable quotient ledger; unknown collisions decline.
    """
    f, x, lower, upper = map(sp.sympify, (expr, var, lower_left, upper_right))
    try:
        data = _rectangle_data(f, x, lower, upper)
    except _ERRORS:
        data = None
    if data is not None:
        return MeromorphicContourCertificate(f, x, lower, upper, *data)
    from .quotient_isolation import (
        QuotientContourCertificate,
        certify_quotient_isolation,
        quotient_source_supported,
    )

    if quotient_source_supported(f, x):
        try:
            state = certify_quotient_isolation(f, x, lower, upper, policy=policy)
            if state.proof.coverage_complete:
                return QuotientContourCertificate(state.proof)
        except _ERRORS:
            pass
    return None
