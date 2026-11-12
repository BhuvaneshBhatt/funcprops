"""Explicit whole-tail value bounds for continuous coercive image assembly."""

from dataclasses import dataclass, replace

import sympy as sp

from ..analysis import value_enclosure
from ..domain_tracking import track_domain
from ..source_syntax import same_data

_ERRORS = (TypeError, ValueError, AttributeError, ArithmeticError, NotImplementedError)


def _bounded(expression, variable, domain):
    """Bound a fixed oscillatory expression by structural interval arithmetic."""
    if not expression.has(variable):
        w = value_enclosure(expression, variable, sp.FiniteSet(0))
        return (w.lower, w.upper) if w is not None else None
    if expression.func in (sp.sin, sp.cos, sp.tanh, sp.erf):
        record = track_domain(expression.args[0], variable, domain)
        return (
            (-sp.S.One, sp.S.One)
            if record.complete and record.effective == domain
            else None
        )
    if expression.is_Add or expression.is_Mul:
        values = [_bounded(a, variable, domain) for a in expression.args]
        if any(v is None for v in values):
            return None
        low, high = (
            (sp.S.Zero, sp.S.Zero) if expression.is_Add else (sp.S.One, sp.S.One)
        )
        for a, b in values:
            if expression.is_Add:
                low, high = low + a, high + b
            else:
                products = (low * a, low * b, high * a, high * b)
                low, high = min(products), max(products)
        return low, high
    if expression.is_Pow and expression.exp.is_Integer and 0 <= expression.exp <= 16:
        bound = _bounded(expression.base, variable, domain)
        if bound is None:
            return None
        a, b = bound
        n = int(expression.exp)
        points = [a**n, b**n]
        if n and n % 2 == 0 and a <= 0 <= b:
            points.append(sp.S.Zero)
        return min(points), max(points)
    return None


def _tail_data(expression, variable, domain):
    """Derive polynomial dominance after shifting the entire tail to t>0."""
    if not isinstance(domain, sp.Interval) or not (
        domain.start is -sp.oo or domain.end is sp.oo
    ):
        return None
    direction = 1 if domain.end is sp.oo else -1
    if (domain.left_open if direction == 1 else domain.right_open) is not sp.true:
        return None
    cutoff = domain.start if direction == 1 else domain.end
    if cutoff.is_Rational is not True:
        return None
    record = track_domain(expression, variable, domain)
    if not record.complete or record.effective != domain:
        return None
    if sp.calculus.util.continuous_domain(expression, variable, domain) != domain:
        return None
    terms = sp.Add.make_args(sp.expand(expression))
    trend = sp.Add(*(a for a in terms if a.is_polynomial(variable)))
    remainder = sp.Add(*(a for a in terms if not a.is_polynomial(variable)))
    bounds = _bounded(remainder, variable, domain)
    if bounds is None:
        return None
    t = sp.Dummy("outward_distance", positive=True)
    try:
        polynomial = sp.Poly(
            trend.subs(variable, cutoff + direction * t), t, domain=sp.QQ
        )
    except (sp.PolynomialError, sp.polys.polyerrors.CoercionFailed):
        return None
    if polynomial.degree() < 1:
        return None
    coefficients = polynomial.all_coeffs()[:-1]
    if all(c >= 0 for c in coefficients):
        return trend, remainder, bounds, sp.oo, polynomial.nth(0) + bounds[0]
    if all(c <= 0 for c in coefficients):
        return trend, remainder, bounds, -sp.oo, polynomial.nth(0) + bounds[1]
    return None


@dataclass(frozen=True)
class TailValueBound:
    """A whole-tail function bound and infinite limit, independent of monotonicity.

    The remainder uses checked structural bounds; polynomial dominance supplies
    both a finite exclusion bound and the limit. A provider's certification flag
    is metadata and never substitutes for these source-bound premises.
    """

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    trend: sp.Expr
    remainder: sp.Expr
    remainder_bounds: tuple
    limit: sp.Expr
    bound: sp.Expr
    certified: bool = False

    def verify(self):
        """Replay source continuity, bounded remainder and outward polynomial signs."""
        try:
            return (
                type(self) is TailValueBound
                and type(self.certified) is bool
                and same_data(
                    _tail_data(self.expression, self.variable, self.domain),
                    (
                        self.trend,
                        self.remainder,
                        self.remainder_bounds,
                        self.limit,
                        self.bound,
                    ),
                )
            )
        except _ERRORS:
            return False


def bound_range_tail(expression, variable, domain, *, limit=None, certified=False):
    """Return supported explicit polynomial-plus-bounded-remainder tail facts.

    A supplied limit is a proposal checked against the whole-tail squeeze.
    None denotes unsupported dominance, continuity or bounded-remainder work.
    """
    if type(certified) is not bool:
        raise TypeError("certified must be a boolean")
    f, x = sp.sympify(expression), sp.sympify(variable)
    if (
        not isinstance(x, sp.Symbol)
        or x.is_real is False
        or f.free_symbols - {x}
        or f.has(sp.Float)
    ):
        return None
    try:
        data = _tail_data(f, x, domain)
    except _ERRORS:
        return None
    if data is None:
        data = finite_tail_data(f, x, domain)
        if data is None or (limit is not None and sp.sympify(limit) != data[0]):
            return None
        result = FiniteTailBound(f, x, domain, *data)
        return replace(result, certified=certified and result.verify())
    if limit is not None and sp.sympify(limit) != data[3]:
        return None
    result = TailValueBound(f, x, domain, *data)
    return replace(result, certified=certified and result.verify())


@dataclass(frozen=True)
class BoundedTailImage:
    """A compact image with tail exclusion, or opposite-limit surjectivity.

    core=None records the latter theorem, which needs no critical-root search.
    """

    core: object
    tails: tuple


def opposite_tail_summary(expression, variable, domain, tails):
    """Prove surjectivity from continuity and checked opposite infinite limits."""
    if domain is not sp.S.Reals and not isinstance(domain, sp.Interval):
        return None
    if (
        type(tails) is not tuple
        or not tails
        or any(
            type(t) is not TailValueBound
            or t.expression != expression
            or t.variable != variable
            or t.domain.is_subset(domain) is not True
            or not t.verify()
            for t in tails
        )
    ):
        return None
    if {t.limit for t in tails} != {-sp.oo, sp.oo}:
        return None
    return (
        sp.S.Reals
        if sp.calculus.util.continuous_domain(expression, variable, domain) == domain
        else None
    )


def bounded_tail_summary(expression, variable, domain, core, tails):
    """Join an exact compact image to continuous tails with one infinite limit."""
    from ..analytic_roots import CriticalValue

    if (
        (domain is not sp.S.Reals and not isinstance(domain, sp.Interval))
        or type(tails) is not tuple
        or not tails
        or core.expression != expression
        or core.variable != variable
        or not core.complete
        or not isinstance(core.image, (sp.Interval, sp.FiniteSet))
    ):
        return None
    if sp.calculus.util.continuous_domain(expression, variable, domain) != domain:
        return None
    if any(
        type(t) is not TailValueBound
        or t.expression != expression
        or t.variable != variable
        or not t.verify()
        for t in tails
    ):
        return None
    regions = (core.domain_record.effective, *(t.domain for t in tails))
    if sp.Union(*regions) != domain or any(
        sp.Intersection(a, b) is not sp.S.EmptySet
        for i, a in enumerate(regions)
        for b in regions[i + 1 :]
    ):
        return None
    limits = {t.limit for t in tails}
    if len(limits) != 1:
        return None
    upward = next(iter(limits)) is sp.oo
    endpoint = core.image.inf if upward else core.image.sup
    # A rational enclosure suffices to compare a finite tail bound with an
    # implicit core extremum. Exact equality is also valid at the join.
    bound = endpoint.enclosure(20) if type(endpoint) is CriticalValue else None
    comparison = (
        bound.upper
        if bound is not None and upward
        else bound.lower
        if bound is not None
        else endpoint
    )
    if not all(
        (t.bound >= comparison if upward else t.bound <= comparison) is sp.true
        for t in tails
    ):
        return None
    owned = core.image.contains(endpoint) is sp.true
    return (
        sp.Interval(endpoint, sp.oo, not owned, True)
        if upward
        else sp.Interval(-sp.oo, endpoint, True, not owned)
    )


@dataclass(frozen=True)
class FiniteTailBound:
    """A finite limit and whole-tail interval for rationally damped oscillation."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    limit: sp.Expr
    lower: sp.Expr
    upper: sp.Expr
    certified: bool = False

    def verify(self):
        """Replay rational amplitude ranges and checked bounded oscillator factors."""
        try:
            data = finite_tail_data(self.expression, self.variable, self.domain)
            return (
                type(self) is FiniteTailBound
                and type(self.certified) is bool
                and data is not None
                and same_data(data, (self.limit, self.lower, self.upper))
            )
        except _ERRORS:
            return False


def finite_tail_data(expression, variable, domain):
    """Bound a constant plus rationally decaying bounded oscillators on a tail."""
    from ..source_syntax import normalize_arithmetic

    if not isinstance(domain, sp.Interval) or not (
        domain.start is -sp.oo or domain.end is sp.oo
    ):
        return None
    cutoff = domain.start if domain.end is sp.oo else domain.end
    if (
        cutoff.is_Rational is not True
        or (domain.left_open if domain.end is sp.oo else domain.right_open)
        is not sp.true
    ):
        return None
    if expression.free_symbols - {variable} or expression.has(sp.Float):
        return None
    record = track_domain(expression, variable, domain)
    if not record.complete or record.effective != domain:
        return None
    f = normalize_arithmetic(expression)
    if sp.calculus.util.continuous_domain(f, variable, domain) != domain:
        return None
    limit = sp.S.Zero
    low = sp.S.Zero
    high = sp.S.Zero
    for term in sp.Add.make_args(sp.expand(f)):
        if not term.has(variable):
            if term.is_finite is not True or term.is_real is not True:
                return None
            limit += term
            low += term
            high += term
            continue
        factors = sp.Mul.make_args(term)
        rational = sp.Mul(*(a for a in factors if a.is_rational_function(variable)))
        bounded = sp.Mul(*(a for a in factors if not a.is_rational_function(variable)))
        n, d = sp.fraction(sp.cancel(rational))
        try:
            num, den = (sp.Poly(a, variable, domain=sp.QQ) for a in (n, d))
        except (sp.PolynomialError, sp.polys.polyerrors.CoercionFailed):
            return None
        if not 0 <= num.degree() < den.degree() <= 6:
            return None
        bounds = _bounded(bounded, variable, domain)
        if bounds is None:
            return None
        image = sp.calculus.util.function_range(rational, variable, domain)
        if not isinstance(image, sp.Interval) or any(
            a.is_finite is not True for a in (image.start, image.end)
        ):
            return None
        products = tuple(a * b for a in (image.start, image.end) for b in bounds)
        low += min(products)
        high += max(products)
    return limit, low, high


def finite_tail_summary(expression, variable, domain, core, tails):
    """Exclude both finite tail bounds using an exact source-bound core image."""
    from ..analytic_roots import CriticalValue

    if (
        not core.complete
        or not isinstance(core.image, sp.Interval)
        or core.expression != expression
        or core.variable != variable
        or type(tails) is not tuple
        or not tails
        or any(
            type(t) is not FiniteTailBound
            or t.expression != expression
            or t.variable != variable
            or not t.verify()
            for t in tails
        )
    ):
        return None
    regions = (core.domain_record.effective, *(t.domain for t in tails))
    if sp.Union(*regions) != domain or any(
        sp.Intersection(a, b) is not sp.S.EmptySet
        for i, a in enumerate(regions)
        for b in regions[i + 1 :]
    ):
        return None
    lower, upper = core.image.start, core.image.end
    if type(lower) is CriticalValue:
        lower = lower.enclosure(20).upper
    if type(upper) is CriticalValue:
        upper = upper.enclosure(20).lower
    for t in tails:
        if (
            t.lower > lower if core.image.left_open else t.lower >= lower
        ) is not sp.true or (
            t.upper < upper if core.image.right_open else t.upper <= upper
        ) is not sp.true:
            return None
    return core.image
