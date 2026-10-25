"""Exact rational minimization over finitely many real components."""

from dataclasses import dataclass

import sympy as sp

from .domain_tracking import DomainRecord, track_domain
from .exactness import certify_identity_equal
from .source_syntax import differentiate


@dataclass(frozen=True)
class OptimizationCandidate:
    """Record a component endpoint, limit or stationary value candidate."""

    point: sp.Expr
    value: sp.Expr
    attained: bool
    component: sp.Set
    kind: str


@dataclass(frozen=True)
class ComponentMinimumResult:
    """Combine finite-component minimum candidates and attainment data."""

    expression: sp.Expr
    variable: sp.Symbol
    domain_record: DomainRecord
    infimum: sp.Expr | None = None
    minimizers: sp.Set = sp.S.EmptySet
    candidates: tuple[OptimizationCandidate, ...] = ()
    complete: bool = False
    reason: str | None = None

    @property
    def domain(self):
        return self.domain_record.effective

    @property
    def attained(self):
        return self.complete is True and self.minimizers is not sp.S.EmptySet

    @property
    def unique(self):
        return isinstance(self.minimizers, sp.FiniteSet) and len(self.minimizers) == 1

    @property
    def certified(self):
        return self.verify()

    @property
    def certificate(self):
        return self if self.complete else None

    @property
    def scope(self):
        return "global-infimum-on-effective-domain"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return (
                type(self) is ComponentMinimumResult
                and type(self.domain_record) is DomainRecord
                and self.complete is True
                and self.domain_record.verify()
                and self
                == finite_component_minimum(
                    self.expression, self.variable, self.domain_record.requested
                )
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def finite_component_minimum(expr, var, domain=sp.S.Reals):
    """Find a rational function's infimum, distinguishing unattained limits.

    All derivative roots must be solved exactly; unresolved comparisons or root
    coverage return an incomplete result, without claiming an optimum.
    """
    f, x = sp.sympify(expr), sp.sympify(var)
    record = track_domain(f, x, domain)

    def unknown(reason):
        return ComponentMinimumResult(f, x, record, reason=reason)

    if not record.complete:
        return unknown(record.reason)
    D = record.effective
    if D is sp.S.EmptySet:
        return ComponentMinimumResult(f, x, record, sp.oo, complete=True)
    if (
        not f.is_rational_function(x)
        or f.free_symbols - {x}
        or f.has(sp.Float)
        or D.has(sp.Float)
    ):
        return unknown("unsupported-rational-coefficients")
    parts = D.args if isinstance(D, sp.Union) else (D,)
    if any(not isinstance(p, (sp.Interval, sp.FiniteSet)) for p in parts):
        return unknown("unsupported-component-geometry")
    candidates = []
    constant_parts = []
    try:
        derivative = sp.cancel(differentiate(f, x))
        for part in parts:
            if isinstance(part, sp.FiniteSet):
                for point in part:
                    candidates.append(
                        OptimizationCandidate(
                            point, sp.simplify(f.subs(x, point)), True, part, "point"
                        )
                    )
                continue
            for point, opened, direction in (
                (part.start, part.left_open, "+"),
                (part.end, part.right_open, "-"),
            ):
                attained = not opened and point.is_finite is True
                value = (
                    sp.simplify(f.subs(x, point))
                    if attained
                    else sp.limit(f, x, point, dir=direction)
                )
                candidates.append(
                    OptimizationCandidate(point, value, attained, part, "endpoint")
                )
            if derivative == 0:
                point = (
                    (part.start + part.end) / 2
                    if part.start.is_finite and part.end.is_finite
                    else part.start + 1
                    if part.start.is_finite
                    else part.end - 1
                    if part.end.is_finite
                    else sp.S.Zero
                )
                value = sp.simplify(f.subs(x, point))
                candidates.append(
                    OptimizationCandidate(point, value, True, part, "constant")
                )
                constant_parts.append((part, value))
            else:
                roots = sp.solveset(sp.fraction(derivative)[0], x, domain=part)
                if not isinstance(roots, sp.FiniteSet) and roots is not sp.S.EmptySet:
                    return unknown("incomplete-critical-points")
                for point in roots:
                    if point.has(sp.Float):
                        return unknown("inexact-critical-points")
                    if part.contains(point) is not sp.S.true:
                        return unknown("unresolved-critical-membership")
                    candidates.append(
                        OptimizationCandidate(
                            point,
                            sp.simplify(f.subs(x, point)),
                            True,
                            part,
                            "stationary",
                        )
                    )
        best = candidates[0].value
        for c in candidates:
            value = c.value
            if value not in (sp.oo, -sp.oo) and (
                value.is_real is not True or value.is_finite is not True
            ):
                return unknown("unresolved-candidate-value")
            if value == best:
                continue
            if (value < best) is sp.S.true:
                best = value
            elif (value > best) is not sp.S.true and certify_identity_equal(
                value, best
            ) is not True:
                return unknown("unresolved-candidate-order")
        minimizers = sp.FiniteSet(
            *(
                c.point
                for c in candidates
                if c.attained and certify_identity_equal(c.value, best) is True
            )
        )
        for part, value in constant_parts:
            if certify_identity_equal(value, best) is True:
                minimizers = sp.Union(minimizers, part)
        return ComponentMinimumResult(
            f, x, record, best, minimizers, tuple(candidates), True
        )
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        return unknown("backend-inconclusive")
