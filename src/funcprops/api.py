"""Public routing layer for function-property queries.

The wrappers in this module also normalize ``ConditionalExpression`` inputs.  The
underlying property engines remain ordinary SymPy-expression analyzers.
"""

from __future__ import annotations

import functools
import inspect

import sympy as sp
from sympy import S

from .assumptions import normalize_assumptions
from .conditional import (
    combine_assumptions,
    normalize_conditional_input,
    restrict_domain,
)
from .geometry import (
    function_boundary_behavior as _function_boundary_behavior,
)
from .geometry import (
    function_geometry as _function_geometry,
)
from .geometry import (
    function_level_boundedness as _function_level_boundedness,
)
from .geometry import (
    function_mode_existence as _function_mode_existence,
)
from .real_analysis.boundedness import function_boundedness as _function_boundedness
from .real_analysis.complete_monotonicity import (
    function_complete_monotonicity as _function_complete_monotonicity,
)
from .real_analysis.convexity import function_convexity as _function_convexity
from .real_analysis.differentiability import (
    function_differentiability as _function_differentiability,
)
from .real_analysis.domain import function_domain as _function_domain
from .real_analysis.mapping import (
    function_bijective as _function_bijective,
)
from .real_analysis.mapping import (
    function_injective as _function_injective,
)
from .real_analysis.mapping import (
    function_surjective as _function_surjective,
)
from .real_analysis.monotonicity import function_monotonicity as _function_monotonicity
from .real_analysis.oscillation import function_oscillation as _function_oscillation
from .real_analysis.range import function_range as _function_range
from .real_analysis.sign import function_sign as _function_sign
from .real_analysis.smoothness import function_smoothness as _function_smoothness
from .real_analysis.structural_properties import (
    function_homogeneity as _function_homogeneity,
)
from .real_analysis.structural_properties import (
    function_periodicity as _function_periodicity,
)
from .real_analysis.structural_properties import (
    function_symmetry as _function_symmetry,
)
from .real_analysis.zeros import function_zeros as _function_zeros
from .singularities import (
    function_analytic as _function_analytic,
)
from .singularities import (
    function_branchcuts as _function_branchcuts,
)
from .singularities import (
    function_branchpoints as _function_branchpoints,
)
from .singularities import (
    function_continuous as _function_continuous,
)
from .singularities import (
    function_discontinuities as _function_discontinuities,
)
from .singularities import (
    function_meromorphic as _function_meromorphic,
)
from .singularities import (
    function_poles as _function_poles,
)
from .singularities import (
    function_singularities as _function_singularities,
)
from .singularities import (
    function_singularity_analysis as _function_singularity_analysis,
)
from .stratification import resolve_result_assumptions
from .transcendental.complex_roots import (
    function_complex_zeros as _function_complex_zeros,
)
from .transformation import (
    function_change_of_variables as _function_change_of_variables,
)
from .transformation import (
    function_determinant_nonvanishing as _function_determinant_nonvanishing,
)
from .transformation import (
    function_jacobian as _function_jacobian,
)
from .transformation import (
    function_local_invertibility as _function_local_invertibility,
)
from .transformation import (
    function_transformation_geometry as _function_transformation_geometry,
)


def _signature_with_assumptions(sig):
    params = [p for p in sig.parameters.values() if not p.name.startswith("_")]
    if "assumptions" in sig.parameters:
        return sig.replace(parameters=params)
    insertion = len(params)
    for i, param in enumerate(params):
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            insertion = i
            break
    assumptions_param = inspect.Parameter(
        "assumptions", inspect.Parameter.KEYWORD_ONLY, default=True
    )
    params.insert(insertion, assumptions_param)
    return sig.replace(parameters=params)


def _conditional_wrapper(fn, *, domain_mode="ordinary"):
    sig = inspect.signature(fn)
    has_native_assumptions = "assumptions" in sig.parameters

    @functools.wraps(fn)
    def wrapped(expr, *args, **kwargs):
        private = [name for name in kwargs if name.startswith("_")]
        if private:
            raise TypeError(
                f"internal keyword is not part of the public API: {private[0]}"
            )
        normalized = normalize_conditional_input(expr)
        public_assumptions = normalize_assumptions(kwargs.pop("assumptions", True))
        combined = normalize_assumptions(
            combine_assumptions(public_assumptions, normalized.condition)
        )

        bound = sig.bind_partial(normalized.expr, *args, **kwargs)
        var = bound.arguments.get(
            "var", bound.arguments.get("variable", bound.arguments.get("variables"))
        )
        if var is None and args:
            var = args[0]
        if var is not None:
            var = sp.sympify(var)

        if has_native_assumptions:
            kwargs["assumptions"] = combined
        elif "domain" in sig.parameters and domain_mode == "ordinary":
            domain = bound.arguments.get("domain", sig.parameters["domain"].default)
            if normalized.condition is not S.true:
                kwargs["domain"] = restrict_domain(domain, normalized.condition, var)

        if (
            "domain" in sig.parameters
            and domain_mode == "ordinary"
            and has_native_assumptions
        ):
            domain = bound.arguments.get("domain", sig.parameters["domain"].default)
            if normalized.condition is not S.true:
                kwargs["domain"] = restrict_domain(domain, normalized.condition, var)

        result = fn(normalized.expr, *args, **kwargs)
        result = resolve_result_assumptions(result, combined)
        if domain_mode == "natural-domain" and normalized.condition is not S.true:
            restriction = normalized.condition
            if isinstance(result, sp.Set) and not isinstance(var, sp.Tuple):
                from .real_analysis.common import condition_to_set

                restricted_set = condition_to_set(restriction, var)
                if restricted_set is not None:
                    return sp.Intersection(result, restricted_set)
                return sp.And(sp.Contains(var, result), restriction)
            if isinstance(result, sp.Basic):
                return sp.And(result, restriction)
        return result

    wrapped.__signature__ = _signature_with_assumptions(sig)
    return wrapped


function_boundedness = _conditional_wrapper(_function_boundedness)
function_convexity = _conditional_wrapper(_function_convexity)
function_complete_monotonicity = _conditional_wrapper(_function_complete_monotonicity)
function_differentiability = _conditional_wrapper(_function_differentiability)
function_domain = _conditional_wrapper(_function_domain, domain_mode="natural-domain")
function_bijective = _conditional_wrapper(_function_bijective)
function_injective = _conditional_wrapper(_function_injective)
function_surjective = _conditional_wrapper(_function_surjective)
function_monotonicity = _conditional_wrapper(_function_monotonicity)
function_oscillation = _conditional_wrapper(_function_oscillation)
function_range = _conditional_wrapper(_function_range)
function_sign = _conditional_wrapper(_function_sign)
function_smoothness = _conditional_wrapper(_function_smoothness)
function_homogeneity = _conditional_wrapper(_function_homogeneity)
function_periodicity = _conditional_wrapper(_function_periodicity)
function_symmetry = _conditional_wrapper(_function_symmetry)
function_zeros = _conditional_wrapper(_function_zeros)
function_analytic = _conditional_wrapper(_function_analytic)


def _restrict_condition_locus(locus, condition, var):
    combined = sp.And(sp.sympify(locus), sp.sympify(condition))
    # Branch-cut conditions commonly carry Contains(var, Reals).  Under that
    # guard, refine re(var)/im(var) before reducing inequalities.
    if var is not None and combined.has(sp.Contains(var, S.Reals)):
        combined = sp.refine(combined, sp.Q.real(var))
        combined = combined.xreplace({sp.re(var): var, sp.im(var): S.Zero})
    try:
        reduced = (
            sp.reduce_inequalities(combined, var)
            if var is not None
            else sp.simplify(combined)
        )
    except (NotImplementedError, TypeError, ValueError):
        reduced = sp.simplify(combined)
    return reduced


def function_branchcuts(expr, var, *, assumptions=True, mode="conditions"):
    normalized = normalize_conditional_input(expr)
    assumptions = normalize_assumptions(
        combine_assumptions(assumptions, normalized.condition)
    )
    raw = _function_branchcuts(normalized.expr, var, assumptions=assumptions, mode=mode)
    if normalized.condition is S.true or mode == "jumps":
        return raw
    if mode == "conditions":
        out = []
        for locus in raw:
            restricted = _restrict_condition_locus(
                locus, normalized.condition, sp.sympify(var)
            )
            if restricted is not S.false and restricted != S.false:
                out.append(restricted)
        return tuple(out)
    if mode == "union":
        return _restrict_condition_locus(raw, normalized.condition, sp.sympify(var))
    if mode == "records":
        from .results import Singularity

        out = []
        for record in raw:
            locus = _restrict_condition_locus(
                record.condition, normalized.condition, sp.sympify(var)
            )
            if locus is S.false or locus == S.false:
                continue
            out.append(
                Singularity(
                    record.kind, locus, record.guard, record.multiplicity, record.source
                )
            )
        return tuple(out)
    return raw


function_branchpoints = _conditional_wrapper(_function_branchpoints)
function_continuous = _conditional_wrapper(_function_continuous)
function_discontinuities = _conditional_wrapper(_function_discontinuities)
function_meromorphic = _conditional_wrapper(_function_meromorphic)
function_poles = _conditional_wrapper(_function_poles)


def function_singularities(
    expr,
    var,
    domain=S.Complexes,
    *,
    assumptions=True,
    return_result=False,
):
    """Return the Boolean singularity locus, preserving function restrictions.

    ``Dummy`` analysis variables are normalized through an ordinary proxy
    symbol.  Several SymPy set/solver paths introduce their own dummies; using
    a proxy prevents those implementation symbols from leaking into the public
    singularity locus and makes the query invariant to ``Symbol`` versus
    ``Dummy`` callers.
    """
    assumptions = normalize_assumptions(assumptions)
    original_var = sp.sympify(var)
    normalized = normalize_conditional_input(expr)
    concrete_expr = sp.sympify(normalized.expr)
    restriction = sp.sympify(normalized.condition)
    analysis_var = original_var
    if isinstance(original_var, sp.Dummy):
        analysis_var = sp.Symbol("_funcprops_var")
        replacement = {original_var: analysis_var}
        concrete_expr = concrete_expr.xreplace(replacement)
        restriction = restriction.xreplace(replacement)
        assumptions = sp.sympify(assumptions).xreplace(replacement)
    if restriction is not S.true:
        from .results import ConditionalExpression

        concrete_expr = ConditionalExpression(concrete_expr, restriction)
    result = _function_singularities(
        concrete_expr,
        analysis_var,
        domain,
        assumptions=assumptions,
        return_result=return_result,
    )
    if analysis_var != original_var and isinstance(result, sp.Basic):
        result = result.xreplace({analysis_var: original_var})
    return result


function_singularity_analysis = _conditional_wrapper(_function_singularity_analysis)
function_boundary_behavior = _conditional_wrapper(_function_boundary_behavior)
function_level_boundedness = _conditional_wrapper(_function_level_boundedness)
function_mode_existence = _conditional_wrapper(_function_mode_existence)
function_geometry = _conditional_wrapper(_function_geometry)


def function_jacobian(expressions, variables, *, return_result=False):
    """Return a transformation Jacobian matrix or its detailed certificate."""
    return _function_jacobian(expressions, variables, return_result=return_result)


def function_determinant_nonvanishing(
    expressions, variables, *, domain=S.Reals, assumptions=True, return_result=False
):
    """Return whether the Jacobian determinant is nonzero throughout the domain."""
    return _function_determinant_nonvanishing(
        expressions,
        variables,
        domain=domain,
        assumptions=assumptions,
        return_result=return_result,
    )


def function_local_invertibility(
    expressions, variables, *, domain=S.Reals, assumptions=True, return_result=False
):
    """Return whether local invertibility is certified throughout the domain."""
    return _function_local_invertibility(
        expressions,
        variables,
        domain=domain,
        assumptions=assumptions,
        return_result=return_result,
    )


def function_change_of_variables(
    expressions, variables, *, domain=S.Reals, assumptions=True
):
    return _function_change_of_variables(
        expressions, variables, domain=domain, assumptions=assumptions
    )


def function_transformation_geometry(
    expressions, variables, *, domain=S.Reals, assumptions=True
):
    return _function_transformation_geometry(
        expressions, variables, domain=domain, assumptions=assumptions
    )


# Complex rectangle isolation cannot in general intersect an arbitrary Boolean
# condition with a rectangle without a certified planar-set decomposition.  We
# nevertheless accept unconditional ConditionalExpression wrappers and reject only
# genuinely restricted inputs explicitly rather than leaking a SympifyError.
def function_complex_zeros(expr, *args, assumptions=True, **kwargs):
    normalized = normalize_conditional_input(expr)
    assumptions = normalize_assumptions(
        combine_assumptions(assumptions, normalized.condition)
    )
    if assumptions is not S.true:
        raise NotImplementedError(
            "assumption-restricted complex rectangle root isolation requires "
            "certified planar-domain transport"
        )
    return _function_complex_zeros(normalized.expr, *args, **kwargs)


__all__ = [name for name in globals() if name.startswith("function_")]
