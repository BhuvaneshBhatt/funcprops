from __future__ import annotations

import sympy as sp
from sympy import S

from .. import _semialg
from ..engine import evaluate_property
from ..exactness import certify_zero
from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..results import ConditionalExpression, PropertyResult
from ..stratification import (
    evaluate_parameter_strata,
    normalize_cases,
    semantic_condition,
)
from ..transcendental.algebraize import algebraize
from .common import (
    affine_real_parameter_guard,
    combine_domain_condition,
    condition_to_set,
    is_full_natural_domain,
    original_definition_guard,
    set_to_condition,
)
from .domain import (
    _complex_intermediates,
    _real_projection,
    _real_value_on_domain,
    domain,
)
from .image_rules import _quadratic_image, attainment_preserving_range, exact_image
from .monotonic_certificates import (
    matching_partition,
    monotonic_partition,
    range_from_monotonic_partition,
)
from .special_functions import (
    parameter_guard,
    positive_axis_range_strata,
    special_function_range_strata,
)


def _lambda_condition(value, y):
    if isinstance(value, sp.Lambda) and len(value.variables) == 1:
        return sp.sympify(value.expr).xreplace({value.variables[0]: y})
    return None


def _refine_interval_attainment(expr, var, cond, y):
    s = condition_to_set(cond, y)
    if not isinstance(s, sp.Interval):
        return cond
    natural = domain(expr, var)
    ds = condition_to_set(natural, var)
    if ds is None:
        return cond
    left_open = s.left_open
    right_open = s.right_open
    if s.start not in (S.NegativeInfinity, S.Infinity):
        try:
            sol = sp.solveset(sp.Eq(expr, s.start), var, domain=ds)
            if sol is S.EmptySet:
                left_open = True
            elif isinstance(sol, (sp.FiniteSet, sp.ImageSet, sp.Union)):
                left_open = False
        except SYMBOLIC_QUERY_ERRORS:
            pass
    if s.end not in (S.NegativeInfinity, S.Infinity):
        try:
            sol = sp.solveset(sp.Eq(expr, s.end), var, domain=ds)
            if sol is S.EmptySet:
                right_open = True
            elif isinstance(sol, (sp.FiniteSet, sp.ImageSet, sp.Union)):
                right_open = False
        except SYMBOLIC_QUERY_ERRORS:
            pass
    return set_to_condition(
        sp.Interval(s.start, s.end, left_open=left_open, right_open=right_open), y
    )


def _registry_range(expr, var, y):
    r = evaluate_property(expr, "Range", var=var, mode="real")
    pguard = parameter_guard(expr, var, "Range")
    if r.primary is not None:
        cond = _lambda_condition(r.primary, y)
        if cond is None:
            return None
        cond = _refine_interval_attainment(expr, var, cond, y)
        if pguard is S.true:
            return cond
        return normalize_cases(
            (ConditionalExpression(cond, pguard),),
            source="registry-range-stratification",
        )
    if r.cases:
        cases = []
        for c in r.cases:
            cond = _lambda_condition(c.value, y)
            if cond is not None:
                cond = _refine_interval_attainment(expr, var, cond, y)
                cases.append(
                    ConditionalExpression(
                        cond, sp.And(semantic_condition(c.condition), pguard)
                    )
                )
        if cases:
            return normalize_cases(cases, source="registry-range-stratification")
    return None


def _monotone_image_interval(outer, X, inner_set):
    """Assemble a monotone interval image from owned endpoint values and one-sided limits."""

    from ..results import Monotonicity
    from .monotonicity import monotonicity

    dom = set_to_condition(inner_set, X)
    m = monotonicity(outer, X, domain=dom)
    inc = m in (Monotonicity.STRICTLY_INCREASING, Monotonicity.NONDECREASING)
    if m not in (Monotonicity.STRICTLY_INCREASING, Monotonicity.STRICTLY_DECREASING):
        return None
    try:
        continuous = (
            sp.calculus.util.continuous_domain(outer, X, inner_set) == inner_set
        )
    except SYMBOLIC_QUERY_ERRORS:
        continuous = False
    # Audited entire real error functions and real-order modified Bessel
    # functions on the positive axis have no jumps or missing interior values.
    if outer.func in (sp.erf, sp.erfc, sp.erfi) and outer.args == (X,):
        continuous = True
    if (
        outer.func in (sp.besseli, sp.besselk)
        and outer.args[1] == X
        and outer.args[0].is_real is True
    ):
        continuous = inner_set.is_subset(sp.Interval.open(0, sp.oo)) is True
    if not continuous:
        return None

    def image_endpoint(v, is_left, is_open):
        if v is S.NegativeInfinity:
            return sp.limit(outer, X, -sp.oo)
        if v is S.Infinity:
            return sp.limit(outer, X, sp.oo)
        if is_open:
            try:
                return sp.limit(outer, X, v, dir="+" if is_left else "-")
            except SYMBOLIC_QUERY_ERRORS:
                pass
        return sp.simplify(outer.subs(X, v))

    try:
        a = image_endpoint(inner_set.start, True, inner_set.left_open)
        b = image_endpoint(inner_set.end, False, inner_set.right_open)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    if inc:
        lo, hi = a, b
        lo_open = inner_set.left_open or inner_set.start in (
            S.NegativeInfinity,
            S.Infinity,
        )
        hi_open = inner_set.right_open or inner_set.end in (
            S.NegativeInfinity,
            S.Infinity,
        )
    else:
        lo, hi = b, a
        lo_open = inner_set.right_open or inner_set.end in (
            S.NegativeInfinity,
            S.Infinity,
        )
        hi_open = inner_set.left_open or inner_set.start in (
            S.NegativeInfinity,
            S.Infinity,
        )
    if lo is S.NegativeInfinity:
        lo_open = True
    if hi is S.Infinity:
        hi_open = True
    return sp.Interval(lo, hi, left_open=lo_open, right_open=hi_open)


def _composition_range(expr, var, y, domain_condition, *, source_constraints=None):
    varying = [(i, a) for i, a in enumerate(getattr(expr, "args", ())) if a.has(var)]
    if len(varying) != 1 or expr.func in (sp.Add, sp.Mul, sp.Piecewise):
        return None
    i, inner = varying[0]
    inner_domain = domain(inner, var)
    if isinstance(inner_domain, PropertyResult):
        return None
    if inner_domain is not S.true:
        from ..stratification import implication_guard

        if implication_guard(domain_condition, inner_domain, var) is not S.true:
            return None
    if inner == var or (expr.func is sp.Pow and (i != 0 or not expr.exp.is_Rational)):
        return None
    X = sp.Dummy("X", real=True)
    args = list(expr.args)
    args[i] = X
    outer = expr.func(*args)
    audited = outer.func in (
        sp.exp,
        sp.log,
        sp.sin,
        sp.cos,
        sp.sinh,
        sp.cosh,
        sp.tanh,
        sp.atan,
        sp.floor,
        sp.ceiling,
        sp.Pow,
    )
    # Audited images impose the outer domain in the image coordinate. The inner
    # query retains every user constraint and derives its own natural domain.
    inner_constraints = (
        source_constraints
        if audited and source_constraints is not None
        else domain_condition
    )
    u = sp.Dummy("u", real=True)
    rc = range(inner, var, u, constraints=inner_constraints)
    if isinstance(rc, PropertyResult):
        return None
    inner_set = condition_to_set(rc, u)
    if not isinstance(inner_set, sp.Set):
        return None
    out = exact_image(outer, X, inner_set)
    if out is None and isinstance(inner_set, sp.Interval):
        out = _monotone_image_interval(outer, X, inner_set)
    return set_to_condition(out, y) if out is not None else None


def _scale_interval(s, A, B, sign):
    def finite_image(v):
        if v is S.NegativeInfinity:
            return S.NegativeInfinity if sign > 0 else S.Infinity
        if v is S.Infinity:
            return S.Infinity if sign > 0 else S.NegativeInfinity
        return sp.simplify(A * v + B)

    if sign > 0:
        return sp.Interval(
            finite_image(s.start),
            finite_image(s.end),
            left_open=s.left_open,
            right_open=s.right_open,
        )
    return sp.Interval(
        finite_image(s.end),
        finite_image(s.start),
        left_open=s.right_open,
        right_open=s.left_open,
    )


def _affine_transform(expr, var, y, domain):
    """Transform an exact inner range through ``A*g(x) + B``.

    Parameter-dependent coefficient signs are preserved as conditional strata.
    """
    # Identify A*g(x)+B where A and B are independent of the input variable.
    terms = sp.Add.make_args(sp.expand(expr))
    const = sum((t for t in terms if not t.has(var)), S.Zero)
    dep = sp.simplify(expr - const)
    coeff, rest = dep.as_independent(var, as_Add=False)
    if coeff.has(var) or not rest.has(var) or rest == expr:
        return None
    u = sp.Dummy("u", real=True)
    inner = range(rest, var, u, constraints=domain)

    def transform(cond, extra=S.true):
        ss = condition_to_set(cond, u)
        if not isinstance(ss, sp.Interval):
            return None
        A = sp.sympify(coeff)
        B = sp.sympify(const)
        if A.is_positive:
            return set_to_condition(_scale_interval(ss, A, B, 1), y)
        if A.is_negative:
            return set_to_condition(_scale_interval(ss, A, B, -1), y)
        if certify_zero(A) is True:
            return sp.Eq(y, B)
        return normalize_cases(
            (
                ConditionalExpression(
                    set_to_condition(_scale_interval(ss, A, B, 1), y),
                    sp.And(extra, A > 0),
                ),
                ConditionalExpression(sp.Eq(y, B), sp.And(extra, sp.Eq(A, 0))),
                ConditionalExpression(
                    set_to_condition(_scale_interval(ss, A, B, -1), y),
                    sp.And(extra, A < 0),
                ),
            ),
            source="affine-range-stratification",
        )

    if isinstance(inner, PropertyResult):
        cases = []
        for c in inner.cases:
            tr = transform(c.value, c.condition)
            if isinstance(tr, PropertyResult):
                cases.extend(tr.cases)
            elif tr is not None:
                cases.append(ConditionalExpression(tr, c.condition))
        return (
            normalize_cases(cases, source="affine-range-stratification")
            if cases
            else None
        )
    return transform(inner)


def _parameterized_elementary_range(expr, var, y, domain_condition):
    """High-value exact parameter strata not handled by generic calculus."""
    ds = condition_to_set(domain_condition, var)
    positive_axis = ds == sp.Interval.open(0, sp.oo)
    # x**a on x>0: every nonzero real exponent maps onto (0,oo), while
    # a=0 is the singleton 1.  This must precede global catalogue ranges.
    if positive_axis and expr.func is sp.Pow and expr.base == var:
        A = expr.exp
        if A.free_symbols:
            real_guard = S.true if A.is_real is True else sp.Contains(A, S.Reals)
            return normalize_cases(
                (
                    ConditionalExpression(y > 0, sp.And(real_guard, sp.Ne(A, 0))),
                    ConditionalExpression(sp.Eq(y, 1), sp.Eq(A, 0)),
                ),
                source="positive-power-range-stratification",
            )
    if ds is not S.Reals:
        return None
    # exp(a*x+b): nonzero real slope maps R bijectively to (0,oo); zero
    # slope is the singleton exp(b).
    if expr.func is sp.exp:
        affine = affine_real_parameter_guard(expr.args[0], var)
        if affine is not None:
            A, B, real_guard = affine
            if A.free_symbols or B.free_symbols or real_guard is not S.true:
                real_b = S.true if B.is_real is True else sp.Q.real(B)
                return normalize_cases(
                    (
                        ConditionalExpression(y > 0, sp.And(real_guard, sp.Ne(A, 0))),
                        ConditionalExpression(
                            sp.Eq(y, sp.exp(B)), sp.And(real_b, sp.Eq(A, 0))
                        ),
                    ),
                    source="exp-affine-range-stratification",
                )
    return None


def _sympy_range(expr, var, y, domain_condition):
    ds = condition_to_set(domain_condition, var)
    if ds is None:
        return None
    try:
        rs = attainment_preserving_range(expr, var, ds)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    if isinstance(rs, sp.Set) and not rs.has(var):
        return set_to_condition(rs, y)
    return None


def _early_range_stage(expr, var, y, domain_condition, constraints):
    """Run cheap parameter, catalogue, and positive-axis range rules."""
    pr = _parameterized_elementary_range(expr, var, y, domain_condition)
    if pr is not None:
        return pr
    sf_domain = domain_condition if constraints is True else sp.sympify(constraints)
    sfacts = special_function_range_strata(expr, var, y, sf_domain)
    if sfacts:
        out = normalize_cases(
            (ConditionalExpression(v, g) for v, g, *_ in sfacts),
            source="dlmf-special-function-range-stratification",
            evidence=tuple(src for *_, src in sfacts),
        )
        return out.primary if out.primary is not None else out
    ds0 = condition_to_set(domain_condition, var)
    positive_axis = ds0 == sp.Interval.open(0, sp.oo) or condition_to_set(
        constraints, var
    ) == sp.Interval.open(0, sp.oo)
    if positive_axis:
        facts = positive_axis_range_strata(expr, var, y)
        if facts:
            out = normalize_cases(
                (ConditionalExpression(v, g) for v, g, *_ in facts),
                source="special-function-range-stratification",
                evidence=tuple(src for *_, src in facts),
            )
            return out.primary if out.primary is not None else out
    return None


def _semialgebraic_range_stage(expr, var, y, domain_condition, method, kwargs):
    """Run structural then exact semialgebraic range analysis."""
    if not _semialg.eligible_problem(expr, var, domain=domain_condition):
        return None
    structural = _affine_transform(expr, var, y, domain_condition)
    if structural is not None:
        return (
            structural
            if isinstance(structural, PropertyResult)
            else sp.simplify(structural)
        )
    try:
        return _semialg.range(
            expr,
            var,
            y,
            constraints=domain_condition,
            method="qe" if method == "auto" else method,
            **kwargs,
        )
    except SYMBOLIC_QUERY_ERRORS:
        return None


def _piecewise_range(expr, var, y, domain_condition, method, kwargs):
    from .piecewise import combine_piecewise_conditions, piecewise_decomposition

    decomp = piecewise_decomposition(expr, var, domain_condition)
    if not decomp.complete:
        return None
    images = []
    for branch in decomp.branches:
        image = _function_range_impl(
            branch.expression,
            var,
            y,
            constraints=branch.condition,
            method=method,
            partition=None,
            _domain_ready=True,
            **kwargs,
        )
        if isinstance(image, PropertyResult):
            return None
        images.append(image)
    return combine_piecewise_conditions(images, y)


def _algebraic_image(expr, var, domain):
    """Evaluate exact images componentwise to preserve endpoint attainment.

    SymPy's union-domain range aggregation can open a shared endpoint even
    when each component attains it. Building the set union after evaluating
    individual intervals avoids losing those inclusion guarantees.
    """
    if domain is S.EmptySet:
        return S.EmptySet
    if isinstance(domain, sp.FiniteSet):
        values = tuple(expr.subs(var, value) for value in domain)
        if any(value.is_finite is False or value.is_real is False for value in values):
            return None
        return sp.FiniteSet(*values)
    if isinstance(domain, sp.Union):
        parts = [_algebraic_image(expr, var, part) for part in domain.args]
        if any(part is None for part in parts):
            return None
        # SymPy may simplify symbolic overlapping intervals to an open hull.
        # Keep the disjunction unevaluated unless exact endpoint order is known.
        return sp.Union(*parts, evaluate=False)
    if not isinstance(domain, sp.Interval):
        return None
    try:
        image = attainment_preserving_range(expr, var, domain)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    if isinstance(image, (sp.Interval, sp.FiniteSet, sp.Union)) and not image.has(var):
        return image
    return None


def _nonempty_real_domain(source):
    """Return an exact nonemptiness guard, or None if existence is unresolved."""
    if source is S.EmptySet:
        return S.false
    if isinstance(source, sp.FiniteSet):
        return sp.Or(*(sp.Contains(point, S.Reals) for point in source))
    if isinstance(source, sp.Interval):
        real = [
            sp.Contains(endpoint, S.Reals)
            for endpoint in (source.start, source.end)
            if endpoint not in (S.Infinity, S.NegativeInfinity)
        ]
        ordered = (
            source.start < source.end
            if source.left_open or source.right_open
            else source.start <= source.end
        )
        return sp.And(*real, ordered)
    if isinstance(source, sp.Union):
        guards = [_nonempty_real_domain(piece) for piece in source.args]
        if S.true in guards:
            return S.true
        return sp.Or(*guards) if all(guard is not None for guard in guards) else None
    if isinstance(source, sp.Intersection):
        finite = next(
            (part for part in source.args if isinstance(part, sp.FiniteSet)), None
        )
        if finite is not None:
            return sp.Or(
                *(
                    sp.And(sp.Contains(point, S.Reals), source.contains(point))
                    for point in finite
                )
            )
        if all(isinstance(part, sp.Interval) for part in source.args):
            lower = sp.Max(*(part.start for part in source.args))
            upper = sp.Min(*(part.end for part in source.args))
            return sp.Or(
                lower < upper,
                sp.And(
                    sp.Eq(lower, upper), *(part.contains(lower) for part in source.args)
                ),
            )
    if (
        isinstance(source, sp.Set)
        and source.is_subset(S.Reals) is True
        and source.is_empty is False
    ):
        return S.true
    return None


def _function_range_impl(
    expr,
    var,
    y,
    *,
    constraints=True,
    method="auto",
    partition=None,
    _domain_ready=False,
    _source_constraints=None,
    **kwargs,
):
    """Return the real range as a Boolean condition in ``y``.

    Strategy: primitive lookup, structural transformations, SymPy's univariate
    calculus algorithms, and semialg for the semialgebraic subset.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    y = sp.sympify(y)
    if _source_constraints is None:
        _source_constraints = constraints
    natural = domain(expr, var)
    if natural is S.false:
        return S.false
    requested_points = condition_to_set(_source_constraints, var)
    real_on_requested = _real_value_on_domain(expr, var, _source_constraints)
    if isinstance(natural, PropertyResult) and real_on_requested:
        natural = domain(expr, var, domain=S.Complexes)
    if isinstance(natural, PropertyResult) and expr.func is sp.exp:
        theorem = _parameterized_elementary_range(expr, var, y, constraints)
        source_guard = original_definition_guard(expr, (var,))
        if isinstance(theorem, PropertyResult) and source_guard is not None:
            return normalize_cases(
                (
                    ConditionalExpression(
                        case.value, sp.And(case.condition, source_guard)
                    )
                    for case in theorem.cases
                ),
                source=theorem.source,
            )
    if isinstance(requested_points, sp.FiniteSet) and isinstance(
        natural, PropertyResult
    ):
        # Exact point values decide output reality. Definition guards must be
        # derived from the unmodified source before those substitutions.
        natural = domain(expr, var, domain=S.Complexes)
    domain_condition = (
        sp.sympify(constraints)
        if _domain_ready
        else combine_domain_condition(natural, constraints, var)
    )
    if isinstance(requested_points, sp.FiniteSet) and not isinstance(
        natural, PropertyResult
    ):
        terms = []
        for point in requested_points:
            guard = sp.simplify(
                sp.And(sp.Contains(point, S.Reals), domain_condition.subs(var, point))
            )
            if guard is S.false:
                continue
            value = sp.simplify(expr.subs(var, point))
            if value.is_real is False or value.is_finite is False:
                continue
            if value.is_real is not True or value.is_finite is not True:
                return sp.Function("UnknownRange")(expr, var, y)
            terms.append(sp.And(guard, sp.Eq(y, value)))
        return sp.Or(*terms)
    if (
        _complex_intermediates(expr, var)
        and expr.is_real is not True
        and not real_on_requested
    ):
        if isinstance(natural, PropertyResult):
            return sp.Function("UnknownRange")(expr, var, y)
        real_part = _real_projection(expr, var)
        if real_part is None or real_part == expr:
            return sp.Function("UnknownRange")(expr, var, y)
        result = _function_range_impl(
            real_part,
            var,
            y,
            constraints=domain_condition,
            method=method,
            _domain_ready=True,
            _source_constraints=domain_condition,
            **kwargs,
        )
        if getattr(result, "func", None) == sp.Function("UnknownRange"):
            return sp.Function("UnknownRange")(expr, var, y)
        return result
    if not _domain_ready:
        split = evaluate_parameter_strata(
            domain_condition,
            var,
            lambda branch_domain: _function_range_impl(
                expr,
                var,
                y,
                constraints=branch_domain,
                method=method,
                partition=None,
                _domain_ready=True,
                _source_constraints=_source_constraints,
                **kwargs,
            ),
            source="range-parameter-stratification",
        )
        if split is not None:
            return split
    if condition_to_set(domain_condition, var) is S.EmptySet:
        return S.false
    if not expr.has(var):
        if expr.is_real is False or expr.is_finite is False:
            return S.false
        guard = _nonempty_real_domain(condition_to_set(domain_condition, var))
        if guard is None:
            return sp.Function("UnknownRange")(expr, var, y)
        return sp.And(guard, sp.Eq(y, expr))

    if isinstance(expr, sp.Piecewise):
        merged = _piecewise_range(expr, var, y, domain_condition, method, kwargs)
        if merged is not None:
            return merged

    if expr.func in (sp.floor, sp.ceiling) and expr.args == (var,):
        image = exact_image(expr, var, condition_to_set(domain_condition, var))
        if image is not None:
            return set_to_condition(image, y)

    finite_domain = condition_to_set(domain_condition, var)
    if isinstance(finite_domain, sp.FiniteSet):
        if any(point.is_real is not True for point in finite_domain):
            return sp.Function("UnknownRange")(expr, var, y)
        values = [sp.simplify(expr.subs(var, point)) for point in finite_domain]
        if any(
            value.is_real is not True or value.is_finite is not True for value in values
        ):
            return sp.Function("UnknownRange")(expr, var, y)
        return set_to_condition(sp.FiniteSet(*values), y)

    if method == "auto" and not kwargs:
        image = _quadratic_image(expr, var, finite_domain)
        if image is not None:
            return set_to_condition(image, y)

    early = _early_range_stage(expr, var, y, domain_condition, _source_constraints)
    if early is not None:
        return early

    # Preserve parameter strata before delegating semialgebraic elimination.
    # A backend QE call may quantify/treat free coefficients in a way that
    # collapses guarded image cases (for example a*x on x>0) to a tautology.
    backend = _semialgebraic_range_stage(expr, var, y, domain_condition, method, kwargs)
    if backend is not None:
        return backend

    # Exact transcendental algebraization can turn the range problem into a
    # semialgebraic one without changing the output variable. For example,
    # exp(2*x)-3*exp(x)+2 becomes u**2-3*u+2 on u>0.
    ar = algebraize(expr, var, domain=domain_condition)
    if ar.changed and ar.exact and len(ar.substitutions) == 1:
        u, _ = ar.substitutions[0]
        # Preserve openness of the auxiliary image (notably u=exp(x)>0).
        # SymPy's univariate calculus is tried first because it represents
        # endpoint attainment explicitly; semialg remains the exact fallback.
        us = condition_to_set(ar.constraints, u)
        rs = _algebraic_image(ar.expression, u, us)
        if rs is not None:
            return set_to_condition(rs, y)
        try:
            raw = _semialg.range(
                ar.expression,
                u,
                y,
                constraints=ar.constraints,
                method="qe" if method == "auto" else method,
                **kwargs,
            )
            # Refine finite interval endpoints against the actual auxiliary
            # domain so a backend closure approximation cannot turn > into >=.
            rs = condition_to_set(raw, y)
            us = condition_to_set(ar.constraints, u)
            if isinstance(rs, sp.Interval) and us is not None:
                lo_open, hi_open = rs.left_open, rs.right_open
                if rs.start not in (S.NegativeInfinity, S.Infinity):
                    sol = sp.solveset(sp.Eq(ar.expression, rs.start), u, domain=us)
                    if sol is S.EmptySet:
                        lo_open = True
                if rs.end not in (S.NegativeInfinity, S.Infinity):
                    sol = sp.solveset(sp.Eq(ar.expression, rs.end), u, domain=us)
                    if sol is S.EmptySet:
                        hi_open = True
                return set_to_condition(
                    sp.Interval(
                        rs.start, rs.end, left_open=lo_open, right_open=hi_open
                    ),
                    y,
                )
            return raw
        except SYMBOLIC_QUERY_ERRORS:
            pass

    # Monotone composition can turn a known inner interval into the exact
    # outer range (e.g. exp(sin(x)) -> [exp(-1), exp(1)]).
    r = _composition_range(
        expr,
        var,
        y,
        domain_condition,
        source_constraints=constraints if not _domain_ready else None,
    )
    if r is not None:
        return r if isinstance(r, PropertyResult) else sp.simplify(r)

    # Primitive catalogue ranges are exact and cheapest.
    if constraints is True or is_full_natural_domain(domain_condition, natural):
        r = _registry_range(expr, var, y)
        if r is not None:
            return r if isinstance(r, PropertyResult) else sp.simplify(r)

    ds = condition_to_set(domain_condition, var)
    part = matching_partition(partition, expr, var, ds)
    # Indexed special-function geometry is cheap to recognize and expensive to
    # rediscover through generic calculus, so build the shared partition first
    # for those families.  For generic expressions keep SymPy's successful fast
    # path ahead of a potentially redundant derivative-root solve.
    if isinstance(ds, sp.Interval):
        try:
            from ..transcendental.zero_geometry import zero_geometry

            if part is None and zero_geometry(expr, var, derivative_order=1, domain=ds):
                part = monotonic_partition(expr, var, domain=ds, return_result=True)
        except SYMBOLIC_QUERY_ERRORS:
            pass
    if part is not None:
        prange = range_from_monotonic_partition(expr, var, part, domain=ds)
        if prange.complete and isinstance(prange.image, sp.Set):
            return set_to_condition(prange.image, y)

    if isinstance(ds, sp.Interval) and expr.func in (
        sp.erf,
        sp.erfc,
        sp.erfi,
        sp.besseli,
        sp.besselk,
    ):
        mapped = _monotone_image_interval(expr, var, ds)
        if mapped is not None:
            return set_to_condition(mapped, y)

    r = _sympy_range(expr, var, y, domain_condition)
    if r is not None:
        return sp.simplify(r)

    if part is None and isinstance(ds, sp.Interval):
        part = monotonic_partition(expr, var, domain=ds, return_result=True)
        prange = range_from_monotonic_partition(expr, var, part, domain=ds)
        if prange.complete and isinstance(prange.image, sp.Set):
            return set_to_condition(prange.image, y)

    # Indexed extrema consume the same partition certificate, avoiding a second
    # derivative-zero geometry pass.
    try:
        from ..transcendental.extrema import symbolic_extremum_range

        er = symbolic_extremum_range(
            expr,
            var,
            ds if isinstance(ds, sp.Interval) else domain_condition,
            partition=part,
        )
        if er is not None and er.complete:
            cond = er.as_condition(y)
            return cond if cond is not None else er
    except SYMBOLIC_QUERY_ERRORS:
        pass
    if _semialg._algebraic_encoding(expr, var, domain_condition) is not None:
        try:
            return _semialg.range(expr, var, y, constraints=domain_condition)
        except (_semialg.SemialgUnavailable, *SYMBOLIC_QUERY_ERRORS):
            pass
    return sp.Function("UnknownRange")(expr, var, y)


def range(
    expr,
    var,
    y,
    *,
    constraints=True,
    domain=None,
    method="auto",
    partition=None,
    **kwargs,
):
    """Return the real range on the intersection of constraints and domain."""
    if domain is not None:
        from .common import normalize_domain_condition

        constraints = combine_domain_condition(
            normalize_domain_condition(constraints, var), domain, var
        )
    return _function_range_impl(
        expr,
        var,
        y,
        constraints=constraints,
        method=method,
        partition=partition,
        _domain_ready=False,
        **kwargs,
    )
