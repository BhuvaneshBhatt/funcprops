"""Whole-expression regularity evidence; syntax cuts are only candidates."""

from functools import lru_cache

import sympy as sp

from .coverage_checker import _formula_equal
from .domain_tracking import coordinate_domain_compatible, track_domain
from .exactness import certify_equal
from .exceptions import SYMBOLIC_QUERY_ERRORS
from .source_syntax import differentiate

NONSMOOTH = (sp.Abs, sp.sign, sp.floor, sp.ceiling)


def real_affine_argument(expression, variables):
    """A nonconstant affine real map crosses its zero/integer hyperplanes."""
    try:
        p = sp.Poly(expression, *variables)
        if p.total_degree() != 1 or any(v.is_real is not True for v in variables):
            return False
        coefficients = p.coeffs()
        return all(
            c.is_real is True and c.is_finite is True for c in coefficients
        ) and any(p.diff(v).as_expr().is_zero is False for v in variables)
    except SYMBOLIC_QUERY_ERRORS:
        return False


def _global_identities(f, *, complex_mode=False):
    """Recognize supported whole-source identities without treating inner branch cuts as final obstructions."""

    if not isinstance(f, sp.Expr) or not f.args:
        return f
    args = tuple(
        _global_identities(a, complex_mode=complex_mode)
        if isinstance(a, sp.Expr)
        else a
        for a in f.args
    )
    f = f.func(*args)
    if complex_mode:
        if f.func is sp.re:
            u = f.args[0]
            return (u + sp.conjugate(u)) / 2
        if f.func is sp.im:
            u = f.args[0]
            return (u - sp.conjugate(u)) / (2 * sp.I)
        if (
            f.is_Pow
            and f.base.func is sp.Abs
            and isinstance(f.exp, sp.Integer)
            and f.exp > 0
            and f.exp % 2 == 0
        ):
            u = f.base.args[0]
            return (u * sp.conjugate(u)) ** (f.exp // 2)
        return (
            sp.expand(
                f, deep=False, multinomial=False, power_base=False, power_exp=False
            )
            if f.is_Add or f.is_Mul
            else f
        )
    if f.is_Mul:
        factors = list(f.args)
        for sign in tuple(factors):
            if sign.func is not sp.sign or sign.args[0].is_real is not True:
                continue
            u = sign.args[0]
            for _i, factor in enumerate(factors):
                if factor == u or factor == sp.Abs(u):
                    factors.remove(sign)
                    factors.remove(factor)
                    factors.append(sp.Abs(u) if factor == u else u)
                    return _global_identities(sp.Mul(*factors))
                if (
                    factor.is_Pow
                    and factor.base == u
                    and isinstance(factor.exp, sp.Integer)
                    and factor.exp > 0
                ):
                    factors = list(f.args)
                    factors.remove(sign)
                    factors.remove(factor)
                    return _global_identities(
                        sp.Mul(*factors, u ** (factor.exp - 1), sp.Abs(u))
                    )
    # If the whole enclosing expression is even in an Abs value, its sign can
    # be removed. Structural equality after substitution is an exact identity.
    for absolute in sorted(f.atoms(sp.Abs), key=sp.default_sort_key):
        u = absolute.args[0]
        if u.is_real is not True:
            continue
        t = sp.Dummy("absolute_value", real=True)
        lifted = f.xreplace({absolute: t})
        if lifted.xreplace({t: -t}) == lifted:
            return _global_identities(f.xreplace({absolute: u}))
    return f


def source_defined_on_query(f, x, D):
    """Finite real structural definition, independently of continuity of heads."""
    if not coordinate_domain_compatible(x, D):
        return False
    if f == x:
        return True
    if not f.has(x):
        return f.is_real is True and f.is_finite is True
    if f.is_Add or f.is_Mul:
        return all(source_defined_on_query(a, x, D) for a in f.args)
    if f.is_Pow and isinstance(f.exp, sp.Integer) and f.exp >= 0:
        return source_defined_on_query(f.base, x, D)
    if f.func in (
        *NONSMOOTH,
        sp.exp,
        sp.sin,
        sp.cos,
        sp.sinh,
        sp.cosh,
        sp.tanh,
        sp.erf,
        sp.erfc,
    ):
        return source_defined_on_query(f.args[0], x, D)
    if isinstance(f, sp.Piecewise):
        from .coverage_cells import source_cells

        for _, condition in f.args:
            for relation in condition.atoms(sp.core.relational.Relational):
                try:
                    polynomial = sp.Poly(relation.lhs - relation.rhs, x)
                    if any(
                        c.is_real is not True or c.is_finite is not True
                        for c in polynomial.coeffs()
                    ):
                        return False
                except SYMBOLIC_QUERY_ERRORS:
                    return False
        cells = source_cells(f, x, D)
        return cells is not None and all(
            source_defined_on_query(g, x, d) for g, d in cells
        )
    record = track_domain(f, x, D)
    return record.complete and record.effective == D


@lru_cache(maxsize=512)
def regularity_normal_form(expression, variable, domain=sp.S.Reals, complex_mode=False):
    """Exact identities only, guarded by full raw-source definition on the query."""
    f = sp.sympify(expression)
    if (
        not isinstance(variable, sp.Symbol)
        or sp.count_ops(f) > 100
        or not f.has(sp.Abs, sp.sign, sp.Piecewise, sp.re, sp.im)
    ):
        return f
    try:
        result = _global_identities(f, complex_mode=complex_mode)
        if complex_mode:
            from .local_analyticity import complex_definition_domain

            return (
                result
                if result != f
                and complex_definition_domain(f, variable, sp.S.Complexes)
                == sp.S.Complexes
                else f
            )
        from .real_analysis.common import condition_to_set
        from .real_analysis.restricted_simplify import simplify_on_domain

        D = domain if isinstance(domain, sp.Set) else condition_to_set(domain, variable)
        if D is None or D is sp.S.EmptySet:
            return f
        record = track_domain(f, variable, D)
        if (
            not record.complete or record.effective != D
        ) and not source_defined_on_query(f, variable, D):
            return f
        if isinstance(result, sp.Piecewise):
            from .real_analysis.piecewise import piecewise_decomposition

            decomposition = piecewise_decomposition(result, variable, D)
            if decomposition.complete and decomposition.branches:
                branches = []
                for b in decomposition.branches:
                    value, _ = simplify_on_domain(
                        _global_identities(b.expression), variable, b.domain
                    )
                    replacements = {}
                    for node in value.atoms(sp.sign):
                        u = node.args[0]
                        if u.is_real is not True:
                            continue
                        for sign, condition in ((1, u > 0), (-1, u < 0)):
                            support = condition_to_set(condition, variable)
                            if (
                                support is not None
                                and b.domain.is_subset(support) is True
                            ):
                                replacements[node] = sp.Integer(sign)
                    value = value.xreplace(replacements)
                    branches.append((value, b.domain))
                candidate = next(
                    (g for g, d in branches if isinstance(d, sp.Interval)),
                    branches[0][0],
                )
                if all(
                    _formula_equal(g, candidate)
                    or (
                        isinstance(d, sp.FiniteSet)
                        and all(
                            _formula_equal(
                                g.subs(variable, p), candidate.subs(variable, p)
                            )
                            for p in d
                        )
                    )
                    for g, d in branches
                ):
                    result = candidate
        # Strictly off all Abs zeros, the exact restricted rewrite holds in a
        # neighborhood of every requested point, including closed query ends.
        if result.has(sp.Abs) and not result.has(sp.Min, sp.Max, sp.Piecewise):
            zeros = [
                condition_to_set(sp.Eq(a.args[0], 0), variable)
                for a in result.atoms(sp.Abs)
            ]
            if all(
                Z is not None and sp.Intersection(D, Z) is sp.S.EmptySet for Z in zeros
            ):
                result, _ = simplify_on_domain(result, variable, D)
        return result
    except (AttributeError, *SYMBOLIC_QUERY_ERRORS):
        return f


def discontinuity_at(expression, variable, point, assumptions=sp.S.true):
    """True/False/None from actual whole-function one-sided limits and value."""
    try:
        from .singularities.records import _piecewise_branch_for_side

        sides = []
        for direction in ("-", "+"):
            source = (
                _piecewise_branch_for_side(expression, variable, point, direction)
                if isinstance(expression, sp.Piecewise)
                else expression
            )
            if source is None:
                return None
            value = sp.limit(source, variable, point, dir=direction)
            if (
                value.has(sp.Limit)
                or value is sp.nan
                or isinstance(value, sp.AccumBounds)
            ):
                return None
            sides.append(value)
        at = expression.subs(variable, point)
        if at.is_finite is not True:
            return None
        equal = [
            certify_equal(v, at, assumptions=assumptions)
            if v.is_finite is True
            else False
            if v in (sp.oo, -sp.oo, sp.zoo)
            else None
            for v in sides
        ]
        return (
            True if False in equal else False if all(v is True for v in equal) else None
        )
    except (AttributeError, *SYMBOLIC_QUERY_ERRORS):
        return None


def filter_discontinuity_candidate(expression, variable, record, assumptions=sp.S.true):
    """Keep only proved jumps; unresolved candidate guards remain explicit."""
    from .results import Singularity

    if record.condition is sp.S.false or record.guard is sp.S.false:
        return None
    if (
        expression.func in NONSMOOTH
        and real_affine_argument(expression.args[0], (variable,))
    ) or (
        record.source == "registry"
        and expression.func not in NONSMOOTH
        and expression.is_Function
        and expression.args == (variable,)
    ):
        return record
    try:
        condition = record.condition
        roots = (
            sp.solveset(condition.lhs - condition.rhs, variable, domain=sp.S.Reals)
            if isinstance(condition, sp.Equality)
            else None
        )
        if isinstance(roots, sp.FiniteSet):
            verdicts = [
                discontinuity_at(expression, variable, p, assumptions) for p in roots
            ]
            if verdicts and all(v is False for v in verdicts):
                return None
            if verdicts and all(v is True for v in verdicts):
                return record
    except (AttributeError, *SYMBOLIC_QUERY_ERRORS):
        pass
    unresolved = sp.Predicate("unresolved_discontinuity")(
        sp.Tuple(expression, variable, record.condition)
    )
    return Singularity(
        record.kind,
        record.condition,
        sp.And(record.guard, unresolved),
        source="unresolved-whole-discontinuity",
    )


def piecewise_failure_witness(certificate):
    """Find a supported branch or seam obstruction to the requested regularity."""

    if certificate.continuous is False:
        return True
    return any(
        left is not None
        and right is not None
        and sp.sympify(left).is_finite is True
        and sp.sympify(right).is_finite is True
        and certify_equal(left, right) is False
        for left, right in certificate.derivative_limits
    )


def entire_inner(expression, variable, assumptions=sp.S.true):
    """A sufficient *global* entire-source theorem, not local meromorphicity."""
    f = sp.sympify(expression)
    if f == variable:
        return True
    if not f.has(variable):
        return f.is_finite is True
    if f.is_Add or f.is_Mul:
        return all(entire_inner(a, variable, assumptions) for a in f.args)
    from .entire_cancellation import even_root_argument

    matched = even_root_argument(f)
    if matched is not None:
        from .entire_cancellation import _entire_data

        return _entire_data(f, variable) is not None
    if f.is_Pow:
        return (
            isinstance(f.exp, sp.Integer)
            and f.exp >= 0
            and entire_inner(f.base, variable, assumptions)
        )
    if f.func in (sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.erf, sp.erfc, sp.erfi):
        return entire_inner(f.args[0], variable, assumptions)
    if (
        f.func in (sp.besselj, sp.besseli)
        and len(f.args) == 2
        and not f.args[0].has(variable)
        and f.args[0].is_integer is True
        and entire_inner(f.args[1], variable, assumptions)
    ):
        return True
    from .engine import evaluate_property

    dependent = [a for a in f.args if a.has(variable)]
    return (
        f.is_Function
        and dependent == [variable]
        and all(a.is_finite is True for a in f.args if not a.has(variable))
        and evaluate_property(
            f, "Entire", mode="complex", var=variable, assumptions=assumptions
        ).primary
        is sp.S.true
    )


def primitive_subject(expression, variable):
    """Identify a supported primitive subject for a regularity theorem."""

    return expression.is_Function and [
        a for a in expression.args if a.has(variable)
    ] == [variable]


def whole_nonmeromorphic_witness(expression, variable, records):
    """Replay selected local classifications of the whole expression."""
    if primitive_subject(expression, variable):
        return True
    from .certified_operations import classify_singularity

    for record in records:
        if not isinstance(record.condition, sp.Equality):
            continue
        try:
            roots = sp.solveset(
                record.condition.lhs - record.condition.rhs,
                variable,
                domain=sp.S.Complexes,
            )
            if not isinstance(roots, sp.FiniteSet):
                continue
            for point in roots:
                certificate = classify_singularity(
                    expression, variable, point, return_certificate=True
                )
                if (
                    certificate is not None
                    and certificate.kind in ("branch_point", "essential")
                    and certificate.verify()
                ):
                    return True
        except (AttributeError, *SYMBOLIC_QUERY_ERRORS):
            continue
    return False


def meromorphic_composition_premises(expression, variable, assumptions=sp.S.true):
    """A meromorphic outer needs an entire, nonconstant inner (or finite constant).

    Catalogue facts in one argument do not establish joint meromorphicity when
    several argument slots vary. Nonconstancy must hold at the parameter values
    in scope, not merely at generic parameter values.
    """
    from .exactness import certify_identity_zero
    from .source_syntax import normalize_arithmetic

    if primitive_subject(expression, variable):
        return True
    if not expression.is_Function:
        return False
    args = [a for a in expression.args if a.has(variable)]
    if len(args) != 1 or not entire_inner(args[0], variable, assumptions):
        return False
    inner = normalize_arithmetic(args[0])
    if not inner.has(variable):
        return normalize_arithmetic(expression).is_finite is True
    derivative = differentiate(inner, variable)
    if derivative.is_zero is False:
        return True
    # One exact finite derivative value proves nonconstancy. Parameter values
    # must be certified nonzero pointwise, rather than nonzero as an identity.
    for point in (sp.S.Zero, sp.S.One):
        value = derivative.subs(variable, point)
        if value.is_finite is True and value.is_zero is False:
            return True
    if not derivative.free_symbols - {variable}:
        return certify_identity_zero(derivative) is False
    try:
        p = sp.Poly(inner, variable)
        return any(
            power[0] > 0 and coefficient.is_zero is False
            for power, coefficient in p.terms()
        )
    except SYMBOLIC_QUERY_ERRORS:
        return False
