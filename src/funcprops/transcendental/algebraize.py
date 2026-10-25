from __future__ import annotations

from dataclasses import dataclass

import sympy as sp
from sympy import S
from sympy.polys.polyerrors import PolynomialError

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..real_analysis.common import (
    condition_to_set,
    is_semialgebraic_expression,
    set_to_condition,
)


@dataclass(frozen=True)
class AlgebraizationResult:
    """Preserve source restrictions in an auxiliary algebraic representation."""

    expression: sp.Expr
    substitutions: tuple[tuple[sp.Symbol, sp.Expr], ...]
    constraints: sp.Basic = S.true
    exact: bool = True
    method: str = "none"
    source_domain: object = S.Reals
    relations: tuple[sp.Basic, ...] = ()
    inverse_substitutions: tuple[tuple[sp.Symbol, sp.Expr], ...] = ()

    @property
    def changed(self):
        return bool(self.substitutions)


def _linear_coeff(expr, var):
    try:
        p = sp.Poly(sp.expand(expr), var)
        if p.degree() <= 1:
            return p.nth(1), p.nth(0)
    except PolynomialError:
        return None
    return None


def _exp_generator(expr, var):
    exps = list(expr.atoms(sp.exp))
    if not exps:
        return None
    coeffs = []
    for e in exps:
        lc = _linear_coeff(e.args[0], var)
        if lc is None:
            return None
        a, b = lc
        if a == 0 or a.is_rational is not True or b.is_real is not True:
            return None
        coeffs.append((e, a, b))
    slopes = [sp.Rational(a) for _, a, _ in coeffs]
    from math import gcd, lcm

    L = 1
    for a in slopes:
        L = lcm(L, int(a.q))
    ints = [int(a * L) for a in slopes]
    g = abs(ints[0])
    for n in ints[1:]:
        g = gcd(g, abs(n))
    slope = sp.Rational(g, L)
    return coeffs, slope if slope else None


def _exp_domain_image(domain, var, slope):
    """Map a certified real domain through the increasing exp(slope*x).

    The slope selected by the common-generator analysis is positive rational.
    Only sets with an exact interval/finite-point representation are accepted;
    an unresolved domain must not be replaced by the unrestricted image.
    """
    if domain is None:
        return sp.Interval.open(0, sp.oo)
    source = domain if isinstance(domain, sp.Set) else condition_to_set(domain, var)

    def endpoint(value):
        if value is S.NegativeInfinity:
            return S.Zero
        if value is S.Infinity:
            return S.Infinity
        return sp.exp(slope * value)

    def image(part):
        if part is S.EmptySet:
            return S.EmptySet
        if part is S.Reals:
            return sp.Interval.open(0, sp.oo)
        if isinstance(part, sp.Interval):
            return sp.Interval(
                endpoint(part.start),
                endpoint(part.end),
                left_open=part.left_open or part.start is S.NegativeInfinity,
                right_open=part.right_open or part.end is S.Infinity,
            )
        if isinstance(part, sp.FiniteSet):
            return sp.FiniteSet(*(endpoint(value) for value in part))
        if isinstance(part, sp.Union):
            pieces = [image(piece) for piece in part.args]
            if any(piece is None for piece in pieces):
                return None
            return sp.Union(*pieces)
        return None

    if source is None or not isinstance(source, sp.Set):
        return None
    try:
        return image(sp.Intersection(source, S.Reals))
    except SYMBOLIC_QUERY_ERRORS:
        return None


def _real_power_domain(expr):
    """Domain guards for exact real rational powers in an auxiliary expression.

    SymPy noninteger powers use the principal branch, including odd roots;
    negative real bases therefore cannot enter this real auxiliary chart.

    This is structural: it does not try to determine the sign of a radicand.
    Branch-dependent guards require piecewise case analysis, so unsupported
    piecewise radicals are left to the original real-analysis machinery.
    """
    conditions = []
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Pow) and node.exp.is_Rational:
            exponent = node.exp
            if exponent.q != 1:
                if node.base.is_real is False:
                    return None
                conditions.append(
                    node.base > 0 if exponent.is_negative else node.base >= 0
                )
            elif exponent.is_negative:
                conditions.append(sp.Ne(node.base, 0))
    guard = sp.And(*conditions)
    if expr.has(sp.Piecewise) and guard is not S.true:
        return None
    return guard


def _power_nodes(expr):
    return tuple(
        node for node in sp.preorder_traversal(expr) if isinstance(node, sp.Pow)
    )


def _mapped_power_guards(powers, replacements, var, *, hyperbolic=False):
    """Transfer denominator and real-root guards into an auxiliary chart."""
    conditions = []
    for node in powers:
        # Unsupported powers must not disappear through cancellation and leave
        # an apparently algebraic expression with uncertified branch conditions.
        if node.exp.is_Rational is not True:
            return None
        base = node.base.rewrite(sp.exp) if hyperbolic else node.base
        mapped = base.xreplace(replacements)
        if mapped.has(var):
            return None
        if node.exp.q != 1:
            if mapped.is_real is False:
                return None
            conditions.append(mapped > 0 if node.exp.is_negative else mapped >= 0)
        elif node.exp.is_negative:
            conditions.append(sp.Ne(mapped, 0))
    return sp.And(*conditions)


def algebraize_exponentials(expr, var, *, source_domain=None, original_powers=()):
    """Replace commensurate real exponentials by an auxiliary positive coordinate."""

    expr = sp.sympify(expr)
    data = _exp_generator(expr, var)
    if data is None:
        return AlgebraizationResult(expr, ())
    coeffs, slope = data
    u = sp.Dummy("u", real=True)
    repl = {}
    for e, a, b in coeffs:
        power = sp.simplify(a / slope)
        if power.is_Integer is not True:
            return AlgebraizationResult(expr, ())
        repl[e] = sp.exp(b) * u**power
    power_guard = _mapped_power_guards(
        (*_power_nodes(expr), *original_powers), repl, var, hyperbolic=True
    )
    if power_guard is None:
        return AlgebraizationResult(expr, ())
    new = sp.cancel(expr.xreplace(repl))
    if new.has(var) or not is_semialgebraic_expression(new, u):
        return AlgebraizationResult(expr, ())
    real_guard = _real_power_domain(new)
    if real_guard is None:
        return AlgebraizationResult(expr, ())
    auxiliary_domain = _exp_domain_image(source_domain, var, slope)
    if auxiliary_domain is None:
        return AlgebraizationResult(expr, ())
    return AlgebraizationResult(
        new,
        ((u, sp.exp(slope * var)),),
        sp.And(set_to_condition(auxiliary_domain, u), power_guard, real_guard),
        True,
        "exponential_substitution",
        S.Reals if source_domain is None else source_domain,
        (),
        ((var, sp.log(u) / slope),),
    )


def rewrite_hyperbolic_to_exp(expr):
    """Rewrite supported hyperbolic heads using exponential identities."""

    expr = sp.sympify(expr)
    if expr.has(sp.sinh, sp.cosh, sp.tanh, sp.coth, sp.sech, sp.csch):
        try:
            return sp.cancel(expr.rewrite(sp.exp))
        except SYMBOLIC_QUERY_ERRORS:
            return expr
    return expr


def _half_angle_domain(domain, var):
    """Map a subset of (-pi, pi) exactly through tan(x/2)."""
    branch = sp.Interval.open(-sp.pi, sp.pi)
    source = (
        branch
        if domain is None
        else (domain if isinstance(domain, sp.Set) else condition_to_set(domain, var))
    )
    if not isinstance(source, sp.Set) or source.is_subset(branch) is not True:
        return None

    def endpoint(value):
        if value == -sp.pi:
            return S.NegativeInfinity
        if value == sp.pi:
            return S.Infinity
        return sp.tan(value / 2)

    def image(part):
        if part is S.EmptySet:
            return S.EmptySet
        if isinstance(part, sp.Interval):
            return sp.Interval(
                endpoint(part.start),
                endpoint(part.end),
                left_open=part.left_open,
                right_open=part.right_open,
            )
        if isinstance(part, sp.FiniteSet):
            return sp.FiniteSet(*(endpoint(value) for value in part))
        if isinstance(part, sp.Union):
            pieces = [image(piece) for piece in part.args]
            if any(piece is None for piece in pieces):
                return None
            return sp.Union(*pieces)
        return None

    try:
        mapped = image(source)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    return (source, mapped) if mapped is not None else None


def algebraize_trigonometric(expr, var, *, source_domain=None):
    """Use the tangent-half-angle chart on a proven subset of (-pi, pi).

    The chart is bijective there. Domains extending outside the chart are
    rejected instead of truncated; all finite interval endpoints
    and excluded points must survive the change of variables.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if not expr.has(sp.sin(var), sp.cos(var)):
        return AlgebraizationResult(expr, ())
    if any(a.args[0] != var for a in expr.atoms(sp.sin, sp.cos)):
        return AlgebraizationResult(expr, ())
    u = sp.Dummy("t", real=True)
    mapped = _half_angle_domain(source_domain, var)
    if mapped is None:
        return AlgebraizationResult(expr, ())
    source, auxiliary = mapped
    repl = {
        sp.sin(var): 2 * u / (1 + u**2),
        sp.cos(var): (1 - u**2) / (1 + u**2),
    }
    power_guard = _mapped_power_guards(_power_nodes(expr), repl, var)
    if power_guard is None:
        return AlgebraizationResult(expr, ())
    new = sp.cancel(expr.xreplace(repl))
    if new.has(var) or not is_semialgebraic_expression(new, u):
        return AlgebraizationResult(expr, ())
    real_guard = _real_power_domain(new)
    if real_guard is None:
        return AlgebraizationResult(expr, ())
    return AlgebraizationResult(
        new,
        ((u, sp.tan(var / 2)),),
        sp.And(set_to_condition(auxiliary, u), power_guard, real_guard),
        True,
        "tangent_half_angle",
        source,
        (),
        ((var, 2 * sp.atan(u)),),
    )


def algebraize_trig_circle(expr, var):
    """Replace direct sine/cosine terms on a complete phase circle.

    The circle equation describes exactly the reachable pairs over a full
    period. It does not eliminate independent occurrences of the phase.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if not (expr.has(sp.sin(var)) or expr.has(sp.cos(var))):
        return AlgebraizationResult(expr, ())
    if any(a.args[0] != var for a in expr.atoms(sp.sin, sp.cos)):
        return AlgebraizationResult(expr, ())
    s = sp.Dummy("s", real=True)
    c = sp.Dummy("c", real=True)
    repl = {sp.sin(var): s, sp.cos(var): c}
    power_guard = _mapped_power_guards(_power_nodes(expr), repl, var)
    if power_guard is None:
        return AlgebraizationResult(expr, ())
    new = expr.xreplace(repl)
    if (
        new.has(var)
        or not is_semialgebraic_expression(new, s)
        or not is_semialgebraic_expression(new, c)
    ):
        return AlgebraizationResult(expr, ())
    real_guard = _real_power_domain(new)
    if real_guard is None:
        return AlgebraizationResult(expr, ())
    circle = sp.Eq(s**2 + c**2, 1)
    denominator = sp.denom(sp.cancel(new))
    constraints = sp.And(circle, power_guard, real_guard, sp.Ne(denominator, 0))
    return AlgebraizationResult(
        new,
        ((s, sp.sin(var)), (c, sp.cos(var))),
        constraints,
        True,
        "trig_circle",
        sp.Interval.Ropen(0, 2 * sp.pi),
        (circle,),
    )


def algebraize_common_subexprs(expr, var):
    """Introduce auxiliary variables for supported repeated algebraic subexpressions."""

    expr = sp.sympify(expr)
    counts = {}
    for node in sp.preorder_traversal(expr):
        if isinstance(node, sp.Function) and node.has(var):
            counts[node] = counts.get(node, 0) + 1
    repeated = [e for e, n in counts.items() if n > 1]
    if not repeated:
        return AlgebraizationResult(expr, ())
    repl = {
        e: sp.Dummy(f"t{i}", real=True)
        for i, e in enumerate(sorted(repeated, key=sp.default_sort_key), 1)
    }
    return AlgebraizationResult(
        expr.xreplace(repl),
        tuple((v, k) for k, v in repl.items()),
        S.true,
        False,
        "common_subexpression",
    )


def algebraize(expr, var, *, domain=None, allow_trig=False):
    """Transform supported transcendental expressions while retaining exact domain constraints."""

    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if is_semialgebraic_expression(expr, var):
        return AlgebraizationResult(expr, ())
    rewritten = rewrite_hyperbolic_to_exp(expr)
    r = algebraize_exponentials(
        rewritten, var, source_domain=domain, original_powers=_power_nodes(expr)
    )
    if r.changed:
        return r
    if allow_trig:
        r = algebraize_trigonometric(expr, var, source_domain=domain)
        if r.changed:
            return r
    return AlgebraizationResult(expr, ())
