"""Derivative induction: nonnegative closure and explicit strict-positive scope."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .certified_inequalities import InequalityCertificate, certify_inequality
from .domain_tracking import smooth_domain_record
from .exactness import certify_identity_equal
from .results import TruthValue
from .source_syntax import differentiate


@dataclass(frozen=True)
class DerivativeChainCertificate:
    """Prove a derivative sign by induction from endpoint data."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    depth: int
    endpoint: sp.Expr
    base_certificate: object

    @property
    def strict_domain(self):
        if (
            self.depth == 0
            or self.expression.subs(self.variable, self.endpoint).is_positive is True
        ):
            return self.domain
        return sp.Interval(
            self.domain.start, self.domain.end, True, self.domain.right_open
        )

    @property
    def relation(self):
        return ">" if self.strict_domain == self.domain else ">="

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "nonnegative-on-domain-positive-on-strict-domain"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self.depth) is not int
                or self.depth < 0
                or not isinstance(self.domain, sp.Interval)
            ):
                return False
            if (
                self.endpoint != self.domain.start
                or self.endpoint.is_finite is not True
            ):
                return False
            closure = sp.Interval(
                self.domain.start, self.domain.end, False, self.domain.right_open
            )
            if (
                smooth_domain_record(
                    self.expression, self.variable, closure, self.depth
                )
                is None
            ):
                return False
            base = self.base_certificate
            if (
                not isinstance(base, InequalityCertificate)
                or base.variable != self.variable
                or base.domain != self.domain
                or base.relation != ">"
                or base.classification is not TruthValue.TRUE
                or not base.verify()
            ):
                return False
            if (
                certify_identity_equal(
                    differentiate(self.expression, self.variable, self.depth),
                    base.expression,
                )
                is not True
            ):
                return False
            return all(
                sp.simplify(
                    differentiate(self.expression, self.variable, k).subs(
                        self.variable, self.endpoint
                    )
                ).is_nonnegative
                is True
                for k in range(self.depth)
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def derivative_chain_positive(expr, var, domain, *, max_depth=6):
    """Prove nonnegativity on domain and strict positivity on strict_domain.

    A zero at an included left endpoint is retained in the nonnegative claim;
    it is explicitly excluded from strict_domain. No strict endpoint claim is
    inferred merely from positive higher derivatives.
    """
    if type(max_depth) is not int or max_depth < 0:
        raise ValueError("max_depth must be a nonnegative integer")
    if not isinstance(domain, sp.Interval) or domain.start.is_finite is not True:
        return None
    f, x = sp.sympify(expr), sp.sympify(var)
    closure = sp.Interval(domain.start, domain.end, False, domain.right_open)
    for depth in range(max_depth + 1):
        if smooth_domain_record(f, x, closure, depth) is None:
            continue
        cert = certify_inequality(
            differentiate(f, x, depth), 0, x, domain, relation=">", max_depth=5
        )
        if cert.classification is TruthValue.TRUE:
            out = DerivativeChainCertificate(f, x, domain, depth, domain.start, cert)
            if out.verify():
                return out
    return None
