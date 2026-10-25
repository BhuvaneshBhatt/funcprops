"""Guarded affine equation and distinct-root-count theorems on full spaces."""

from dataclasses import dataclass

import sympy as sp

from .assumptions import entails, normalize_assumptions
from .exactness import certify_identity_equal
from .results import ConditionalExpression, PropertyResult
from .source_syntax import differentiate


@dataclass(frozen=True)
class AffineSolution:
    """Represent an affine equation's solution under a parameter guard."""

    solutions: sp.Set
    root_count: object


@dataclass(frozen=True)
class GuardedAffineEquationCertificate:
    """Bind exhaustive affine solution cases to real-coefficient premises."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    assumptions: object
    cases: tuple

    @property
    def solutions(self):
        values = tuple(
            case.value.solutions for case in self.cases if case.condition is sp.S.true
        )
        return values[0] if len(values) == 1 else None

    @property
    def root_count(self):
        values = tuple(
            case.value.root_count for case in self.cases if case.condition is sp.S.true
        )
        return values[0] if len(values) == 1 else None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "exhaustive-affine-equation-cases-on-full-domain-under-assumptions"

    def specialize(self, assumptions):
        """Apply exact parameter substitutions and retain the conditions they must satisfy."""

        return affine_equation_cases(
            self.expression,
            self.variable,
            self.domain,
            assumptions=sp.And(self.assumptions, normalize_assumptions(assumptions)),
        )

    def as_result(self):
        """Project guarded evidence into its mathematical result representation."""

        return PropertyResult(
            self.solutions,
            cases=tuple(
                ConditionalExpression(c.value.solutions, c.condition)
                for c in self.cases
            ),
            complete=self.complete,
            certified=self.certified,
            evidence=(self,),
            source="guarded-affine-equation",
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return bool(self.cases) and self == affine_equation_cases(
                self.expression,
                self.variable,
                self.domain,
                assumptions=self.assumptions,
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
            sp.PolynomialError,
        ):
            return False


def affine_equation_cases(
    expression, variable, domain=sp.S.Complexes, *, assumptions=True
):
    """Derive exhaustive affine solution cases with coefficient realness guards."""

    f, x = sp.sympify(expression), sp.sympify(variable)
    context = normalize_assumptions(assumptions)
    if not isinstance(x, sp.Symbol):
        raise TypeError("affine solving requires a Symbol")
    if context.has(x):
        raise ValueError(
            "parameter assumptions cannot restrict the full coordinate space"
        )

    def result(cases=()):
        return GuardedAffineEquationCertificate(f, x, domain, context, tuple(cases))

    if (
        domain not in (sp.S.Reals, sp.S.Complexes)
        or context is sp.S.false
        or entails(sp.S.false, context) is True
    ):
        return result()
    if domain is sp.S.Reals:
        from .domain_tracking import coordinate_domain_compatible

        if not coordinate_domain_compatible(x, domain):
            return result()
    # Polynomial coefficient extraction must not erase coordinate holes.
    for node in sp.preorder_traversal(f):
        if node.has(x):
            if node == x or node.is_Add or node.is_Mul:
                continue
            if (
                node.is_Pow
                and node.exp.is_Integer is True
                and node.exp.is_nonnegative is True
            ):
                continue
            return result()
        if (
            node.is_finite is not True
            and entails(sp.Q.finite(node), context) is not True
        ):
            return result()
    try:
        polynomial = sp.Poly(f, x)
    except (sp.PolynomialError, TypeError, ValueError):
        return result()
    if not polynomial.is_zero and polynomial.degree() > 1:
        return result()
    slope, offset = polynomial.nth(1), polynomial.nth(0)
    if domain is sp.S.Reals and any(
        c.is_real is not True and entails(sp.Q.real(c), context) is not True
        for c in (slope, offset)
    ):
        return result()
    guards = (
        sp.Ne(slope, 0),
        sp.And(sp.Eq(slope, 0), sp.Eq(offset, 0)),
        sp.And(sp.Eq(slope, 0), sp.Ne(offset, 0)),
    )
    rows = []
    for index, guard in enumerate(guards):
        if guard is sp.S.false or entails(sp.Not(guard), context) is True:
            continue
        condition = (
            sp.S.true
            if guard is sp.S.true or entails(guard, context) is True
            else guard
        )
        value = (
            AffineSolution(sp.FiniteSet(-offset / slope), 1)
            if index == 0
            else AffineSolution(domain, sp.oo)
            if index == 1
            else AffineSolution(sp.S.EmptySet, 0)
        )
        rows.append(ConditionalExpression(value, condition))
    return result(rows)


@dataclass(frozen=True)
class AffineContourCount:
    """Record a guarded affine contour count and its divisor data."""

    count: int | None
    admissible: bool


@dataclass(frozen=True)
class GuardedAffineContourCertificate:
    """Assemble affine contour counts under explicit parameter conditions."""

    expression: sp.Expr
    variable: sp.Symbol
    contour: object
    assumptions: object
    cases: tuple

    @property
    def admissible(self):
        known = tuple(c.value for c in self.cases if c.condition is sp.S.true)
        if len(known) == 1:
            return known[0].admissible
        return (
            True if self.cases and all(c.value.admissible for c in self.cases) else None
        )

    @property
    def zeros_minus_poles(self):
        known = tuple(c.value for c in self.cases if c.condition is sp.S.true)
        return known[0].count if len(known) == 1 and known[0].admissible else None

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "guarded-affine-circle-count-and-explicit-inadmissible-strata"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return bool(self.cases) and self == affine_contour_cases(
                self.expression,
                self.variable,
                self.contour,
                assumptions=self.assumptions,
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
            sp.PolynomialError,
        ):
            return False

    def as_result(self):
        """Project guarded evidence into its mathematical result representation."""

        return PropertyResult(
            self.zeros_minus_poles,
            cases=self.cases,
            complete=self.complete,
            certified=self.certified,
            evidence=(self,),
            source="guarded-affine-circle-count",
        )

    def specialize(self, assumptions):
        """Apply exact parameter substitutions and retain the conditions they must satisfy."""

        return affine_contour_cases(
            self.expression,
            self.variable,
            self.contour,
            assumptions=sp.And(self.assumptions, normalize_assumptions(assumptions)),
        )


def affine_contour_cases(expression, variable, contour, *, assumptions=True):
    """Derive guarded counts for an affine divisor on a supported contour."""

    from .certified_operations import (
        _continuation_contour_is_piecewise_c1,
        _raw_circle_phase,
        winding_number,
    )
    from .domain_tracking import smooth_domain_record

    f, x = sp.sympify(expression), sp.sympify(variable)
    equation = affine_equation_cases(f, x, sp.S.Complexes, assumptions=assumptions)
    context = equation.assumptions

    def result(cases=()):
        return GuardedAffineContourCertificate(f, x, contour, context, tuple(cases))

    if (
        not equation.verify()
        or not _continuation_contour_is_piecewise_c1(contour)
        or context.has(contour.parameter)
    ):
        return result()
    t = contour.parameter
    if f.has(t) or contour.gamma.has(x):
        return result()
    atoms = tuple(e for e in contour.gamma.atoms(sp.exp) if e.has(t))
    if len(atoms) != 1:
        return result()
    exponential = atoms[0]
    phase = _raw_circle_phase(exponential.args[0])
    if (
        phase is None
        or smooth_domain_record(
            phase,
            t,
            sp.Interval(
                sp.Min(contour.lower, contour.upper),
                sp.Max(contour.lower, contour.upper),
            ),
            1,
        )
        is None
    ):
        return result()
    speed = sp.simplify(differentiate(phase, t))
    if speed.has(t) or speed.is_zero is not False:
        return result()
    center, oscillating = contour.gamma.as_independent(exponential, as_Add=True)
    amplitude = oscillating.coeff(exponential)
    if (
        center.has(t)
        or amplitude.has(t)
        or amplitude.is_zero is not False
        or amplitude.is_finite is not True
        or center.is_finite is not True
        or certify_identity_equal(oscillating, amplitude * exponential) is not True
    ):
        return result()
    turns = winding_number(contour, center)
    if type(turns) is not int or turns == 0:
        return result()
    polynomial = sp.Poly(f, x)
    slope, offset = polynomial.nth(1), polynomial.nth(0)
    delta = sp.simplify(
        sp.Abs(slope * amplitude) ** 2 - sp.Abs(slope * center + offset) ** 2
    )
    rows = []
    for guard, value in (
        (sp.And(sp.Ne(slope, 0), delta > 0), AffineContourCount(turns, True)),
        (sp.And(sp.Ne(slope, 0), delta < 0), AffineContourCount(0, True)),
        (sp.And(sp.Ne(slope, 0), sp.Eq(delta, 0)), AffineContourCount(None, False)),
        (sp.And(sp.Eq(slope, 0), sp.Ne(offset, 0)), AffineContourCount(0, True)),
        (sp.And(sp.Eq(slope, 0), sp.Eq(offset, 0)), AffineContourCount(None, False)),
    ):
        if guard is sp.S.false or entails(sp.Not(guard), context) is True:
            continue
        condition = (
            sp.S.true
            if guard is sp.S.true or entails(guard, context) is True
            else guard
        )
        rows.append(ConditionalExpression(value, condition))
    return result(rows)
