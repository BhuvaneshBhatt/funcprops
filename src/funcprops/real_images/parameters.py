"""Exact parameter families of polynomial images and invertible outer functions."""

from dataclasses import dataclass, replace

import sympy as sp

from ..analysis import condition_to_real_set
from ..source_syntax import same_data

# The output guard selects the real inverse branch of each outer map.
_INVERSES = {
    sp.exp: (sp.log, lambda y: y > 0),
    sp.log: (sp.exp, lambda y: sp.true),
    sp.sinh: (sp.asinh, lambda y: sp.true),
    sp.asinh: (sp.sinh, lambda y: sp.true),
    sp.tanh: (sp.atanh, lambda y: sp.And(y > -1, y < 1)),
    sp.atanh: (sp.tanh, lambda y: sp.true),
    sp.atan: (sp.tan, lambda y: sp.And(y > -sp.pi / 2, y < sp.pi / 2)),
    sp.asin: (sp.sin, lambda y: sp.And(y >= -sp.pi / 2, y <= sp.pi / 2)),
    sp.acos: (sp.cos, lambda y: sp.And(y >= 0, y <= sp.pi)),
    sp.acosh: (sp.cosh, lambda y: y >= 0),
    sp.erf: (sp.erfinv, lambda y: sp.And(y > -1, y < 1)),
    sp.erfc: (lambda y: sp.erfinv(1 - y), lambda y: sp.And(y > 0, y < 2)),
}


def _relation(expression, operator):
    numerator, denominator = sp.fraction(sp.cancel(expression))
    return operator(sp.expand(numerator * denominator), 0)


def _parts(domain):
    return domain.args if isinstance(domain, sp.Union) else (domain,)


def _interval_condition(polynomial, x, y, interval):
    """Describe the image by possible extremal values, without dividing by its degree.

    Endpoint limits and an interior sample handle affine and constant strata.
    The vertex contributes only when it is inside the interval. Multiplying its
    value comparison by 4*A keeps the A=0 stratum defined and avoids choosing an
    order for parameter-dependent endpoint values.
    """
    a, b, c = (polynomial.nth(i) for i in (2, 1, 0))
    L, U = interval.start, interval.end
    sites = (
        (polynomial.eval(L), not interval.left_open),
        (polynomial.eval(U), not interval.right_open),
        (polynomial.eval((L + U) / 2), True),
    )
    lower = [_relation(y - v, sp.Ge if owned else sp.Gt) for v, owned in sites]
    upper = [_relation(y - v, sp.Le if owned else sp.Lt) for v, owned in sites]
    positive = _relation(a, sp.Gt)
    negative = _relation(a, sp.Lt)
    # Vertex ownership is strict here: an endpoint vertex already has that
    # endpoint's ownership in sites. This also handles a deleted endpoint.
    positive_vertex = sp.And(
        positive, _relation(b + 2 * a * L, sp.Lt), _relation(b + 2 * a * U, sp.Gt)
    )
    negative_vertex = sp.And(
        negative, _relation(b + 2 * a * L, sp.Gt), _relation(b + 2 * a * U, sp.Lt)
    )
    comparison = 4 * a * (y - c) + b**2
    lower.extend(
        (
            sp.And(positive_vertex, _relation(comparison, sp.Ge)),
            sp.And(negative_vertex, _relation(comparison, sp.Le)),
        )
    )
    upper.extend(
        (
            sp.And(positive_vertex, _relation(comparison, sp.Le)),
            sp.And(negative_vertex, _relation(comparison, sp.Ge)),
        )
    )
    return sp.And(sp.Or(*lower), sp.Or(*upper))


def _cubic_interval_condition(polynomial, x, y, interval):
    """Keep real, defined critical candidates on every cubic degree stratum.

    Clearing coefficient denominators makes pole substitutions harmless before
    their guards are evaluated. Safe divisors and nonnegative radicands keep
    inactive degree/discriminant branches real and defined as well.
    """
    denominator = sp.lcm(
        [sp.fraction(sp.cancel(c))[1] for c in polynomial.all_coeffs()]
    )
    numerator = sp.Poly(sp.cancel(polynomial.as_expr() * denominator), x)
    a, b, c = (numerator.nth(i) for i in (3, 2, 1))
    safe_a = sp.Piecewise((a, sp.Ne(a, 0)), (1, True))
    safe_b = sp.Piecewise((b, sp.Ne(b, 0)), (1, True))
    discriminant = b * b - 3 * a * c
    root = sp.sqrt(sp.Max(discriminant, 0))
    candidates = (
        ((-b - root) / (3 * safe_a), sp.And(sp.Ne(a, 0), discriminant >= 0)),
        ((-b + root) / (3 * safe_a), sp.And(sp.Ne(a, 0), discriminant >= 0)),
        (-c / (2 * safe_b), sp.And(sp.Eq(a, 0), sp.Ne(b, 0))),
    )
    L, U = interval.start, interval.end
    sites = [
        (L, not interval.left_open, sp.true),
        (U, not interval.right_open, sp.true),
        ((L + U) / 2, True, sp.true),
    ]
    sites.extend(
        (point, True, sp.And(guard, point > L, point < U))
        for point, guard in candidates
    )
    lower, upper = [], []
    for point, owned, guard in sites:
        difference = (y * denominator - numerator.eval(point)) * denominator
        lower.append(
            sp.And(guard, sp.Ge(difference, 0) if owned else sp.Gt(difference, 0))
        )
        upper.append(
            sp.And(guard, sp.Le(difference, 0) if owned else sp.Lt(difference, 0))
        )
    return sp.And(sp.Or(*lower), sp.Or(*upper))


def _cubic_events(polynomial, x, interval):
    """List degree, critical-point, boundary and equal-value event candidates."""
    f = polynomial.as_expr()
    derivative = sp.diff(f, x)
    a, b, c = (polynomial.nth(i) for i in (3, 2, 1))
    return (
        a,
        b * b - 3 * a * c,
        derivative.subs(x, interval.start),
        derivative.subs(x, interval.end),
        f.subs(x, interval.start) - f.subs(x, interval.end),
        *(
            sp.resultant(derivative, f - f.subs(x, p), x)
            for p in (interval.start, interval.end)
        ),
    )


def _validate_parameter_guard(guard, parameters):
    """Keep a family's parameter domain independent of source and output coordinates."""
    guard = sp.sympify(guard)
    if (
        not isinstance(guard, sp.logic.boolalg.Boolean)
        or guard.has(sp.Float)
        or guard.free_symbols - set(parameters)
    ):
        raise ValueError("parameter_domain must constrain only the declared parameters")
    return guard


def _family(expression, variable, parameters, domain, parameter_domain, value):
    """Validate a fixed rational source geometry and derive its family formula."""
    from ..domain_tracking import coordinate_domain_compatible

    f, x, y = expression, variable, value
    parameter_domain = _validate_parameter_guard(parameter_domain, parameters)
    if not isinstance(domain, sp.Set) or not coordinate_domain_compatible(x, domain):
        return None
    if f.has(sp.Float) or f.free_symbols - {x, *parameters}:
        return None
    core, head = (f.args[0], f.func) if f.func in _INVERSES else (f, None)
    # Arithmetic normalization must not delete a source pole in x. Coefficient
    # poles are retained as parameter guards, including held zero products.
    guards = []
    coordinates = {x, *parameters}
    for node in sp.preorder_traversal(core):
        if not (
            node in coordinates
            or node.is_Rational is True
            or node.is_Add
            or node.is_Mul
            or (node.is_Pow and node.exp.is_Integer is True)
        ):
            return None
        if isinstance(node, sp.Pow) and node.exp.is_negative:
            if node.base.has(x):
                return None
            guards.append(sp.Ne(node.base, 0))
    if not core.is_rational_function(x, *parameters):
        return None
    try:
        polynomial = sp.Poly(sp.cancel(core), x)
    except sp.PolynomialError:
        return None
    if polynomial.degree() > 3:
        return None
    if any(not v.is_rational_function(*parameters) for v in polynomial.all_coeffs()):
        return None
    for coefficient in polynomial.all_coeffs():
        guards.append(sp.Ne(sp.fraction(sp.cancel(coefficient))[1], 0))
    parameter_guard = sp.And(parameter_domain, *guards)
    conditions, events = [], []
    if domain is not sp.S.EmptySet:
        for cell in _parts(domain):
            if isinstance(cell, sp.FiniteSet):
                conditions.extend(sp.Eq(y, polynomial.eval(p)) for p in cell)
            elif isinstance(cell, sp.Interval) and all(
                endpoint.is_Rational is True for endpoint in (cell.start, cell.end)
            ):
                conditions.append(
                    (
                        _cubic_interval_condition
                        if polynomial.degree() == 3
                        else _interval_condition
                    )(polynomial, x, y, cell)
                )
                a, b = polynomial.nth(2), polynomial.nth(1)
                candidates = (
                    a,
                    2 * a * cell.start + b,
                    2 * a * cell.end + b,
                    polynomial.eval(cell.start) - polynomial.eval(cell.end),
                )
                if polynomial.degree() == 3:
                    candidates = _cubic_events(polynomial, x, cell)
                events.extend(_relation(v, sp.Eq) for v in candidates)
            else:
                return None
    if any(
        point.is_Rational is not True
        for cell in _parts(domain)
        if isinstance(cell, sp.FiniteSet)
        for point in cell
    ):
        return None
    formula = sp.Or(*conditions)
    if head is not None:
        inverse, output_guard = _INVERSES[head]
        valid_output = output_guard(y)
        default = 1 if head in (sp.exp, sp.erfc) else 0
        safe_output = sp.Piecewise((y, valid_output), (default, True))
        formula = sp.And(valid_output, formula.xreplace({y: inverse(safe_output)}))
    formula = sp.And(parameter_guard, formula)
    events = tuple(sorted(set(events) - {sp.true, sp.false}, key=sp.default_sort_key))
    return core, head, parameter_guard, formula, events


@dataclass(frozen=True)
class ParameterRangeAnalysis:
    """A quantifier-free image family for rational polynomial coefficients of degree at most three.

    ``condition`` is a formula in ``value`` and the declared parameters. It
    retains constant and affine strata, coefficient poles, endpoint ownership,
    vertex crossings and endpoint ties. ``transitions`` lists candidate events;
    it does not claim every event changes the image. Supported transcendental
    outer maps use their real inverse branch. Other families remain incomplete.
    """

    expression: sp.Expr
    variable: sp.Symbol
    parameters: tuple
    domain: sp.Set
    parameter_domain: object
    value: sp.Symbol
    condition: object = None
    transitions: tuple = ()
    complete: bool = False
    certified: bool = False
    reason: object = None

    def verify(self):
        """Replay the source grammar and polynomial image identities."""
        try:
            if (
                type(self) is not ParameterRangeAnalysis
                or type(self.certified) is not bool
            ):
                return False
            _validate_coordinates(self.variable, self.parameters, self.value)
            family = _family(
                self.expression,
                self.variable,
                self.parameters,
                self.domain,
                self.parameter_domain,
                self.value,
            )
            return (
                family is not None
                and self.complete is True
                and same_data(
                    (self.condition, self.transitions), (family[3], family[4])
                )
            )
        except (
            TypeError,
            ValueError,
            AttributeError,
            ArithmeticError,
            NotImplementedError,
        ):
            return False

    def specialize(self, substitutions):
        """Return an exact real image set at fixed real parameter values, or None.

        All parameters must be supplied. A value outside the parameter domain,
        or at a coefficient pole, has empty image. Unknown real order declines.
        """
        substitutions = {
            sp.sympify(k): sp.sympify(v) for k, v in dict(substitutions).items()
        }
        if set(substitutions) != set(self.parameters):
            raise ValueError("supply exactly the declared parameters")
        if any(
            v.free_symbols or v.has(sp.Float) or v.is_real is not True
            for v in substitutions.values()
        ):
            raise ValueError("parameter values must be fixed exact real expressions")
        if not self.complete or not self.verify():
            return None
        from ..domain_tracking import coordinate_domain_compatible

        if any(
            not coordinate_domain_compatible(p, sp.FiniteSet(v))
            for p, v in substitutions.items()
        ):
            return sp.S.EmptySet
        core, head, guard, _, _ = _family(
            self.expression,
            self.variable,
            self.parameters,
            self.domain,
            self.parameter_domain,
            self.value,
        )
        guard = sp.simplify(guard.subs(substitutions, simultaneous=True))
        if guard is sp.false:
            return sp.S.EmptySet
        if guard is not sp.true:
            return None
        polynomial = sp.Poly(core.subs(substitutions, simultaneous=True), self.variable)
        images = []
        for cell in _parts(self.domain):
            if cell is sp.S.EmptySet:
                continue
            if isinstance(cell, sp.FiniteSet):
                images.append(sp.FiniteSet(*(polynomial.eval(p) for p in cell)))
                continue
            sites = [
                (polynomial.eval(cell.start), not cell.left_open),
                (polynomial.eval(cell.end), not cell.right_open),
                (polynomial.eval((cell.start + cell.end) / 2), True),
            ]
            if polynomial.degree() > 2:
                for point in sp.solve(polynomial.diff().as_expr(), self.variable):
                    if point.is_real is False:
                        continue
                    if point.is_real is not True:
                        return None
                    owned = cell.contains(point)
                    if owned is sp.true:
                        sites.append((polynomial.eval(point), True))
                    elif owned is not sp.false:
                        return None
            else:
                a, b = polynomial.nth(2), polynomial.nth(1)
                if a.is_zero is False:
                    vertex = -b / (2 * a)
                    if cell.contains(vertex) is sp.true:
                        sites.append((polynomial.eval(vertex), True))
                elif a.is_zero is not True:
                    return None
            try:
                lo, hi = min(v for v, _ in sites), max(v for v, _ in sites)
                images.append(
                    sp.Interval(
                        lo,
                        hi,
                        not any(v == lo and owned for v, owned in sites),
                        not any(v == hi and owned for v, owned in sites),
                    )
                )
            except TypeError:
                return None
        image = sp.Union(*images)
        if head is not None:
            from ..real_analysis.image_rules import exact_image

            image = exact_image(head(self.variable), self.variable, image)
        return image


def _validate_coordinates(variable, parameters, value):
    from ..domain_tracking import coordinate_domain_compatible

    coordinates = (variable, value, *parameters)
    if (
        type(parameters) is not tuple
        or not parameters
        or len(set(coordinates)) != len(coordinates)
        or any(not isinstance(p, sp.Symbol) or p.is_real is False for p in coordinates)
        or not coordinate_domain_compatible(value, sp.S.Reals)
    ):
        raise ValueError(
            "use distinct real coordinate Symbols and at least one parameter"
        )


def analyze_parameter_range(
    expression,
    variable,
    parameters,
    domain,
    *,
    value=None,
    parameter_domain=sp.true,
    certified=False,
):
    """Analyze polynomial image families of degree at most three on fixed finite rational source cells.

    Coefficients may be rational functions of any number of real parameters.
    One invertible elementary outer map is supported. General transcendental
    critical-point families and parameter-dependent source cells are unresolved.
    No optimization package is imported.
    """
    if type(certified) is not bool:
        raise TypeError("certified must be a boolean")
    f, x = sp.sympify(expression), sp.sympify(variable)
    parameters = tuple(map(sp.sympify, parameters))
    y = sp.Dummy("image_value", real=True) if value is None else sp.sympify(value)
    _validate_coordinates(x, parameters, y)
    if not isinstance(domain, sp.Set):
        domain = condition_to_real_set(domain, x)
    if domain is None or domain.free_symbols:
        raise ValueError("domain must be a fixed real set")
    guard = sp.sympify(parameter_domain)
    if isinstance(guard, sp.Set) and len(parameters) == 1:
        from ..real_analysis.common import set_to_condition

        guard = set_to_condition(guard, parameters[0])
    guard = _validate_parameter_guard(guard, parameters)
    result = ParameterRangeAnalysis(f, x, parameters, domain, guard, y)
    family = _family(f, x, parameters, domain, guard, y)
    if family is None:
        return replace(result, reason="unsupported-parameter-image-family")
    result = replace(result, condition=family[3], transitions=family[4], complete=True)
    return replace(result, certified=certified and result.verify())


def parameter_range(expression, variable, parameters, domain, **kwargs):
    """Return the exact parameter-dependent image condition, or None if unsupported."""
    return analyze_parameter_range(
        expression, variable, parameters, domain, **kwargs
    ).condition
