from __future__ import annotations

import sympy as sp
from sympy import S

from .. import _semialg
from ..engine import evaluate_property, simplify_condition
from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..results import PropertyResult
from ..source_syntax import logarithm_quotient, normalize_arithmetic
from ..stratification import (
    semantic_condition,
    stratify_boolean_by_parameters,
)
from .common import condition_to_set, is_semialgebraic_expression

# These heads accept every defined complex operand. Logarithms and powers
# need their own zero/branch guards, but may occur inside a real-valued output.
_COMPLEX_UNARY_HEADS = frozenset(
    (sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.Abs, sp.re, sp.im, sp.conjugate)
)
_REAL_LOCUS_HEADS = _COMPLEX_UNARY_HEADS | {sp.Add, sp.Mul, sp.Pow}
_ELEMENTARY_FUNCTION_HEADS = _COMPLEX_UNARY_HEADS | {sp.log}
_ELEMENTARY_HEADS = _REAL_LOCUS_HEADS | {sp.log}


def _real_on_definition(expr, var):
    """Recognize real rational formulas even where poles obscure is_real."""
    if expr.is_real is True:
        return True
    if not expr.is_rational_function(var):
        return False
    numerator, denominator = expr.as_numer_denom()
    return all(
        coefficient.is_real is True and coefficient.is_finite is True
        for polynomial in (numerator, denominator)
        for coefficient in sp.Poly(polynomial, var).all_coeffs()
    )


def _complex_intermediates(expr, var):
    """Detect where real operands cannot describe the whole real-valued locus.

    Entire functions and arithmetic can return real values at complex inputs.
    Checking each operand's real domain would discard those points. A real
    coordinate also prevents assumptions on the caller's symbol from deciding
    output reality before the analysis axis has been fixed.
    """
    if expr.has(sp.I):
        return True
    if expr.func not in _ELEMENTARY_HEADS:
        return False
    if expr.func is sp.log:
        if len(expr.args) != 2:
            return False
        quotient = logarithm_quotient(expr)
        defined = _argument_domains(quotient, var, domain=S.Complexes)
        return (
            defined is S.false
            or isinstance(defined, PropertyResult)
            or _complex_intermediates(quotient, var)
        )
    # Special-function domains use their guarded family declarations. Their
    # unknown SymPy reality flags alone do not establish a complex composition.
    if any(
        node.func not in _ELEMENTARY_FUNCTION_HEADS for node in expr.atoms(sp.Function)
    ):
        return False
    axis = sp.Dummy("real_axis", real=True)
    # Held zero products can have inconsistent parity deductions in SymPy.
    # Query reality on rebuilt arithmetic; callers retain the original tree
    # for definition guards, including any canceled denominators.
    value = normalize_arithmetic(expr).xreplace({var: axis})
    if value.is_real is not True and any(
        parameter.is_real is not True for parameter in expr.free_symbols - {var}
    ):
        return True
    arguments = tuple(
        normalize_arithmetic(argument).xreplace({var: axis}) for argument in expr.args
    )
    real = tuple(_real_on_definition(argument, axis) for argument in arguments)
    if expr.is_Add and real.count(False) <= 1:
        return False
    if (
        expr.is_Mul
        and real.count(False) <= 1
        and all(
            not known_real or argument.as_numer_denom()[0].is_zero is False
            for argument, known_real in zip(arguments, real, strict=True)
        )
    ):
        return False
    return not all(real)


def _real_projection(expr, var):
    axis = sp.Dummy("real_axis", real=True)
    value = sp.expand_complex(normalize_arithmetic(expr).xreplace({var: axis}))
    # Polar expansions can introduce atan2(0, 0) at a defined zero of a
    # radical. They are not interchangeable with the original source there.
    if value.has(sp.arg, sp.atan2):
        return None
    return sp.simplify(sp.re(value)).xreplace({axis: var})


def _real_value_on_domain(expr, var, requested):
    """Prove output reality on a signed real axis, separately from definition.

    The caller must retain the original complex definition guards: replacing
    the coordinate can rebuild held arithmetic and cancel source holes.
    """
    support = condition_to_set(requested, var)
    if not isinstance(support, sp.Set) or support is S.EmptySet:
        return False
    if support.is_subset(sp.Interval.open(0, sp.oo)) is True:
        axis = sp.Dummy("real_axis", positive=True)
    elif support.is_subset(sp.Interval.open(-sp.oo, 0)) is True:
        axis = sp.Dummy("real_axis", negative=True)
    else:
        axis = sp.Dummy("real_axis", real=True)
    return normalize_arithmetic(expr).xreplace({var: axis}).is_real is True


def _pow_real_domain(expr, var):
    if normalize_arithmetic(expr).is_real is False:
        return S.false
    base, exponent = expr.args
    inner = _function_domain_impl(base, var)
    if exponent.is_integer is True:
        if exponent.is_negative:
            return sp.And(inner, sp.Ne(base, 0))
        return inner
    if exponent.is_Rational:
        # Ordinary SymPy Pow uses the complex principal branch even for odd
        # denominators. Explicit real_root expressions have their own structure.
        rel = base > 0 if exponent.is_negative else base >= 0
        return sp.And(inner, rel)
    # A positive real exponent also defines 0**exponent as zero. Negative
    # bases still need an integer exponent on the principal branch.
    if exponent.is_real is True:
        nonnegative_base = sp.Or(base > 0, sp.And(sp.Eq(base, 0), exponent > 0))
        if exponent.is_integer is None:
            # A compound numeric exponent can be an integer even when SymPy
            # has not classified it. Negative bases and 0**0 need that case.
            return sp.And(
                inner,
                sp.Or(
                    sp.Eq(exponent, 0),
                    nonnegative_base,
                    sp.And(base < 0, sp.Contains(exponent, S.Integers)),
                ),
            )
        return sp.And(inner, nonnegative_base)
    return inner


def _argument_domains(expr, var, *, domain):
    """Intersect raw operand domains without rebuilding away constant holes."""
    conditions = []
    unknown = None
    for argument in expr.args:
        if argument == var or (
            argument.is_Atom
            and argument.is_finite is True
            and (domain is S.Complexes or argument.is_real is True)
        ):
            continue
        condition = _function_domain_impl(argument, var, domain=domain)
        if condition is S.false:
            return S.false
        if isinstance(condition, PropertyResult):
            unknown = condition
        else:
            conditions.append(condition)
    return unknown if unknown is not None else sp.And(*conditions)


def _piecewise_domain(expr, var, *, domain):
    """Retain guard definitions on the region where each guard is evaluated."""
    clauses = []
    remaining = S.true
    for value, condition in expr.args:
        if remaining is S.false:
            break
        guards = []
        unknown = None
        for relation in condition.atoms(sp.core.relational.Relational):
            field = (
                S.Complexes
                if isinstance(relation, (sp.Equality, sp.Unequality))
                else S.Reals
            )
            for operand in (relation.lhs, relation.rhs):
                guard = _function_domain_impl(operand, var, domain=field)
                if guard is S.false:
                    return sp.Or(*clauses)
                if isinstance(guard, PropertyResult):
                    unknown = guard
                else:
                    guards.append(guard)
        if unknown is not None:
            return unknown
        defined = sp.And(*guards)
        active = sp.And(remaining, defined, condition)
        if active is not S.false:
            branch = _function_domain_impl(value, var, domain=domain)
            if isinstance(branch, PropertyResult):
                return branch
            clauses.append(sp.And(active, branch))
        remaining = sp.And(remaining, defined, sp.Not(condition))
    return sp.simplify(sp.Or(*clauses))


def _function_domain_impl(expr, var, *, domain=S.Reals, stratified=False):
    """Largest supported real/complex domain condition for ``expr`` in ``var``.

    funcprops owns transcendental structural rules. semialg is invoked only for
    expressions that are structurally semialgebraic.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    real_mode = domain in (S.Reals, "real", "reals", "R", "RR")
    complex_mode = domain in (S.Complexes, "complex", "complexes", "C", "CC")
    if not (real_mode or complex_mode):
        raise ValueError("domain must be Reals or Complexes")
    from ..entire_cancellation import entire_cancellation_proof

    proof = entire_cancellation_proof(expr, var)
    if proof is not None:
        if complex_mode:
            return S.true
        real_axis = sp.Dummy("entire_real_axis", real=True)
        # An entire inner source and a real-coefficient even series define
        # a real value on every real input whenever the inner map is real.
        if proof.inner.xreplace({var: real_axis}).is_real is True:
            return S.true
    if expr.func is sp.log and len(expr.args) == 2:
        quotient = logarithm_quotient(expr)
        defined = _argument_domains(quotient, var, domain=S.Complexes)
        if isinstance(defined, PropertyResult) or defined is S.false:
            return defined
        return _function_domain_impl(
            quotient, var, domain=domain, stratified=stratified
        )
    if expr == var:
        return S.true
    if isinstance(expr, sp.Piecewise) and (real_mode or not expr.has(var)):
        return _piecewise_domain(
            expr, var, domain=S.Reals if real_mode else S.Complexes
        )
    if not expr.has(var):
        if expr.func in _ELEMENTARY_HEADS:
            # A held constant may normalize to a finite value while an inner
            # source operation is undefined, as in exp(log(0)). Complex input
            # guards retain that hole without rejecting legitimate intermediates.
            operands = _argument_domains(expr, var, domain=S.Complexes)
            if isinstance(operands, PropertyResult) or operands is S.false:
                return operands
            return sp.And(
                sp.Contains(
                    normalize_arithmetic(expr), S.Reals if real_mode else S.Complexes
                ),
                operands,
            )
        return sp.Contains(expr, S.Reals if real_mode else S.Complexes)
    source_defined = S.true
    if expr.is_Pow:
        # Exponent-zero rules may simplify the value, but cannot define an
        # undefined source operand. Complex intermediates use these guards too.
        source_defined = _argument_domains(expr, var, domain=S.Complexes)
        if isinstance(source_defined, PropertyResult) or source_defined is S.false:
            return source_defined
    if real_mode and _complex_intermediates(expr, var):
        # Real-valued output can arise from complex intermediate values. Use
        # the complex definition domain, then impose reality on the whole
        # expression; testing each operand as a real function is unsound.
        if normalize_arithmetic(expr).is_real is False:
            return S.false
        defined = _function_domain_impl(expr, var, domain=S.Complexes)
        if isinstance(defined, PropertyResult):
            return defined
        axis = sp.Dummy("real_axis", real=True)
        value = normalize_arithmetic(expr).xreplace({var: axis})
        if value.is_real is True:
            return defined
        if expr.is_Function and any(
            parameter.is_real is None for parameter in expr.free_symbols - {var}
        ):
            return PropertyResult(primary="unknown_domain", source="funcprops")
        expanded = sp.expand_complex(value)
        if expanded.has(sp.arg, sp.atan2):
            # A polar formula can be undefined at a perfectly defined zero of
            # a radical. Without a chart/seam proof it cannot describe the
            # exact real locus; finite-domain consumers can evaluate points.
            return PropertyResult(primary="unknown_domain", source="funcprops")
        reality = sp.Eq(sp.simplify(sp.im(expanded)), 0).xreplace({axis: var})
        return simplify_condition(sp.And(defined, reality))

    if complex_mode:
        # Entire elementary heads and arithmetic retain the definition domains
        # of complex operands, without imposing real-operand branch guards.
        if expr.func in (sp.Add, sp.Mul):
            operands = _argument_domains(expr, var, domain=S.Complexes)
            return (
                operands
                if isinstance(operands, PropertyResult)
                else simplify_condition(operands)
            )
        if expr.func in _COMPLEX_UNARY_HEADS:
            return _function_domain_impl(expr.args[0], var, domain=S.Complexes)
        if expr.func is sp.Pow and expr.exp.is_Rational:
            return simplify_condition(
                sp.And(source_defined, sp.Ne(expr.base, 0))
                if expr.exp.is_negative
                else source_defined
            )
        if expr.func is sp.log and len(expr.args) == 1:
            defined = _function_domain_impl(expr.args[0], var, domain=S.Complexes)
            if isinstance(defined, PropertyResult):
                return defined
            return simplify_condition(sp.And(defined, sp.Ne(expr.args[0], 0)))

    if real_mode and expr.func is sp.Pow:
        if expr.exp.is_Rational and not expr.exp.is_Integer:
            return simplify_condition(
                sp.And(source_defined, _pow_real_domain(expr, var))
            )
        if is_semialgebraic_expression(expr, var):
            try:
                return sp.And(source_defined, sp.sympify(_semialg.domain(expr, var)))
            except SYMBOLIC_QUERY_ERRORS:
                pass
        # Symbolic exponents have genuinely parameter-dependent real domains
        # (integer, negative-integer, and noninteger cases).  The catalogue is
        # substantially more informative than the conservative x>0 fallback.
        if expr.exp.free_symbols:
            reg = evaluate_property(expr, "RealDomain", var=var, mode="real")
            if reg.primary is not None:
                dom = semantic_condition(reg.primary)
                # SymPy defines x**0 as 1 even at x=0; the catalogue-derived
                # source treats 0^0 as indeterminate.  SymPy semantics take
                # precedence in funcprops.
                return sp.And(source_defined, sp.Or(sp.Eq(expr.exp, 0), dom))
        return simplify_condition(sp.And(source_defined, _pow_real_domain(expr, var)))

    # Constant operands can also contain held undefined source operations.
    if real_mode and expr.func in (sp.Add, sp.Mul):
        operands = _argument_domains(expr, var, domain=S.Reals)
        return (
            operands
            if isinstance(operands, PropertyResult)
            else simplify_condition(operands)
        )

    # Trigonometric reciprocal/pole domains are clearer and more useful in
    # structural form than the equivalent integer-membership catalogue rule.
    if (
        real_mode
        and expr.func in (sp.tan, sp.sec, sp.cot, sp.csc)
        and len(expr.args) == 1
    ):
        a = expr.args[0]
        inner = (
            _function_domain_impl(a, var, domain=S.Reals)
            if a.has(var) and a != var
            else S.true
        )
        denom = sp.cos(a) if expr.func in (sp.tan, sp.sec) else sp.sin(a)
        return simplify_condition(sp.And(inner, sp.Ne(denom, 0)))

    constraints = []

    # semialg is an exact backend for semialgebraic expressions only.
    if real_mode and is_semialgebraic_expression(expr, var):
        try:
            constraints.append(sp.sympify(_semialg.domain(expr, var)))
        except _semialg.SemialgUnavailable:
            pass
        except SYMBOLIC_QUERY_ERRORS:
            pass

    mode = "real" if real_mode else "complex"
    prop = "RealDomain" if real_mode else "ComplexDomain"
    reg = evaluate_property(expr, prop, var=var, mode=mode)
    if reg.primary is not None:
        constraints.append(sp.sympify(reg.primary))
    elif reg.cases:
        # Preserve parameter-dependent domains as a Boolean piecewise equivalent:
        # OR(guard AND domain-value). Unknown default stays unasserted.
        terms = []
        for case in reg.cases:
            if case.value in (S.true, S.false) or isinstance(
                case.value, (sp.logic.boolalg.Boolean, sp.core.relational.Relational)
            ):
                terms.append(sp.And(case.condition, case.value))
        if terms:
            constraints.append(sp.Or(*terms))

    # Explicit elementary rules not represented as standalone SymPy heads in the registry.
    if real_mode:
        if expr.func is sp.exp:
            constraints.append(S.true)
        elif expr.func is sp.log and len(expr.args) == 1:
            constraints.append(expr.args[0] > 0)
        elif expr.func is sp.asin or expr.func is sp.acos:
            a = expr.args[0]
            constraints.append(sp.And(a >= -1, a <= 1))
        elif expr.func is sp.acosh:
            constraints.append(expr.args[0] >= 1)
        elif expr.func is sp.atanh:
            a = expr.args[0]
            constraints.append(sp.And(a > -1, a < 1))

    # Every varying argument must itself be defined.
    for arg in getattr(expr, "args", ()):
        if arg == var or not getattr(arg, "has", lambda *_: False)(var):
            continue
        d = _function_domain_impl(
            arg, var, domain=S.Reals if real_mode else S.Complexes
        )
        if isinstance(d, PropertyResult):
            return d
        constraints.append(sp.sympify(d))

    if not constraints:
        return PropertyResult(primary="unknown_domain", source="funcprops")
    try:
        result = simplify_condition(sp.And(source_defined, *constraints))
    except SYMBOLIC_QUERY_ERRORS:
        result = sp.And(source_defined, *constraints)
    if stratified and real_mode:
        return stratify_boolean_by_parameters(
            result, var, source="domain-parameter-stratification"
        )
    return result


def domain(expr, var, *, domain=S.Reals, stratified=False):
    """Cached public wrapper around the lazy real/complex domain prover."""
    from ..proof_cache import property_proof_context

    complex_mode = domain in (S.Complexes, "complex", "complexes", "C", "CC")
    if not (complex_mode or domain in (S.Reals, "real", "reals", "R", "RR")):
        raise ValueError("domain must be Reals or Complexes")
    return property_proof_context(expr, var).natural_domain(
        complex_domain=complex_mode, stratified=stratified
    )
