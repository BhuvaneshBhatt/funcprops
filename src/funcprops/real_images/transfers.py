"""Source-preserving elementary, periodic and monotone-tail image transfers."""

from dataclasses import dataclass, replace
from functools import reduce
from math import gcd, lcm

import sympy as sp

from ..analysis import derivative_on_domain
from ..exactness import certify_identity_equal
from ..source_syntax import same_data
from .tails import BoundedTailImage

_TRIG = (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc)


@dataclass(frozen=True)
class ElementaryImage:
    """A primitive real image computed on the complete effective source set."""


@dataclass(frozen=True)
class ComposedImage:
    """A fixed outer function applied to a source-bound inner image analysis."""

    outer: sp.Lambda
    inner: object


@dataclass(frozen=True)
class PeriodicImage:
    """A domain-periodic source represented by a fully contained period window."""

    period: sp.Expr
    window: sp.Interval
    analysis: object


@dataclass(frozen=True)
class ReflectedImage:
    """Reduce a symmetric source and even function to its nonnegative half."""

    analysis: object


@dataclass(frozen=True)
class RealFormulaImage:
    """A source-restricted real formula obtained by exact branch expansion."""

    formula: sp.Expr
    analysis: object


@dataclass(frozen=True)
class ComponentImage:
    """Images of all disjoint effective source components, with no omissions."""

    analyses: tuple


@dataclass(frozen=True)
class MonotoneTail:
    """A C1 tail image with strict derivative-sign and endpoint-limit premises."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    sign_proof: object
    limit: sp.Expr
    image: sp.Set

    def verify(self):
        """Replay smoothness, the entire-tail sign and its exact limit."""
        from ..asymptotic_tails import TailSignCertificate

        D = self.domain
        x = self.variable
        f = self.expression
        p = self.sign_proof
        if (
            type(self) is not MonotoneTail
            or type(p) is not TailSignCertificate
            or not isinstance(D, sp.Interval)
        ):
            return False
        direction = 1 if D.end is sp.oo else -1 if D.start is -sp.oo else None
        if direction is None or not p.verify() or p.direction != direction:
            return False
        cutoff = D.start if direction == 1 else D.end
        if (
            cutoff != direction * sp.Abs(p.threshold)
            or derivative_on_domain(f, x, D.closure) is None
            or not same_data(p.expression, sp.diff(f, x))
            or p.variable != x
        ):
            return False
        limit = sp.limit(f, x, direction * sp.oo)
        return same_data(limit, self.limit) and same_data(
            self.image, _tail_image(f, x, D, p.sign, limit)
        )


@dataclass(frozen=True)
class TailImage:
    """A compact core and all remaining proved monotone tails."""

    core: object
    tails: tuple


def _known_image(f, x, D):
    from ..real_analysis.image_rules import exact_image

    if f == x:
        return D
    from ..source_syntax import normalize_arithmetic

    formula = normalize_arithmetic(f)
    if (
        x not in formula.free_symbols
        and formula.is_real is True
        and formula.is_finite is True
    ):
        return sp.S.EmptySet if D is sp.S.EmptySet else sp.FiniteSet(formula)
    source = sp.Interval(-sp.oo, sp.oo) if D is sp.S.Reals else D
    image = exact_image(f, x, source)
    if image is not None:
        return image
    # Reduce a polynomial in sin(x), cos(x) modulo their circle identity.
    # This recognizes, for example, sin(x) + cos(2*x) as a quadratic in sin(x).
    if not f.has(sp.sin(x), sp.cos(x)):
        return None
    sine, cosine = sp.Dummy("sine", real=True), sp.Dummy("cosine", real=True)
    expanded = sp.expand_trig(f).xreplace({sp.sin(x): sine, sp.cos(x): cosine})
    if expanded.has(x) or not expanded.is_polynomial(sine, cosine):
        return None
    for eliminated, kept, head in ((cosine, sine, sp.sin), (sine, cosine, sp.cos)):
        remainder = sp.rem(expanded, eliminated**2 + kept**2 - 1, eliminated)
        if not remainder.has(eliminated):
            inner = exact_image(head(x), x, source)
            if inner is not None:
                image = exact_image(remainder, kept, inner)
                if image is not None:
                    return image
    return None


def _period_invariant(f, x, P):
    if not f.has(x):
        return True
    if f.func in _TRIG:
        arg = f.args[0]
        try:
            p = sp.Poly(arg, x)
        except sp.PolynomialError:
            return False
        if p.degree() != 1 or p.free_symbols - {x}:
            return False
        from ..domain_tracking import track_domain

        domain = track_domain(arg, x)
        unit = sp.pi if f.func in (sp.tan, sp.cot) else 2 * sp.pi
        return (
            domain.complete
            and domain.effective is sp.S.Reals
            and sp.simplify(p.nth(1) * P / unit).is_integer is True
        )
    if f == x or not f.args:
        return False
    return all(_period_invariant(a, x, P) for a in f.args)


def _source_period(f, x):
    heads = [a for a in sp.preorder_traversal(f) if a.func in _TRIG and a.has(x)]
    if not heads:
        return None
    slopes = []
    for head in heads:
        try:
            p = sp.Poly(head.args[0], x)
        except sp.PolynomialError:
            return None
        if p.degree() != 1:
            return None
        slopes.append(p.nth(1))
    base = slopes[0]
    ratios = [sp.simplify(a / base) for a in slopes]
    if any(r.is_Rational is not True for r in ratios):
        return None
    denominator = reduce(lcm, (int(r.q) for r in ratios), 1)
    numerator = reduce(gcd, (abs(int(r.p)) for r in ratios))
    period = sp.simplify(2 * sp.pi * denominator / (numerator * sp.Abs(base)))
    return (
        period
        if period.is_positive is True and _period_invariant(f, x, period)
        else None
    )


def _tail_image(f, x, D, sign, limit):
    point = D.start if D.end is sp.oo else D.end
    value = sp.simplify(f.subs(x, point))
    if (
        value.is_real is not True
        or value.is_finite is not True
        or limit.is_extended_real is not True
    ):
        return None
    values = (value, limit) if D.end is sp.oo else (limit, value)
    if sign < 0:
        values = values[::-1]
    return sp.Interval(values[0], values[1], True, True)


def _summary(seed, transfer, image, inner, outer, unresolved):
    return replace(
        seed,
        transfer=transfer,
        image=image,
        inner=inner,
        outer=outer,
        unresolved=unresolved,
        reason=None if image is not None else "unresolved-transferred-image",
    )


def _bounded_transfer(seed, policy, facts, previous):
    """Assemble a source-bound core and tails that cannot improve its extremum."""
    from .analysis import analyze_range
    from .tails import (
        FiniteTailBound,
        bounded_tail_summary,
        finite_tail_summary,
        opposite_tail_summary,
    )

    f, x, D = seed.expression, seed.variable, seed.domain_record.effective
    finite = all(type(t) is FiniteTailBound for t in facts)
    if not finite and opposite_tail_summary(f, x, D, facts) is not None:
        return _summary(
            seed,
            BoundedTailImage(None, facts),
            sp.S.Reals,
            sp.S.Reals,
            sp.S.Reals,
            sp.S.EmptySet,
        )
    core_domain = sp.Complement(D, sp.Union(*(t.domain for t in facts)))
    core = analyze_range(
        f,
        x,
        core_domain,
        policy=policy,
        _previous=previous.core if type(previous) is BoundedTailImage else None,
    )
    image = (finite_tail_summary if finite else bounded_tail_summary)(
        f, x, D, core, facts
    )
    return (
        _summary(
            seed, BoundedTailImage(core, facts), image, image, image, sp.S.EmptySet
        )
        if image is not None
        else None
    )


def propose_transfer(seed, policy, previous=None, tail_facts=()):
    """Try primitive images, composition, periodic windows, then proved tails."""
    from ..real_analysis.image_rules import exact_image
    from .analysis import analyze_range

    f, x, D = seed.expression, seed.variable, seed.domain_record.effective
    if tail_facts:
        transfer = _bounded_transfer(seed, policy, tail_facts, previous)
        if transfer is not None:
            return transfer
    image = _known_image(f, x, D)
    if image is not None:
        return _summary(seed, ElementaryImage(), image, image, image, sp.S.EmptySet)
    from ..real_analysis.domain import (
        _has_complex_intermediates,
        _real_formula_on_domain,
    )

    if _has_complex_intermediates(f, x):
        if isinstance(D, sp.Union):
            children = tuple(
                analyze_range(f, x, part, policy=policy) for part in _parts(D)
            )
            if all(
                child.verify() and child.domain_record.effective == part
                for child, part in zip(children, _parts(D), strict=True)
            ):
                return _summary(
                    seed, ComponentImage(children), *_component_images(children)
                )
        formula = _real_formula_on_domain(f, x, D)
        if formula is not None and formula != f:
            child = analyze_range(formula, x, D, policy=policy)
            if child.verify() and child.domain_record.effective == D:
                return _summary(
                    seed,
                    RealFormulaImage(formula, child),
                    child.image,
                    child.inner,
                    child.outer,
                    child.unresolved,
                )
    from .oscillatory import OscillatoryEscape, escape_data

    data = escape_data(f, x, D)
    if data is not None:
        return _summary(
            seed,
            OscillatoryEscape(f, x, D, *data),
            sp.S.Reals,
            sp.S.Reals,
            sp.S.Reals,
            sp.S.EmptySet,
        )
    from .trigonometric import DenseTrigImage, dense_trig_data

    dense = dense_trig_data(f, x, D)
    if dense is not None:
        image = dense[-1]
        return _summary(
            seed, DenseTrigImage(f, x, D, *dense), image, image, image, sp.S.EmptySet
        )
    positive = sp.Intersection(D, sp.Interval(0, sp.oo))
    if (
        isinstance(D, sp.Union)
        and positive != D
        and sp.Union(positive, sp.imageset(sp.Lambda(x, -x), positive)) == D
        and certify_identity_equal(f, f.subs(x, -x)) is True
    ):
        child = analyze_range(f, x, positive, policy=policy)
        if child.verify():
            return _summary(
                seed,
                ReflectedImage(child),
                child.image,
                child.inner,
                child.outer,
                sp.S.EmptySet if child.complete else D,
            )
    varying = [(i, a) for i, a in enumerate(f.args) if a.has(x)]
    if len(varying) == 1 and f.func not in (sp.Add, sp.Mul, sp.Piecewise):
        i, g = varying[0]
        if g != x:
            u = sp.Dummy("image_argument", real=True)
            args = list(f.args)
            args[i] = u
            outer = f.func(*args)
            if (
                same_data(sp.Lambda(u, outer)(g), f)
                and exact_image(outer, u, sp.FiniteSet(0, 1)) is not None
            ):
                child = analyze_range(
                    g,
                    x,
                    D,
                    policy=policy,
                    _previous=previous.inner
                    if type(previous) is ComposedImage
                    else None,
                )
                if child.verify() and child.domain_record.effective == D:
                    image = (
                        exact_image(outer, u, child.image)
                        if child.image is not None
                        else None
                    )
                    inner = exact_image(outer, u, child.inner)
                    enclosure = exact_image(outer, u, child.outer)
                    inner = sp.S.EmptySet if inner is None else inner
                    enclosure = sp.S.Reals if enclosure is None else enclosure
                    if image is None and same_data(inner, enclosure):
                        image = inner
                    return _summary(
                        seed,
                        ComposedImage(sp.Lambda(u, outer), child),
                        image,
                        inner,
                        enclosure,
                        sp.S.EmptySet if image is not None else D,
                    )
    from ..analysis import condition_to_real_set

    requested = condition_to_real_set(seed.requested, x)
    if isinstance(requested, sp.Interval) and (
        requested.start is -sp.oo or requested.end is sp.oo
    ):
        P = _source_period(f, x)
        if P is not None:
            width = sp.ceiling(P)
            if width.is_Integer is not True:
                return None
            if requested.start is not -sp.oo:
                start = sp.ceiling(requested.start) + 1
            elif requested.end is not sp.oo:
                start = sp.floor(requested.end) - width - 1
            else:
                start = sp.S.Zero
            if start.is_Integer is not True:
                return None
            window = sp.Interval(start, start + width)
            child = analyze_range(
                f,
                x,
                window,
                policy=policy,
                _previous=previous.analysis
                if type(previous) is PeriodicImage
                else None,
            )
            if child.verify():
                return _summary(
                    seed,
                    PeriodicImage(P, window, child),
                    child.image,
                    child.inner,
                    child.outer,
                    sp.S.EmptySet if child.complete else D,
                )
    if not isinstance(D, sp.Interval) or (D.start is not -sp.oo and D.end is not sp.oo):
        return None
    from ..asymptotic_tails import certify_tail_sign

    for T in (1, 2, 4, 8, 16, 32):
        if D.start is not -sp.oo and (D.start < T) is not sp.true:
            continue
        if D.end is not sp.oo and (-T < D.end) is not sp.true:
            continue
        core = sp.Intersection(D, sp.Interval(-T, T))
        tails = []
        for wing in _parts(sp.Complement(D, core)):
            if (
                not isinstance(wing, sp.Interval)
                or derivative_on_domain(f, x, wing.closure) is None
            ):
                break
            direction = 1 if wing.end is sp.oo else -1
            proof = certify_tail_sign(
                sp.diff(f, x), x, direction=direction, threshold=T
            )
            if proof is None:
                break
            limit = sp.limit(f, x, direction * sp.oo)
            if limit.has(sp.Limit, sp.AccumBounds, sp.Piecewise):
                break
            image = _tail_image(f, x, wing, proof.sign, limit)
            if image is None:
                break
            tail = MonotoneTail(f, x, wing, proof, limit, image)
            if not tail.verify():
                break
            tails.append(tail)
        else:
            previous_core = (
                previous.core
                if type(previous) is TailImage and previous.core.requested == core
                else None
            )
            child = analyze_range(f, x, core, policy=policy, _previous=previous_core)
            if child.verify():
                image = (
                    sp.Union(child.image, *(t.image for t in tails))
                    if child.image is not None
                    else None
                )
                return _summary(
                    seed,
                    TailImage(child, tuple(tails)),
                    image,
                    sp.Union(child.inner, *(t.image for t in tails)),
                    sp.Union(child.outer, *(t.image for t in tails)),
                    child.unresolved,
                )
    from .tails import bound_range_tail

    for threshold in (sp.Rational(1, 2), 1, 2, 4, 8, 16, 32):
        core = sp.Intersection(D, sp.Interval(-threshold, threshold))
        if core is sp.S.EmptySet:
            continue
        wings = _parts(sp.Complement(D, core))
        facts = tuple(bound_range_tail(f, x, wing) for wing in wings)
        if facts and all(fact is not None for fact in facts):
            transfer = _bounded_transfer(seed, policy, facts, previous)
            if transfer is not None:
                return transfer
    return None


def _component_images(children):
    return (
        sp.Union(*(c.image for c in children))
        if all(c.complete for c in children)
        else None,
        sp.Union(*(c.inner for c in children)),
        sp.Union(*(c.outer for c in children)),
        sp.Union(*(c.unresolved for c in children)),
    )


def _parts(D):
    return D.args if isinstance(D, sp.Union) else () if D is sp.S.EmptySet else (D,)


def verify_transfer(result):
    """Replay transfer premises and bind every child to the parent source request."""
    from ..real_analysis.image_rules import exact_image
    from .analysis import RangeAnalysis

    t = result.transfer
    f, x, D = result.expression, result.variable, result.domain_record.effective
    if result.cells:
        return False
    from .oscillatory import OscillatoryEscape
    from .trigonometric import DenseTrigImage

    if type(t) is OscillatoryEscape:
        if t.expression != f or t.variable != x or t.domain != D or not t.verify():
            return False
        expected = (sp.S.Reals, sp.S.Reals, sp.S.Reals, sp.S.EmptySet)
    elif type(t) is DenseTrigImage:
        if t.expression != f or t.variable != x or t.domain != D or not t.verify():
            return False
        expected = (t.image, t.image, t.image, sp.S.EmptySet)
    elif type(t) is ElementaryImage:
        image = _known_image(f, x, D)
        return image is not None and same_data(
            (result.image, result.inner, result.outer, result.unresolved),
            (image, image, image, sp.S.EmptySet),
        )
    elif type(t) is ReflectedImage:
        child = t.analysis
        positive = sp.Intersection(D, sp.Interval(0, sp.oo))
        if (
            type(child) is not RangeAnalysis
            or child.expression != f
            or child.variable != x
            or child.requested != positive
            or not child.verify()
            or sp.Union(positive, sp.imageset(sp.Lambda(x, -x), positive)) != D
            or certify_identity_equal(f, f.subs(x, -x)) is not True
        ):
            return False
        expected = (
            child.image,
            child.inner,
            child.outer,
            sp.S.EmptySet if child.complete else D,
        )
    elif type(t) is RealFormulaImage:
        from ..real_analysis.domain import _real_formula_on_domain

        child = t.analysis
        if (
            type(child) is not RangeAnalysis
            or child.expression != t.formula
            or child.variable != x
            or child.requested != D
            or child.domain_record.effective != D
            or not child.verify()
            or _real_formula_on_domain(f, x, D) != t.formula
        ):
            return False
        expected = (child.image, child.inner, child.outer, child.unresolved)
    elif type(t) is ComponentImage:
        if (
            not isinstance(D, sp.Union)
            or type(t.analyses) is not tuple
            or len(t.analyses) != len(_parts(D))
        ):
            return False
        for child, part in zip(t.analyses, _parts(D), strict=True):
            if (
                type(child) is not RangeAnalysis
                or child.expression != f
                or child.variable != x
                or child.requested != part
                or child.domain_record.effective != part
                or not child.verify()
            ):
                return False
        expected = _component_images(t.analyses)
    elif type(t) is ComposedImage:
        child = t.inner
        if (
            type(child) is not RangeAnalysis
            or not child.verify()
            or child.variable != x
            or child.requested != D
            or child.domain_record.effective != D
            or not same_data(t.outer(child.expression), f)
        ):
            return False
        u = t.outer.variables[0]
        outer = t.outer.expr
        image = exact_image(outer, u, child.image) if child.image is not None else None
        inner = exact_image(outer, u, child.inner)
        enclosure = exact_image(outer, u, child.outer)
        inner = sp.S.EmptySet if inner is None else inner
        enclosure = sp.S.Reals if enclosure is None else enclosure
        if image is None and same_data(inner, enclosure):
            image = inner
        expected = (image, inner, enclosure, sp.S.EmptySet if image is not None else D)
    elif type(t) is PeriodicImage:
        from ..analysis import condition_to_real_set

        requested = condition_to_real_set(result.requested, x)
        child = t.analysis
        if (
            type(child) is not RangeAnalysis
            or not child.verify()
            or child.expression != f
            or child.variable != x
            or child.requested != t.window
            or not isinstance(requested, sp.Interval)
            or not (requested.start is -sp.oo or requested.end is sp.oo)
            or (t.window.measure >= t.period) is not sp.true
            or t.window.is_subset(requested) is not True
            or t.period.is_positive is not True
            or not _period_invariant(f, x, t.period)
        ):
            return False
        expected = (
            child.image,
            child.inner,
            child.outer,
            sp.S.EmptySet if child.complete else D,
        )
    elif type(t) is BoundedTailImage:
        from .tails import (
            FiniteTailBound,
            bounded_tail_summary,
            finite_tail_summary,
            opposite_tail_summary,
        )

        if type(t.tails) is not tuple:
            return False
        if t.core is None:
            image = opposite_tail_summary(f, x, D, t.tails)
        elif type(t.core) is RangeAnalysis and t.core.verify():
            summary = (
                finite_tail_summary
                if all(type(a) is FiniteTailBound for a in t.tails)
                else bounded_tail_summary
            )
            image = summary(f, x, D, t.core, t.tails)
        else:
            return False
        if image is None:
            return False
        expected = (image, image, image, sp.S.EmptySet)
    elif type(t) is TailImage:
        child = t.core
        if (
            type(child) is not RangeAnalysis
            or not child.verify()
            or child.expression != f
            or child.variable != x
            or type(t.tails) is not tuple
            or not all(
                type(a) is MonotoneTail
                and a.expression == f
                and a.variable == x
                and a.verify()
                for a in t.tails
            )
        ):
            return False
        regions = (child.domain_record.effective, *(a.domain for a in t.tails))
        if sp.Union(*regions) != D or any(
            sp.Intersection(a, b) is not sp.S.EmptySet
            for i, a in enumerate(regions)
            for b in regions[i + 1 :]
        ):
            return False
        image = (
            sp.Union(child.image, *(a.image for a in t.tails))
            if child.image is not None
            else None
        )
        expected = (
            image,
            sp.Union(child.inner, *(a.image for a in t.tails)),
            sp.Union(child.outer, *(a.image for a in t.tails)),
            child.unresolved,
        )
    else:
        return False
    return same_data(
        (result.image, result.inner, result.outer, result.unresolved), expected
    )
