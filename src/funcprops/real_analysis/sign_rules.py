"""Bounded exact sign rules for rational functions and monotone thresholds."""

import sympy as sp
from sympy import S

from ..domain_tracking import coordinate_domain_compatible
from ..results import Sign
from ..source_syntax import normalize_arithmetic
from .image_rules import _quadratic_image
from .piecewise import combine_piecewise_sign


def _small_rational(value):
    return (
        value.is_Rational
        and max(abs(int(value.p)).bit_length(), int(value.q).bit_length()) <= 512
    )


def _combine_signs(values):
    if Sign.SIGN_CHANGING in values and Sign.UNKNOWN not in values:
        return Sign.SIGN_CHANGING
    return combine_piecewise_sign(values)


def _rational_degrees(expression, variable):
    """Bound numerator/denominator degrees before cancellation or expansion."""
    if expression == variable:
        return 1, 0
    if expression.is_Rational:
        return (0, 0) if _small_rational(expression) else None
    if not expression.has(variable):
        return None
    if expression.is_Add or expression.is_Mul:
        numerator, denominator = 0, 0
        for argument in expression.args:
            degree = _rational_degrees(argument, variable)
            if degree is None:
                return None
            n, d = degree
            numerator = (
                max(numerator + d, n + denominator)
                if expression.is_Add
                else numerator + n
            )
            denominator += d
            if max(numerator, denominator) > 12:
                return None
        return numerator, denominator
    if expression.is_Pow and expression.exp.is_Integer and abs(expression.exp) <= 12:
        degree = _rational_degrees(expression.base, variable)
        if degree is None:
            return None
        n, d = degree if expression.exp >= 0 else degree[::-1]
        n, d = n * abs(expression.exp), d * abs(expression.exp)
        return (n, d) if max(n, d) <= 12 else None
    return None


def rational_polynomials(expression, variable):
    """Parse a small rational formula without expanding unsupported powers."""
    for index, _ in enumerate(sp.preorder_traversal(expression)):
        if index == 96:
            return None
    if _rational_degrees(expression, variable) is None:
        return None
    numerator, denominator = sp.fraction(sp.cancel(normalize_arithmetic(expression)))
    if numerator.has(sp.nan, sp.zoo, sp.oo, -sp.oo) or denominator.has(
        sp.nan, sp.zoo, sp.oo, -sp.oo
    ):
        return None
    n, d = (sp.Poly(part, variable, domain=sp.QQ) for part in (numerator, denominator))
    if d.is_zero:
        return None
    return n, d


def rational_components(domain):
    """Recognize finite unions of rational intervals and rational points."""
    parts = domain.args if isinstance(domain, sp.Union) else (domain,)
    if len(parts) > 8:
        return None
    for part in parts:
        if isinstance(part, sp.Interval):
            if any(
                not _small_rational(p) and p not in (-sp.oo, sp.oo)
                for p in (part.start, part.end)
            ):
                return None
        elif isinstance(part, sp.FiniteSet):
            if len(part) > 16 or any(not _small_rational(p) for p in part):
                return None
        else:
            return None
    return parts


def _sample_ratio(numerator, denominator, interval):
    degree = int(numerator.degree())
    for k in range(1, degree + 2):
        if interval.start is -sp.oo and interval.end is sp.oo:
            point = sp.Integer(k - 1)
        elif interval.start is -sp.oo:
            point = interval.end - k
        elif interval.end is sp.oo:
            point = interval.start + k
        else:
            point = interval.start + (interval.end - interval.start) * sp.Rational(
                k, degree + 2
            )
        value = numerator.eval(point) / denominator.eval(point)
        if value:
            return 1 if value > 0 else -1
    return None


def rational_sign(expression, variable, domain):
    """Classify a rational formula on its already established effective domain.

    Exact Sturm counts distinguish absent zeros, odd interior crossings, and attained even or
    endpoint zeros. Denominator zeros always decline this route. Original
    canceled holes remain in the caller's effective domain.
    """
    if not isinstance(domain, sp.Set):
        return Sign.UNKNOWN
    parts = rational_components(domain)
    if parts is None or not coordinate_domain_compatible(variable, domain):
        return Sign.UNKNOWN
    polynomials = rational_polynomials(expression, variable)
    if polynomials is None:
        return Sign.UNKNOWN
    n, d = polynomials
    from ..coverage_checker import _distinct_count

    results = []
    for part in parts:
        if isinstance(part, sp.FiniteSet):
            for point in part:
                if not d.eval(point):
                    return Sign.UNKNOWN
                value = n.eval(point) / d.eval(point)
                results.append(
                    Sign.ZERO
                    if not value
                    else Sign.POSITIVE
                    if value > 0
                    else Sign.NEGATIVE
                )
            continue
        if _distinct_count(d, part):
            return Sign.UNKNOWN
        if n.is_zero:
            results.append(Sign.ZERO)
            continue
        count = _distinct_count(n, part)
        if count:
            interior = sp.Interval.open(part.start, part.end)
            odd = sp.prod(
                factor.as_expr()
                for factor, multiplicity in n.sqf_list()[1]
                if multiplicity % 2
            )
            odd = sp.sympify(odd)
            if odd.has(variable) and _distinct_count(
                sp.Poly(odd, variable, domain=sp.QQ), interior
            ):
                results.append(Sign.SIGN_CHANGING)
                continue
        sample = _sample_ratio(n, d, part)
        if sample is None:
            return Sign.UNKNOWN
        results.append(
            (Sign.NONNEGATIVE if sample > 0 else Sign.NONPOSITIVE)
            if count
            else (Sign.POSITIVE if sample > 0 else Sign.NEGATIVE)
        )
    return _combine_signs(results)


def _affine_image(polynomial, source):
    if polynomial.degree() != 1:
        return None
    a, b = polynomial.all_coeffs()
    images = []
    for part in rational_components(source) or ():
        if isinstance(part, sp.FiniteSet):
            images.append(sp.FiniteSet(*(polynomial.eval(p) for p in part)))
        else:
            lo, hi = a * part.start + b, a * part.end + b
            images.append(
                sp.Interval(
                    lo, hi, left_open=part.left_open, right_open=part.right_open
                )
                if a > 0
                else sp.Interval(
                    hi, lo, left_open=part.right_open, right_open=part.left_open
                )
            )
    return sp.Union(*images) if images else None


def _image_threshold_sign(image, level):
    from ..enclosures import enclosure_witness

    if level.is_Rational:
        bounds = level, level
    else:
        axis = sp.Symbol("threshold_axis", real=True)
        witness = enclosure_witness(level, axis, sp.FiniteSet(0), precision=20)
        if witness is None:
            return Sign.UNKNOWN
        bounds = witness.lower, witness.upper

    def compare(point):
        if bounds[0] == bounds[1] == point:
            return 0
        if point < bounds[0]:
            return -1
        if point > bounds[1]:
            return 1
        return None

    results = []
    for part in image.args if isinstance(image, sp.Union) else (image,):
        if isinstance(part, sp.FiniteSet):
            for point in part:
                sign = compare(point)
                if sign is None:
                    return Sign.UNKNOWN
                results.append(
                    Sign.ZERO
                    if sign == 0
                    else Sign.POSITIVE
                    if sign > 0
                    else Sign.NEGATIVE
                )
            continue
        if not isinstance(part, sp.Interval):
            return Sign.UNKNOWN
        lo = -1 if part.start is -sp.oo else compare(part.start)
        hi = 1 if part.end is sp.oo else compare(part.end)
        if lo is None or hi is None:
            return Sign.UNKNOWN
        if lo > 0 or (lo == 0 and part.left_open):
            results.append(Sign.POSITIVE)
        elif hi < 0 or (hi == 0 and part.right_open):
            results.append(Sign.NEGATIVE)
        elif lo >= 0:
            results.append(Sign.NONNEGATIVE)
        elif hi <= 0:
            results.append(Sign.NONPOSITIVE)
        else:
            results.append(Sign.SIGN_CHANGING)
    return _combine_signs(results)


def threshold_sign(expression, variable, domain):
    """Transfer an exp/log comparison through an exact affine/quadratic image."""
    if not expression.is_Add or expression.free_symbols != {variable}:
        return Sign.UNKNOWN
    for index, _ in enumerate(sp.preorder_traversal(expression)):
        if index == 96:
            return Sign.UNKNOWN
    varying = [term for term in expression.args if term.has(variable)]
    if len(varying) != 1:
        return Sign.UNKNOWN
    coefficient, head = varying[0].as_independent(variable, as_Add=False)
    if (
        not _small_rational(coefficient)
        or not coefficient
        or head.func not in (sp.exp, sp.log)
        or len(head.args) != 1
    ):
        return Sign.UNKNOWN
    constant = expression - varying[0]
    if constant.is_real is not True or constant.is_finite is not True:
        return Sign.UNKNOWN
    constant_scale, constant_head = constant.as_coeff_Mul()
    if not _small_rational(constant_scale) or not (
        _small_rational(constant_head)
        or constant_head in (sp.E, sp.pi)
        or (
            constant_head.func is sp.log
            and len(constant_head.args) == 1
            and _small_rational(constant_head.args[0])
            and constant_head.args[0] > 0
        )
    ):
        return Sign.UNKNOWN
    polynomials = rational_polynomials(head.args[0], variable)
    if polynomials is None or polynomials[1].degree() != 0:
        return Sign.UNKNOWN
    if rational_components(domain) is None or not coordinate_domain_compatible(
        variable, domain
    ):
        return Sign.UNKNOWN
    level = -constant / coefficient
    if head.func is sp.exp:
        if level.is_nonpositive is True:
            result = Sign.POSITIVE
            return result if coefficient > 0 else Sign.NEGATIVE
        if level.is_positive is not True:
            return Sign.UNKNOWN
        threshold = sp.log(level)
    else:
        from ..enclosures import enclosure_witness

        if level.is_Rational:
            level_bounds = level, level
        else:
            axis = sp.Symbol("threshold_axis", real=True)
            witness = enclosure_witness(level, axis, sp.FiniteSet(0), precision=20)
            if witness is None:
                return Sign.UNKNOWN
            level_bounds = witness.lower, witness.upper
        if max(abs(p) for p in level_bounds) > 128:
            return Sign.UNKNOWN
        threshold = sp.exp(level)
    inner = normalize_arithmetic(head.args[0])
    image = _quadratic_image(inner, variable, domain)
    if image is None:
        image = _affine_image(
            polynomials[0].mul_ground(1 / polynomials[1].LC()), domain
        )
    if image is None:
        return Sign.UNKNOWN
    if head.func is sp.log and image.is_subset(sp.Interval.open(0, sp.oo)) is not True:
        return Sign.UNKNOWN
    result = _image_threshold_sign(image, threshold)
    if coefficient > 0:
        return result
    return {
        Sign.POSITIVE: Sign.NEGATIVE,
        Sign.NEGATIVE: Sign.POSITIVE,
        Sign.NONNEGATIVE: Sign.NONPOSITIVE,
        Sign.NONPOSITIVE: Sign.NONNEGATIVE,
    }.get(result, result)


def trig_sign(expression, variable, domain):
    """Use rational subcharts of sine/cosine's central sign intervals.

    The exact bounds 3 < pi < 4 give sign(sin(t)) = sign(t) for |t| <= 3,
    cos(t) > 0 for |t| <= 3/2, and cos(t) < 0 for 2 <= |t| <= 3.
    No root search or approximate phase reduction is needed on these charts.
    """
    if expression.func not in (sp.sin, sp.cos):
        return Sign.UNKNOWN
    if rational_components(domain) is None or not coordinate_domain_compatible(
        variable, domain
    ):
        return Sign.UNKNOWN
    polynomials = rational_polynomials(expression.args[0], variable)
    if polynomials is None or polynomials[1].degree() != 0:
        return Sign.UNKNOWN
    polynomial = polynomials[0].mul_ground(1 / polynomials[1].LC())
    image = _affine_image(polynomial, domain)
    if image is None:
        return Sign.UNKNOWN
    if expression.func is sp.sin and image.is_subset(sp.Interval(-3, 3)) is True:
        return _image_threshold_sign(image, S.Zero)
    if expression.func is sp.cos:
        if image.is_subset(sp.Interval(-sp.Rational(3, 2), sp.Rational(3, 2))) is True:
            return Sign.POSITIVE
        negative = sp.Union(sp.Interval(-3, -2), sp.Interval(2, 3))
        if image.is_subset(negative) is True:
            return Sign.NEGATIVE
    return Sign.UNKNOWN
