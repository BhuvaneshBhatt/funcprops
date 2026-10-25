"""Transformation geometry and change-of-variables certificates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp
from sympy import S
from sympy.assumptions import Q, ask

from ._semialg import SemialgUnavailable
from .exactness import certify_identity_equal, certify_zero
from .exceptions import SYMBOLIC_QUERY_ERRORS
from .real_analysis.common import (
    condition_to_set,
    normalize_domain_condition,
    normalize_expressions,
    normalize_variables,
)
from .registry_derivatives import JacobianCertificate, registry_jacobian
from .results import Continuity, Sign, TruthValue
from .source_syntax import same_data


def _domain_condition(domain, variables):
    try:
        return normalize_domain_condition(domain, variables)
    except (TypeError, ValueError):
        return None


def _truth_from_nonzero(expr, assumptions=S.true):
    expr = sp.sympify(expr)
    zero = certify_zero(expr, assumptions=assumptions)
    if zero is True:
        source = "identically-zero" if assumptions is S.true else "assumption-zero"
        return TruthValue.FALSE, source
    if zero is False:
        source = "constant-nonzero" if not expr.free_symbols else "assumption-nonzero"
        return TruthValue.TRUE, source
    return TruthValue.UNKNOWN, "unresolved"


def _scalar_sign_exclusion(determinant, variable, support):
    """Reuse bounded scalar sign rules on the established real C1 support.

    Factor signs can establish nonvanishing. Mixed signs on disconnected
    support do not by themselves establish a zero between the components.
    """
    from .real_analysis.sign_rules import (
        rational_polynomials,
        rational_sign,
        threshold_sign,
        trig_sign,
    )

    result = rational_sign(determinant, variable, support)
    if result is Sign.UNKNOWN:
        result = threshold_sign(determinant, variable, support)
    if result is not Sign.UNKNOWN:
        return result
    if determinant.is_Mul:
        orientation = 1
        for factor in determinant.args:
            value = _scalar_sign_exclusion(factor, variable, support)
            if value not in (Sign.POSITIVE, Sign.NEGATIVE):
                return Sign.UNKNOWN
            orientation *= 1 if value is Sign.POSITIVE else -1
        return Sign.POSITIVE if orientation > 0 else Sign.NEGATIVE
    if determinant.func is sp.exp:
        polynomials = rational_polynomials(determinant.args[0], variable)
        if polynomials is not None and polynomials[1].degree() == 0:
            return Sign.POSITIVE
    return trig_sign(determinant, variable, support)


def _scalar_zero_witness(determinant, variable, support):
    """Reuse finite affine trigonometric zero sets; a single checked root suffices."""
    from .real_analysis.zeros import zeros

    if not isinstance(support, sp.Interval) or not all(
        p.is_real is True
        and p.is_finite is True
        and not p.free_symbols
        and not p.has(sp.Float)
        for p in (support.start, support.end)
    ):
        return None
    factors = sp.Mul.make_args(determinant)
    for factor in factors:
        if factor.func not in (sp.sin, sp.cos):
            continue
        try:
            polynomial = sp.Poly(factor.args[0], variable, domain=sp.QQ)
        except (sp.PolynomialError, sp.CoercionFailed):
            continue
        if (
            polynomial.degree() != 1
            or (abs(polynomial.nth(1)) * (support.end - support.start) <= 32)
            is not S.true
        ):
            continue
        roots = zeros(factor, variable, domain=support)
        if isinstance(roots, sp.FiniteSet) and len(roots) <= 16:
            for point in sp.ordered(roots):
                if (
                    support.contains(point) is S.true
                    and certify_zero(determinant.subs(variable, point)) is True
                ):
                    return point
    return None


def _map_support(variables, domain, assumptions):
    """Keep coordinate assumptions and nonempty real input support as premises."""
    from .domain_tracking import coordinate_domain_compatible

    assumptions = sp.sympify(assumptions)
    condition = _domain_condition(domain, variables)
    if condition is None or sp.And(condition, assumptions) is S.false:
        return None
    if len(variables) == 1:
        support = condition_to_set(condition, variables[0])
        if assumptions is not S.true and not assumptions.free_symbols.difference(
            variables
        ):
            restricted = condition_to_set(sp.And(condition, assumptions), variables[0])
            if isinstance(restricted, sp.Set):
                support = restricted
        if (
            not isinstance(support, sp.Set)
            or support.is_empty is not False
            or not coordinate_domain_compatible(variables[0], support)
        ):
            return None
        return condition, support
    axes = (
        domain.args
        if isinstance(domain, sp.ProductSet)
        else (S.Reals,) * len(variables)
    )
    if len(axes) != len(variables) or any(
        not coordinate_domain_compatible(v, axis)
        for v, axis in zip(variables, axes, strict=True)
    ):
        return None
    if condition is not S.true:
        # Existence over parameter values does not establish a nonempty fiber
        # for every admissible parameter. Leave that geometry unresolved.
        if condition.free_symbols.difference(variables):
            return None
        from ._semialg import is_satisfiable

        if is_satisfiable(condition, variables) is not True:
            return None
    return condition, domain


def _c1_real_map(expressions, variables, domain, assumptions):
    """Establish the real C1 hypothesis before invoking the inverse theorem."""
    from .assumptions import entails
    from .domain_tracking import track_domain
    from .real_analysis.domain import domain as natural_domain
    from .real_analysis.smoothness import SmoothnessResult, smoothness
    from .regularity_evidence import entire_inner

    var_arg = variables[0] if len(variables) == 1 else variables
    try:
        supported = _map_support(variables, domain, assumptions)
        if supported is None:
            return False
        condition, support = supported
        context = sp.And(condition, assumptions)
        for expr in expressions:
            covered = False
            if len(variables) == 1:
                record = track_domain(expr, variables[0], support)
                covered = record.complete and record.effective == support
            if not covered:
                guard = natural_domain(expr, var_arg)
                if (
                    not isinstance(guard, sp.logic.boolalg.Boolean)
                    or entails(guard, assumptions=context) is not True
                ):
                    return False
            if all(entire_inner(expr, v, assumptions) for v in variables):
                continue
            result = smoothness(
                expr,
                var_arg,
                domain=domain,
                max_order=1,
                return_result=True,
            )
            if not isinstance(result, SmoothnessResult):
                return False
            order = result.differentiability_order
            if (
                result.continuity is not Continuity.CONTINUOUS
                or order is None
                or not (order == sp.oo or order >= 1)
            ):
                return False
    except (SemialgUnavailable, *SYMBOLIC_QUERY_ERRORS):
        return False
    return True


@dataclass(frozen=True)
class DeterminantNonvanishingCertificate:
    """Bind a real C1 map and its domain to a Jacobian nonvanishing decision."""

    determinant: Any
    variables: tuple[sp.Symbol, ...]
    domain: Any
    classification: TruthValue
    source: str
    witness: Any = None
    assumptions: Any = S.true
    expressions: tuple = ()

    @property
    def primary(self):
        return self.classification

    @property
    def scope(self):
        return "real-C1-map-Jacobian-nonvanishing-on-requested-domain"

    def verify(self):
        """Replay the bound map, its real C1 premises and determinant decision."""
        if type(self.expressions) is not tuple or not self.expressions:
            return False
        try:
            jacobian = registry_jacobian(self.expressions, self.variables)
            if self.source == "scalar-zero-witness":
                if (
                    type(self) is not DeterminantNonvanishingCertificate
                    or len(self.variables) != 1
                    or len(self.expressions) != 1
                    or self.classification is not TruthValue.FALSE
                    or any(e.has(sp.Float) for e in self.expressions)
                ):
                    return False
                determinant = sp.factor(sp.trigsimp(jacobian.jacobian.det()))
                support = _map_support(self.variables, self.domain, self.assumptions)
                return (
                    same_data(self.determinant, determinant)
                    and support is not None
                    and isinstance(self.witness, sp.Expr)
                    and self.witness.is_real is True
                    and self.witness.is_finite is True
                    and support[1].contains(self.witness) is S.true
                    and sp.simplify(
                        sp.sympify(self.assumptions).subs(
                            self.variables[0], self.witness
                        )
                    )
                    is S.true
                    and _c1_real_map(
                        self.expressions, self.variables, self.domain, self.assumptions
                    )
                    and certify_zero(determinant.subs(self.variables[0], self.witness))
                    is True
                )
            expected = _det_nonzero_from_jacobian(
                self.expressions,
                self.variables,
                jacobian,
                domain=self.domain,
                assumptions=self.assumptions,
            )
            return same_data(self, expected)
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


@dataclass(frozen=True)
class LocalInvertibilityCertificate:
    """Record applicability of the real C1 inverse function theorem.

    FALSE means a theorem hypothesis fails. It does not rule out a continuous
    or nondifferentiable inverse, as illustrated by the cube map at zero.
    """

    expressions: tuple[Any, ...]
    variables: tuple[sp.Symbol, ...]
    jacobian: JacobianCertificate
    determinant: Any
    nonvanishing: DeterminantNonvanishingCertificate
    classification: TruthValue
    source: str = "inverse-function-theorem"

    @property
    def primary(self):
        return self.classification

    @property
    def scope(self):
        return "real-C1-inverse-function-theorem-applicability"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        if (
            type(self.jacobian) is not JacobianCertificate
            or type(self.nonvanishing) is not DeterminantNonvanishingCertificate
            or type(self.expressions) is not tuple
            or type(self.variables) is not tuple
        ):
            return False
        if len(self.expressions) != len(self.variables):
            return (
                self.classification is TruthValue.UNKNOWN
                and self.source == "nonsquare-map"
                and self.determinant is S.NaN
                and self.jacobian.expressions == self.expressions
                and self.jacobian.variables == self.variables
                and self.jacobian.verify()
                and self.nonvanishing.variables == self.variables
                and self.nonvanishing.expressions == self.expressions
                and self.nonvanishing.determinant is S.NaN
                and self.nonvanishing.classification is TruthValue.UNKNOWN
                and self.nonvanishing.source == "nonsquare-map"
                and self.nonvanishing.verify()
            )
        if self.classification in (TruthValue.TRUE, TruthValue.FALSE) and any(
            sp.sympify(e).has(sp.Float) for e in self.expressions
        ):
            return False
        if (
            self.jacobian.expressions != self.expressions
            or self.jacobian.variables != self.variables
            or self.nonvanishing.variables != self.variables
            or self.nonvanishing.expressions != self.expressions
            or certify_identity_equal(self.nonvanishing.determinant, self.determinant)
            is not True
            or not self.jacobian.verify()
        ):
            return False
        if (
            certify_identity_equal(self.jacobian.jacobian.det(), self.determinant)
            is not True
        ):
            return False
        if self.classification is TruthValue.TRUE:
            return (
                _c1_real_map(
                    self.expressions,
                    self.variables,
                    self.nonvanishing.domain,
                    self.nonvanishing.assumptions,
                )
                and self.nonvanishing.classification is TruthValue.TRUE
                and self.nonvanishing.verify()
            )
        if self.classification is TruthValue.FALSE:
            return (
                self.nonvanishing.classification is TruthValue.FALSE
                and self.nonvanishing.verify()
            )
        return self.nonvanishing.classification is TruthValue.UNKNOWN or (
            self.source == "c1-real-map-unproved"
            and self.nonvanishing.classification is TruthValue.TRUE
            and not _c1_real_map(
                self.expressions,
                self.variables,
                self.nonvanishing.domain,
                self.nonvanishing.assumptions,
            )
        )


@dataclass(frozen=True)
class ChangeOfVariablesCertificate:
    """Record a substitution's Jacobian, orientation and absolute determinant."""

    expressions: tuple[Any, ...]
    variables: tuple[sp.Symbol, ...]
    jacobian: JacobianCertificate
    determinant: Any
    absolute_determinant: Any
    local_invertibility: LocalInvertibilityCertificate
    classification: TruthValue
    orientation: Sign
    domain: Any = S.Reals
    source: str = "local-change-of-variables"

    @property
    def primary(self):
        return self.classification

    @property
    def volume_factor(self):
        return self.absolute_determinant

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        if (
            type(self.local_invertibility) is not LocalInvertibilityCertificate
            or type(self.jacobian) is not JacobianCertificate
            or type(self.expressions) is not tuple
            or type(self.variables) is not tuple
        ):
            return False
        if (
            self.expressions != self.local_invertibility.expressions
            or self.variables != self.local_invertibility.variables
            or self.jacobian != self.local_invertibility.jacobian
            or self.domain != self.local_invertibility.nonvanishing.domain
            or not self.jacobian.verify()
            or not self.local_invertibility.verify()
        ):
            return False
        if len(self.expressions) != len(self.variables):
            return (
                self.determinant is S.NaN
                and self.absolute_determinant is S.NaN
                and self.classification is TruthValue.UNKNOWN
                and self.orientation is Sign.UNKNOWN
                and self.local_invertibility.classification is TruthValue.UNKNOWN
            )
        if certify_identity_equal(
            self.determinant, self.local_invertibility.determinant
        ) is not True or self.orientation is not _orientation(
            self.determinant, self.local_invertibility.nonvanishing.assumptions
        ):
            return False
        if (
            certify_identity_equal(self.absolute_determinant, sp.Abs(self.determinant))
            is not True
        ):
            return False
        if self.classification is TruthValue.TRUE:
            return self.local_invertibility.classification is TruthValue.TRUE
        if self.classification is TruthValue.FALSE:
            return self.local_invertibility.classification is TruthValue.FALSE
        if self.classification is TruthValue.UNKNOWN:
            return self.local_invertibility.classification is TruthValue.UNKNOWN
        return False


@dataclass(frozen=True)
class TransformationGeometry:
    """Combine Jacobian, invertibility and change-of-variables conclusions."""

    expressions: tuple[Any, ...]
    variables: tuple[sp.Symbol, ...]
    domain: Any
    jacobian: JacobianCertificate
    determinant: Any
    determinant_nonvanishing: DeterminantNonvanishingCertificate
    local_invertibility: LocalInvertibilityCertificate
    change_of_variables: ChangeOfVariablesCertificate


def jacobian(expressions, variables, *, return_result=False):
    """Return the Jacobian matrix; request its certificate with ``return_result=True``."""
    certificate = registry_jacobian(
        normalize_expressions(expressions), normalize_variables(variables)
    )
    return certificate if return_result else certificate.jacobian


def _det_nonzero_from_jacobian(
    expressions, variables, jacobian, *, domain=S.Reals, assumptions=S.true
):
    """Prove a Jacobian determinant nonzero under supported exact coefficient and domain guards."""

    if len(expressions) != len(variables):
        return DeterminantNonvanishingCertificate(
            S.NaN,
            variables,
            domain,
            TruthValue.UNKNOWN,
            "nonsquare-map",
            assumptions=assumptions,
            expressions=expressions,
        )
    det = sp.factor(sp.trigsimp(jacobian.jacobian.det()))
    if any(sp.sympify(e).has(sp.Float) for e in expressions):
        return DeterminantNonvanishingCertificate(
            det,
            variables,
            domain,
            TruthValue.UNKNOWN,
            "inexact-jacobian",
            assumptions=assumptions,
            expressions=expressions,
        )
    if det.has(sp.nan, sp.oo, -sp.oo, sp.zoo) or not _c1_real_map(
        expressions, variables, domain, assumptions
    ):
        return DeterminantNonvanishingCertificate(
            det,
            variables,
            domain,
            TruthValue.UNKNOWN,
            "c1-real-map-unproved",
            assumptions=assumptions,
            expressions=expressions,
        )
    verdict, source = _truth_from_nonzero(det, assumptions)
    if verdict is not TruthValue.UNKNOWN:
        return DeterminantNonvanishingCertificate(
            det,
            variables,
            domain,
            verdict,
            source,
            assumptions=assumptions,
            expressions=expressions,
        )

    condition = _domain_condition(domain, variables)
    if condition is None:
        return DeterminantNonvanishingCertificate(
            det,
            variables,
            domain,
            TruthValue.UNKNOWN,
            "domain-unresolved",
            assumptions=assumptions,
            expressions=expressions,
        )

    # A parameter is not a transformation coordinate.  Semialgebraic zero
    # search must not choose parameter values as if they were points in the
    # requested domain.
    unresolved_parameters = det.free_symbols.difference(variables)
    if unresolved_parameters:
        return DeterminantNonvanishingCertificate(
            det,
            variables,
            domain,
            TruthValue.UNKNOWN,
            "parameter-dependent-determinant",
            assumptions=assumptions,
            expressions=expressions,
        )
    if len(variables) == 1:
        support = condition_to_set(sp.And(condition, assumptions), variables[0])
        sign = _scalar_sign_exclusion(det, variables[0], support)
        if sign in (Sign.POSITIVE, Sign.NEGATIVE):
            return DeterminantNonvanishingCertificate(
                det,
                variables,
                domain,
                TruthValue.TRUE,
                "scalar-sign-exclusion",
                witness=sign,
                assumptions=assumptions,
                expressions=expressions,
            )
    try:
        from ._semialg import is_satisfiable

        query = sp.And(condition, assumptions, sp.Eq(det, 0))
        sat = is_satisfiable(query, variables)
        if sat is False:
            return DeterminantNonvanishingCertificate(
                det,
                variables,
                domain,
                TruthValue.TRUE,
                "semialgebraic-no-zero",
                assumptions=assumptions,
                expressions=expressions,
            )
        if sat is True:
            return DeterminantNonvanishingCertificate(
                det,
                variables,
                domain,
                TruthValue.FALSE,
                "semialgebraic-zero-witness",
                witness=query,
                assumptions=assumptions,
                expressions=expressions,
            )
    except (SemialgUnavailable, *SYMBOLIC_QUERY_ERRORS):
        pass
    if len(variables) == 1:
        point = _scalar_zero_witness(det, variables[0], support)
        if point is not None:
            return DeterminantNonvanishingCertificate(
                det,
                variables,
                domain,
                TruthValue.FALSE,
                "scalar-zero-witness",
                witness=point,
                assumptions=assumptions,
                expressions=expressions,
            )
    return DeterminantNonvanishingCertificate(
        det,
        variables,
        domain,
        TruthValue.UNKNOWN,
        "unresolved",
        assumptions=assumptions,
        expressions=expressions,
    )


def determinant_nonvanishing(
    expressions, variables, *, domain=S.Reals, assumptions=S.true, return_result=False
):
    """Check Jacobian nonvanishing after proving a real C1 map on the query.

    Unproved source definition, incompatible coordinate assumptions, empty or
    unresolved support, and unproved C1 regularity return UNKNOWN.
    """
    expressions = normalize_expressions(expressions)
    variables = normalize_variables(variables)
    jacobian = registry_jacobian(expressions, variables)
    certificate = _det_nonzero_from_jacobian(
        expressions, variables, jacobian, domain=domain, assumptions=assumptions
    )
    return certificate if return_result else certificate.classification


def _local_invertibility_from_facts(expressions, variables, jacobian, nonvanishing):
    if len(expressions) != len(variables):
        return LocalInvertibilityCertificate(
            expressions,
            variables,
            jacobian,
            S.NaN,
            nonvanishing,
            TruthValue.UNKNOWN,
            "nonsquare-map",
        )
    determinant = sp.factor(sp.trigsimp(jacobian.jacobian.det()))
    classification = nonvanishing.classification
    source = "inverse-function-theorem"
    if (
        classification is TruthValue.UNKNOWN
        and nonvanishing.source == "c1-real-map-unproved"
    ):
        source = "c1-real-map-unproved"
    return LocalInvertibilityCertificate(
        expressions,
        variables,
        jacobian,
        determinant,
        nonvanishing,
        classification,
        source,
    )


def local_invertibility(
    expressions, variables, *, domain=S.Reals, assumptions=S.true, return_result=False
):
    """Return whether the inverse function theorem certifies local invertibility."""
    expressions = normalize_expressions(expressions)
    variables = normalize_variables(variables)
    jacobian = registry_jacobian(expressions, variables)
    nonvanishing = _det_nonzero_from_jacobian(
        expressions, variables, jacobian, domain=domain, assumptions=assumptions
    )
    certificate = _local_invertibility_from_facts(
        expressions, variables, jacobian, nonvanishing
    )
    return certificate if return_result else certificate.classification


def _orientation(det, assumptions=S.true):
    try:
        if ask(Q.positive(det), assumptions) is True:
            return Sign.POSITIVE
        if ask(Q.negative(det), assumptions) is True:
            return Sign.NEGATIVE
    except SYMBOLIC_QUERY_ERRORS:
        pass
    return Sign.UNKNOWN


def _change_of_variables_from_facts(
    expressions, variables, jacobian, local_invertibility, *, domain, assumptions
):
    determinant = local_invertibility.determinant
    absolute_determinant = sp.Abs(determinant) if determinant is not S.NaN else S.NaN
    return ChangeOfVariablesCertificate(
        expressions,
        variables,
        jacobian,
        determinant,
        absolute_determinant,
        local_invertibility,
        local_invertibility.classification,
        _orientation(determinant, assumptions)
        if determinant is not S.NaN
        else Sign.UNKNOWN,
        domain,
    )


def change_of_variables(expressions, variables, *, domain=S.Reals, assumptions=S.true):
    """Certify the local differential change-of-variables factor ``Abs(det J)``."""
    expressions = normalize_expressions(expressions)
    variables = normalize_variables(variables)
    jacobian = registry_jacobian(expressions, variables)
    nonvanishing = _det_nonzero_from_jacobian(
        expressions, variables, jacobian, domain=domain, assumptions=assumptions
    )
    local = _local_invertibility_from_facts(
        expressions, variables, jacobian, nonvanishing
    )
    return _change_of_variables_from_facts(
        expressions,
        variables,
        jacobian,
        local,
        domain=domain,
        assumptions=assumptions,
    )


def transformation_geometry(
    expressions, variables, *, domain=S.Reals, assumptions=S.true
):
    """Return the combined transformation-geometry summary."""
    expressions = normalize_expressions(expressions)
    variables = normalize_variables(variables)
    jacobian = registry_jacobian(expressions, variables)
    nonvanishing = _det_nonzero_from_jacobian(
        expressions, variables, jacobian, domain=domain, assumptions=assumptions
    )
    local = _local_invertibility_from_facts(
        expressions, variables, jacobian, nonvanishing
    )
    change_of_variables = _change_of_variables_from_facts(
        expressions,
        variables,
        jacobian,
        local,
        domain=domain,
        assumptions=assumptions,
    )
    return TransformationGeometry(
        expressions,
        variables,
        domain,
        jacobian,
        local.determinant,
        nonvanishing,
        local,
        change_of_variables,
    )
