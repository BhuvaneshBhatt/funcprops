"""Exact set images for a small real elementary vocabulary."""

from __future__ import annotations

import sympy as sp
from sympy import S

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..source_syntax import differentiate, normalize_arithmetic


def _small_polynomial_degree(expression, variable):
    if expression == variable:
        return 1
    if expression.is_Rational:
        return 0
    if expression.is_Add or expression.is_Mul:
        degrees = [_small_polynomial_degree(arg, variable) for arg in expression.args]
        if any(degree is None for degree in degrees):
            return None
        degree = max(degrees) if expression.is_Add else sum(degrees)
        return degree if degree <= 2 else None
    if expression.is_Pow and expression.exp in (1, 2):
        degree = _small_polynomial_degree(expression.base, variable)
        if degree is not None and degree * expression.exp <= 2:
            return degree * expression.exp
    return None


def _quadratic_image(expression, variable, source):
    """Map rational interval components through a rational quadratic exactly.

    The caller supplies the effective source set after checking the original
    expression's definition guards. Arithmetic rebuilding can cancel factors,
    so that source set must retain the resulting holes. Vertex and endpoint
    values decide both extrema and attainment, including tied endpoint values.
    The grammar and component bounds keep unsuccessful dispatch work bounded.
    """
    from ..domain_tracking import coordinate_domain_compatible

    if not isinstance(source, (sp.Interval, sp.Union, sp.FiniteSet)):
        return None
    for index, _ in enumerate(sp.preorder_traversal(expression)):
        if index == 64:
            return None
    expression = normalize_arithmetic(expression)
    if _small_polynomial_degree(expression, variable) != 2:
        return None
    components = source.args if isinstance(source, sp.Union) else (source,)
    if len(components) > 16:
        return None
    for component in components:
        if isinstance(component, sp.Interval):
            if any(
                not endpoint.is_Rational
                and endpoint not in (S.NegativeInfinity, S.Infinity)
                for endpoint in (component.start, component.end)
            ):
                return None
        elif isinstance(component, sp.FiniteSet):
            if len(component) > 16 or any(not point.is_Rational for point in component):
                return None
        else:
            return None
    if not coordinate_domain_compatible(variable, source):
        return None
    polynomial = sp.Poly(expression, variable, domain=sp.QQ)
    if polynomial.degree() != 2:
        return None
    a, b, _ = polynomial.all_coeffs()
    vertex = -b / (2 * a)
    vertex_value = polynomial.eval(vertex)
    infinite_value = S.Infinity if a > 0 else S.NegativeInfinity
    images = []
    for component in components:
        if isinstance(component, sp.FiniteSet):
            images.append(
                sp.FiniteSet(*(polynomial.eval(point) for point in component))
            )
            continue
        candidates = []
        for endpoint, is_open in (
            (component.start, component.left_open),
            (component.end, component.right_open),
        ):
            value = (
                infinite_value
                if endpoint in (S.NegativeInfinity, S.Infinity)
                else polynomial.eval(endpoint)
            )
            candidates.append((value, not is_open))
        if component.contains(vertex) is S.true:
            candidates.append((vertex_value, True))
        lower = min(value for value, _ in candidates)
        upper = max(value for value, _ in candidates)
        images.append(
            sp.Interval(
                lower,
                upper,
                left_open=not any(
                    value == lower and owned for value, owned in candidates
                ),
                right_open=not any(
                    value == upper and owned for value, owned in candidates
                ),
            )
        )
    return sp.Union(*images)


def attainment_preserving_range(expression, variable, source):
    """Restore attained extrema dropped by SymPy's endpoint aggregation.

    An open endpoint limit can equal a value attained elsewhere, including a
    closed endpoint or an interior stationary point. Its presence among the
    limits alone must not open the image endpoint. Reinsert only source-bound,
    finite real values; unresolved critical sets decline this route.
    """
    expression = normalize_arithmetic(expression)
    image = sp.calculus.util.function_range(expression, variable, source)
    if not expression.has(variable):
        return image
    critical = sp.solveset(differentiate(expression, variable), variable, domain=source)
    if not isinstance(critical, sp.FiniteSet) and critical is not S.EmptySet:
        return None
    points = list(critical)
    for component in source.args if isinstance(source, sp.Union) else (source,):
        if isinstance(component, sp.FiniteSet):
            points.extend(component)
        elif isinstance(component, sp.Interval):
            if not component.left_open:
                points.append(component.start)
            if not component.right_open:
                points.append(component.end)
        else:
            return None
    attained = []
    for point in points:
        if source.contains(point) is not S.true:
            return None
        value = sp.simplify(expression.subs(variable, point))
        if value.is_finite is not True or value.is_real is not True:
            return None
        attained.append(value)
    return sp.Union(image, sp.FiniteSet(*attained))


def _interval_power(interval, exponent):
    """A monotone principal power on a single sign component."""

    def value(endpoint):
        if endpoint in (S.Infinity, S.NegativeInfinity):
            if exponent < 0:
                return S.Zero
            return endpoint**exponent
        if endpoint == 0 and exponent < 0:
            if exponent.q == 1 and exponent.is_odd and interval.end == 0:
                return S.NegativeInfinity
            return S.Infinity
        return sp.simplify(endpoint**exponent)

    a, b = value(interval.start), value(interval.end)
    negative = interval.end <= 0
    decreasing = (
        (exponent < 0)
        if not negative
        else ((exponent > 0) if exponent.is_even else (exponent < 0))
    )
    if decreasing:
        a, b = b, a
        left_open, right_open = interval.right_open, interval.left_open
    else:
        left_open, right_open = interval.left_open, interval.right_open
    return sp.Interval(
        a,
        b,
        left_open=left_open or a is S.NegativeInfinity,
        right_open=right_open or b is S.Infinity,
    )


def exact_image(outer, variable, source):
    """Return an exact image set, or None when any part is unsupported."""
    if source is S.EmptySet:
        return S.EmptySet
    if isinstance(source, sp.Union):
        parts = [exact_image(outer, variable, part) for part in source.args]
        if any(part is None for part in parts):
            return None
        return sp.Union(*parts, evaluate=False)
    if isinstance(source, sp.FiniteSet):
        values = []
        for point in source:
            value = sp.simplify(outer.subs(variable, point))
            if value.is_real is False or value.is_finite is False:
                continue
            if value.is_real is not True or value.is_finite is not True:
                return None
            values.append(value)
        return sp.FiniteSet(*values)
    if not isinstance(source, sp.Interval):
        return None
    try:
        if outer.func is sp.Pow and outer.base == variable and outer.exp.is_Rational:
            exponent = outer.exp
            if exponent == 0:
                return sp.FiniteSet(1)
            if exponent.q != 1:
                allowed = (
                    sp.Interval.open(0, sp.oo)
                    if exponent < 0
                    else sp.Interval(0, sp.oo)
                )
                restricted = sp.Intersection(source, allowed)
                if restricted is S.EmptySet:
                    return restricted
                if isinstance(restricted, sp.FiniteSet):
                    return exact_image(outer, variable, restricted)
                if not isinstance(restricted, sp.Interval):
                    return None
                return _interval_power(restricted, exponent)
            parts = []
            for half in (sp.Interval.open(-sp.oo, 0), sp.Interval.open(0, sp.oo)):
                part = sp.Intersection(source, half)
                if isinstance(part, sp.Interval):
                    parts.append(_interval_power(part, exponent))
                elif part is not S.EmptySet:
                    return None
            if exponent > 0 and source.contains(0) is S.true:
                parts.append(sp.FiniteSet(0))
            return sp.Union(*parts)
        if outer.func in (sp.floor, sp.ceiling) and outer.args == (variable,):
            a, b = source.start, source.end
            lo = S.NegativeInfinity if a is S.NegativeInfinity else outer.func(a)
            hi = S.Infinity if b is S.Infinity else outer.func(b)
            if outer.func is sp.ceiling and source.left_open and a.is_finite is True:
                if a.is_integer is None:
                    return None
                if a.is_integer:
                    lo += 1
            if outer.func is sp.floor and source.right_open and b.is_finite is True:
                if b.is_integer is None:
                    return None
                if b.is_integer:
                    hi -= 1
            return sp.Intersection(S.Integers, sp.Interval(lo, hi))
        if outer.func in (sp.sin, sp.cos) and outer.args == (variable,):
            width = source.end - source.start
            # On an open interval of exactly one period, both occurrences of
            # an extremum can be excluded endpoints. Wider intervals contain
            # an interior occurrence of each extremum.
            if width is S.Infinity or (width - 2 * sp.pi).is_positive is True:
                return sp.Interval(-1, 1)
            return attainment_preserving_range(outer, variable, source)
        if outer.func in (
            sp.exp,
            sp.log,
            sp.sinh,
            sp.cosh,
            sp.tanh,
            sp.atan,
        ) and outer.args == (variable,):
            if outer.func is sp.log:
                source = sp.Intersection(source, sp.Interval.open(0, sp.oo))
                if source is S.EmptySet:
                    return source
            return attainment_preserving_range(outer, variable, source)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    return None
