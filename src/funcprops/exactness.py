"""Certified zero and equality decisions used at mathematical proof boundaries."""

from __future__ import annotations

import sympy as sp
from exprtest import zerotest
from sympy import S


def _complex_zero_parts(expr):
    """Do not let a real-only zero decision certify a complex expression."""
    if expr.is_real is True or (not expr.has(sp.I) and expr.is_real is not False):
        return None
    real, imaginary = sp.expand_complex(expr).as_real_imag()
    if real == expr and imaginary == 0:
        return None
    return real, imaginary


def _combine_zero_parts(parts):
    if any(part is False for part in parts):
        return False
    if all(part is True for part in parts):
        return True
    return None


def certify_zero(expr, assumptions=True) -> bool | None:
    """Return whether ``expr`` is provably zero under ``assumptions``.

    ``False`` means nonzero is proved under the supplied assumptions; ``None``
    preserves unresolved symbolic cases.  Only exprtest's certified mode is used.
    """
    expr = sp.sympify(expr)
    parts = _complex_zero_parts(expr)
    if parts is not None:
        return _combine_zero_parts(
            tuple(certify_zero(part, assumptions) for part in parts)
        )
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
        zero = sp.ask(sp.Q.zero(expr), assumptions)
    except (TypeError, ValueError, NotImplementedError):
        zero = None
    if zero is True:
        return True
    if zero is False:
        return False
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
    parts = _complex_zero_parts(expr)
    if parts is not None:
        return _combine_zero_parts(tuple(certify_identity_zero(part) for part in parts))
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


def certify_identity_equal_on_domain(
    left, right, var, *, domain=S.Reals, assumptions=S.true
):
    """Certify an identity for property transfer without erasing branch/domain data.

    Formula identity is necessary but not sufficient when rewriting can change the
    natural domain (for example a cancelled rational hole).  Non-structural
    transfers therefore also require equality of the relevant natural domains.
    """
    left, right, var = sp.sympify(left), sp.sympify(right), sp.sympify(var)
    if left == right:
        return True
    if certify_identity_equal(left, right) is not True:
        return None
    try:
        from .real_analysis.domain import domain as function_domain

        dl = function_domain(left, var, domain=domain)
        dr = function_domain(right, var, domain=domain)
        if dl == dr:
            return True
        from .stratification import exact_set_equal

        if isinstance(dl, sp.Set) and isinstance(dr, sp.Set):
            return exact_set_equal(dl, dr) is True
    except (TypeError, ValueError, NotImplementedError):
        return None
    return None
