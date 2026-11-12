"""Exact univariate rational sign charts independent of optimization."""

from dataclasses import dataclass
from functools import cmp_to_key
from itertools import pairwise

import sympy as sp

from .domain_tracking import track_domain
from .source_syntax import normalize_arithmetic


def _compare(a, b):
    difference = sp.simplify(a - b)
    if difference == 0:
        return 0
    if difference.is_positive is True:
        return 1
    if difference.is_negative is True:
        return -1
    raise NotImplementedError("unresolved real algebraic ordering")


def _sample(region):
    if isinstance(region, sp.FiniteSet):
        return next(iter(region))
    if isinstance(region, sp.Union):
        return _sample(region.args[0])
    if not isinstance(region, sp.Interval):
        return None
    a, b = region.start, region.end
    if a is -sp.oo:
        return sp.S.Zero if b is sp.oo else b - 1
    return a + 1 if b is sp.oo else (a + b) / 2


def rational_sign_region(expression, variable, relation):
    """Return the exact truth set of a fixed real algebraic rational inequality."""
    f, x = sp.sympify(expression), sp.sympify(variable)
    if f.free_symbols - {x} or f.has(sp.Float) or not f.is_rational_function(x):
        return None
    p, q = (sp.Poly(a, x, extension=True) for a in sp.fraction(sp.cancel(f)))
    if any(
        c.is_algebraic is not True or c.is_real is not True
        for poly in (p, q)
        for c in poly.all_coeffs()
    ):
        return None
    roots = []
    for poly in (p, q):
        if poly.degree() > 0:
            roots.extend(sp.real_roots(poly, extension=True))
    cuts = sorted(set(roots), key=cmp_to_key(_compare))

    def matches(point):
        value = sp.cancel(f.subs(x, point))
        if value.is_finite is not True or value.is_real is not True:
            return False
        condition = {
            ">": value > 0,
            "<": value < 0,
            ">=": value >= 0,
            "<=": value <= 0,
        }[relation]
        if condition is not sp.true and condition is not sp.false:
            raise NotImplementedError("unresolved rational sign")
        return condition is sp.true

    pieces = [sp.FiniteSet(v) for v in cuts if matches(v)]
    for a, b in pairwise([-sp.oo, *cuts, sp.oo]):
        interval = sp.Interval.open(a, b)
        if matches(_sample(interval)):
            pieces.append(interval)
    return sp.Union(*pieces)


@dataclass(frozen=True)
class RationalSignCertificate:
    """Bind a rational inequality to its complete zero/pole sign partition."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    relation: str
    region: sp.Set

    def verify(self):
        """Recompute sign-chart coverage without constructing any minimizing point."""
        if type(self) is not RationalSignCertificate or self.relation not in {
            ">",
            "<",
            ">=",
            "<=",
        }:
            return False
        try:
            record = track_domain(self.expression, self.variable, self.domain)
            actual = rational_sign_region(self.expression, self.variable, self.relation)
            return (
                record.complete
                and record.effective == self.domain
                and actual == self.region
                and sp.Complement(self.domain, actual) is sp.S.EmptySet
            )
        except (
            TypeError,
            ValueError,
            ArithmeticError,
            NotImplementedError,
            sp.PolynomialError,
        ):
            return False


def rational_sign_evidence(expression, variable, domain, relation):
    """Return sign evidence and an exact counterexample candidate when supported."""
    try:
        region = rational_sign_region(
            normalize_arithmetic(expression), variable, relation
        )
        if region is None:
            return None, None
        remainder = sp.Complement(domain, region)
        if remainder is sp.S.EmptySet:
            proof = RationalSignCertificate(
                expression, variable, domain, relation, region
            )
            return (proof if proof.verify() else None), None
        return None, _sample(remainder)
    except (
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
        sp.PolynomialError,
    ):
        return None, None
