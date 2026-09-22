"""Certified zero and equality decisions used at mathematical proof boundaries."""

from __future__ import annotations

import sympy as sp
from exprtest import zerotest


def certify_zero(expr, assumptions=True) -> bool | None:
    """Return whether ``expr`` is provably zero under ``assumptions``.

    ``False`` means nonzero is proved under the supplied assumptions; ``None``
    preserves unresolved symbolic cases.  Only exprtest's certified mode is used.
    """
    expr = sp.sympify(expr)
    result = zerotest(expr, assumptions=assumptions, confidence="certified")
    if result is True:
        return True
    if result is None:
        return None

    # ``zerotest(..., confidence="certified") is False`` proves that an
    # expression is not the zero *identity*.  For a function-property query we
    # need the stronger pointwise statement that it cannot vanish under the
    # supplied assumptions.  A free symbol such as ``x`` is therefore
    # unresolved, not certified nonzero: the polynomial x is not identically
    # zero, but it certainly vanishes at x = 0.
    if not expr.free_symbols:
        return False
    try:
        nonzero = sp.ask(sp.Q.nonzero(expr), assumptions)
    except (TypeError, ValueError, NotImplementedError):
        nonzero = None
    if nonzero is True:
        return False
    if nonzero is False:
        return True
    return None


def certify_equal(left, right, assumptions=True) -> bool | None:
    """Return whether two expressions are provably equal under assumptions."""
    return certify_zero(sp.sympify(left) - sp.sympify(right), assumptions=assumptions)


def certify_identity_zero(expr) -> bool | None:
    """Return whether a symbolic expression is identically zero.

    The certified zero oracle runs first.  When free symbols make a pointwise
    nonzero proof inappropriate, exact polynomial structure may still prove that
    the expression is not the zero polynomial.
    """
    expr = sp.sympify(expr)
    result = zerotest(expr, confidence="certified")
    if result is not None:
        return result
    symbols = tuple(sorted(expr.free_symbols, key=sp.default_sort_key))
    if not symbols:
        return None
    try:
        poly = sp.Poly(expr, *symbols)
    except (sp.PolynomialError, TypeError, ValueError):
        return None
    return True if poly.is_zero else False


def certify_identity_equal(left, right) -> bool | None:
    """Return whether two symbolic formulas are identically equal."""
    return certify_identity_zero(sp.sympify(left) - sp.sympify(right))
