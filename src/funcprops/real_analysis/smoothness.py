"""Joint continuity, differentiability, smoothness, and analyticity analysis."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp
from sympy import S

from .. import _semialg
from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..results import Analyticity, Continuity
from ..singularities import (
    function_analytic,
    function_continuous,
    function_discontinuities,
)
from ..stratification import evaluate_parameter_strata
from .common import (
    combine_natural_domain_condition,
    condition_to_set,
)
from .domain import function_domain


@dataclass(frozen=True)
class SmoothnessResult:
    """Certified regularity information on a requested real domain."""

    continuity: Continuity
    differentiability_order: int | sp.Expr | None
    smooth: bool | None
    analytic: Analyticity
    exceptional_loci: tuple = ()
    evidence: tuple = ()


def _exception_loci(records):
    """Return unique singularity conditions while preserving source order."""
    loci = []
    for record in records:
        condition = getattr(record, "condition", record)
        if condition not in loci:
            loci.append(condition)
    return tuple(loci)


def _locus_intersects_domain(locus, domain, var):
    """Conservatively decide whether a locus can meet a requested domain."""
    domain_set = condition_to_set(domain, var)
    locus_set = condition_to_set(locus, var)
    if domain_set is not None and locus_set is not None:
        try:
            overlap = sp.Intersection(domain_set, locus_set)
        except (TypeError, ValueError, NotImplementedError):
            overlap = None
        if overlap is not None:
            if overlap is S.EmptySet or overlap == S.EmptySet:
                return False
            is_empty = getattr(overlap, "is_empty", None)
            if is_empty is True:
                return False
            if is_empty is False:
                return True

    try:
        satisfiable = sp.satisfiable(sp.And(sp.sympify(domain), sp.sympify(locus)))
    except (TypeError, ValueError, NotImplementedError):
        return True
    return satisfiable is not False


def _domain_loci(records, domain, var):
    return tuple(
        locus
        for locus in _exception_loci(records)
        if _locus_intersects_domain(locus, domain, var)
    )


def _structurally_smooth(expr, var):
    """Recognize globally smooth expression trees without derivative probing.

    The rule set intentionally contains only closure operations that cannot
    introduce a real singularity: polynomial arithmetic, nonnegative integer
    powers, and composition with entire elementary functions.
    """
    expr = sp.sympify(expr)
    if not expr.has(var):
        return True
    if expr == var:
        return True
    if expr.is_Add or expr.is_Mul:
        return all(_structurally_smooth(arg, var) for arg in expr.args)
    if expr.is_Pow:
        base, exponent = expr.args
        return bool(exponent.is_Integer and exponent.is_nonnegative) and (
            _structurally_smooth(base, var)
        )
    entire_heads = {sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.erf}
    if expr.func in entire_heads and len(expr.args) == 1:
        return _structurally_smooth(expr.args[0], var)
    return False


def function_smoothness(expr, var, *, domain=True, max_order=6, _domain_ready=False):
    """Analyze regularity up to ``max_order`` on the requested real domain.

    Finite derivative probing never certifies :math:`C^\\infty`.  Smoothness is
    true only when analyticity proves it; it is false only after a witnessed
    finite-order failure, and otherwise remains unknown.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if isinstance(max_order, bool) or not isinstance(max_order, int) or max_order < 1:
        raise ValueError("max_order must be a positive integer")

    natural_domain = function_domain(expr, var)
    requested_domain = (
        sp.sympify(domain)
        if _domain_ready
        else combine_natural_domain_condition(natural_domain, domain, var)
    )
    if not _domain_ready:
        split = evaluate_parameter_strata(
            requested_domain,
            var,
            lambda branch_domain: function_smoothness(
                expr,
                var,
                domain=branch_domain,
                max_order=max_order,
                _domain_ready=True,
            ),
            source="smoothness-parameter-stratification",
        )
        if split is not None:
            return split
    analyticity = function_analytic(expr, var, domain=requested_domain)
    if analyticity is Analyticity.ANALYTIC:
        continuity = function_continuous(expr, var, domain=requested_domain)
        exceptions = list(
            _domain_loci(function_discontinuities(expr, var), requested_domain, var)
        )
        return SmoothnessResult(
            continuity,
            sp.oo,
            True,
            analyticity,
            tuple(exceptions),
            ("analytic-implies-smooth",),
        )

    backend = None
    if _semialg.eligible_problem(expr, var, domain=requested_domain):
        try:
            backend = _semialg.function_smoothness(
                expr, var, domain=requested_domain, max_order=max_order
            )
            # Negative/finite regularity results are safe to use immediately.
            # A backend claim of C-infinity is validated below through the
            # requested finite derivative order before it can strengthen the
            # public result.
            if backend.smooth is not True:
                continuity = (
                    Continuity.CONTINUOUS
                    if backend.continuous is True
                    else Continuity.DISCONTINUOUS
                    if backend.continuous is False
                    else Continuity.UNKNOWN
                )
                exceptions = [
                    backend.continuity_exceptions,
                    *backend.derivative_exceptions.values(),
                ]
                exceptions = [
                    locus for locus in exceptions if locus not in (S.false, False)
                ]
                return SmoothnessResult(
                    continuity,
                    backend.differentiability_order,
                    backend.smooth,
                    analyticity,
                    tuple(exceptions),
                    (("semialg", backend),),
                )
        except (_semialg.SemialgUnavailable, *SYMBOLIC_QUERY_ERRORS):
            backend = None

    continuity = function_continuous(expr, var, domain=requested_domain)
    exceptions = list(
        _domain_loci(function_discontinuities(expr, var), requested_domain, var)
    )

    if continuity is Continuity.CONTINUOUS and _structurally_smooth(expr, var):
        return SmoothnessResult(
            continuity,
            sp.oo,
            True,
            analyticity,
            tuple(exceptions),
            ("smooth-structural-closure",),
        )

    order = 0 if continuity is Continuity.CONTINUOUS else None
    failure_proved = False
    domain_set = condition_to_set(requested_domain, var)
    if domain_set is None:
        return SmoothnessResult(
            continuity, order, None, analyticity, tuple(exceptions), ()
        )

    from ..proof_cache import property_proof_context

    context = property_proof_context(expr, var, domain=requested_domain)
    for derivative_order in range(1, max_order + 1):
        try:
            derivative = context.derivative(derivative_order)
        except (TypeError, ValueError, NotImplementedError):
            break

        loci = _domain_loci(
            function_discontinuities(derivative, var), requested_domain, var
        )
        for locus in loci:
            if locus not in exceptions:
                exceptions.append(locus)
        if loci:
            failure_proved = True
            break

        try:
            continuous_domain = sp.calculus.util.continuous_domain(
                derivative, var, domain_set
            )
        except (TypeError, ValueError, NotImplementedError):
            # An unsupported continuity query is uncertainty, not evidence of
            # either continuity or discontinuity.
            break

        if continuous_domain == domain_set:
            order = derivative_order
            continue

        missing = sp.Complement(domain_set, continuous_domain)
        if missing is not S.EmptySet and missing != S.EmptySet:
            failure_proved = True
        break

    smooth = False if failure_proved else None
    evidence = (("verified-derivatives-through", order),) if order is not None else ()
    if (
        not failure_proved
        and backend is not None
        and backend.smooth is True
        and order == max_order
    ):
        order = sp.oo
        smooth = True
        evidence = (*evidence, ("semialg", backend))
    return SmoothnessResult(
        continuity,
        order,
        smooth,
        analyticity,
        tuple(exceptions),
        evidence,
    )
