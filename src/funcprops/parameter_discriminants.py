"""Certified transition loci for parameterized univariate families."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .exactness import certify_identity_equal
from .source_syntax import differentiate


def _polynomial_syntax(node, symbols, atoms=()):
    if node in symbols or node in atoms:
        return True
    if not node.free_symbols:
        return not node.has(sp.Float) and node.is_finite is True
    if node.is_Add or node.is_Mul:
        return all(_polynomial_syntax(a, symbols, atoms) for a in node.args)
    return (
        node.is_Pow
        and node.exp.is_Integer
        and node.exp >= 0
        and _polynomial_syntax(node.base, symbols, atoms)
    )


@dataclass(frozen=True)
class TranscendentalDiscriminant:
    """Describe parameter transitions for a supported transcendental family."""

    family: str
    condition: sp.Expr
    transition: sp.Expr
    source: str


@dataclass(frozen=True)
class ParameterTransitionLocus:
    """Record a polynomial family's exceptional parameter locus."""

    expression: sp.Expr
    variable: sp.Symbol
    parameters: tuple
    locus: sp.Expr
    complete: bool
    source: str

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                self.source != "polynomial-resultant"
                or self.complete is not True
                or not isinstance(self.variable, sp.Symbol)
                or not isinstance(self.parameters, tuple)
                or self.parameters
                != tuple(
                    sorted(self.expression.free_symbols - {self.variable}, key=str)
                )
                or not self.parameters
                or not _polynomial_syntax(self.expression, self.expression.free_symbols)
                or not _polynomial_syntax(self.locus, self.expression.free_symbols)
            ):
                return False
            p = sp.Poly(self.expression, self.variable)
            if p.degree() < 1:
                return False
            r = sp.factor(
                sp.resultant(
                    p.as_expr(),
                    differentiate(p.as_expr(), self.variable),
                    self.variable,
                )
            )
        except (AttributeError, TypeError, ValueError, sp.PolynomialError):
            return False
        return certify_identity_equal(r, self.locus) is True


def polynomial_transition_locus(expr, var, parameters=None):
    """Compute parameter loci where a polynomial's degree or multiplicities can change."""

    f = sp.sympify(expr)
    x = sp.sympify(var)
    if not isinstance(x, sp.Symbol) or not _polynomial_syntax(f, f.free_symbols):
        return None
    try:
        p = sp.Poly(f, x)
    except sp.PolynomialError:
        return None
    pars = tuple(
        sorted(
            (f.free_symbols - {x})
            if parameters is None
            else map(sp.sympify, parameters),
            key=str,
        )
    )
    if (
        not pars
        or pars != tuple(sorted(f.free_symbols - {x}, key=str))
        or p.degree() < 1
    ):
        return None
    r = sp.factor(sp.resultant(p.as_expr(), differentiate(p.as_expr(), x), x))
    c = ParameterTransitionLocus(f, x, pars, r, True, "polynomial-resultant")
    return c if c.verify() else None


def exp_linear_discriminant(expr, var, a, b):
    """Compute the supported exponential-linear root transition locus."""

    x = sp.sympify(var)
    a = sp.sympify(a)
    b = sp.sympify(b)
    f = sp.sympify(expr)
    from .domain_tracking import coordinate_domain_compatible

    if (
        not isinstance(x, sp.Symbol)
        or not coordinate_domain_compatible(x, sp.S.Reals)
        or any(
            c.has(x)
            or c.has(sp.Float)
            or c.is_real is not True
            or c.is_finite is not True
            for c in (a, b)
        )
        or any(
            s.is_real is not True or s.is_finite is not True
            for s in f.free_symbols - {x}
        )
        or not _polynomial_syntax(f, f.free_symbols, (sp.exp(x),))
    ):
        return None
    if certify_identity_equal(f, sp.exp(x) + a * x + b) is not True:
        return None
    D = sp.simplify(b + a * (sp.log(-a) - 1))
    return TranscendentalDiscriminant(
        "exp-linear", a < 0, D, "critical-point-elimination"
    )


def exp_linear_root_strata(expr, var, a, b):
    """Partition a supported exponential-linear family by its real root counts."""

    a, b = sp.sympify(a), sp.sympify(b)
    d = exp_linear_discriminant(expr, var, a, b)
    if d is None:
        return None
    D = d.transition
    negative = (
        (
            (2, sp.And(a < 0, D < 0)),
            (1, sp.And(a < 0, sp.Eq(D, 0))),
            (0, sp.And(a < 0, D > 0)),
        )
        if a.is_nonnegative is not True
        else ()
    )
    return (
        *negative,
        (1, a > 0),
        (1, sp.And(sp.Eq(a, 0), b < 0)),
        (0, sp.And(sp.Eq(a, 0), b >= 0)),
    )
