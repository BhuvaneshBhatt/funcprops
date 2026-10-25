"""Bounded proposals for exhaustive tails and indexed real families."""

from dataclasses import replace

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .coverage_search import _accepted
from .enclosures import enclosure_witness
from .infinite_checker import (
    _AUX,
    _LEVEL,
    _index_data,
    exponential_groups,
    period,
    periodic_data,
    phases,
    pole_set,
)
from .infinite_contract import (
    CoveredRootFamily,
    ExponentialTailWitness,
    IndexRangeWitness,
    IntegerEndpointWitness,
    PeriodicDomainWitness,
    PeriodicRootWitness,
)


def periodic_domain(expr, var, requested):
    """Propose an exact source-domain witness for a rational trigonometric family."""

    try:
        data = periodic_data(expr, var)
        if data is None:
            return None
        kind, rate, phase, numerator, denominator, guards = data
        poly = sp.Poly(
            sp.prod(
                sp.Poly.from_list(list(c), _LEVEL, domain=sp.QQ).as_expr()
                for c in guards
            ),
            _LEVEL,
            domain=sp.QQ,
        )
        if poly.is_zero:
            return None
        poles = tuple(
            r
            for r, _ in poly.real_roots(multiple=False)
            if kind == "tan" or sp.Interval(-1, 1).contains(r) is sp.S.true
        )
        excluded = pole_set(kind, rate, phase, poles)
        record = PeriodicDomainWitness(
            expr,
            var,
            requested,
            sp.Complement(requested, excluded),
            excluded,
            kind,
            rate,
            phase,
            numerator,
            denominator,
            guards,
            poles,
        )
        return record if record.verify() else None
    except (
        ValueError,
        TypeError,
        NotImplementedError,
        sp.PolynomialError,
        CoercionFailed,
        DomainError,
    ):
        return None


def propose_tail(context, region, direction, threshold, policy):
    """Propose a rigorous exponential-polynomial tail-exclusion leaf."""

    from .coverage_checker import cell_expression

    f = cell_expression(context, region)
    if f is None:
        return None
    for sign in (1, -1):
        try:
            groups = exponential_groups(f, context.variable, direction, threshold, sign)
        except (
            ValueError,
            TypeError,
            NotImplementedError,
            sp.PolynomialError,
            CoercionFailed,
            DomainError,
        ):
            continue
        if groups is None:
            continue
        for precision in policy.precisions:
            bounds = tuple(
                tuple(
                    enclosure_witness(
                        c, _AUX, sp.FiniteSet(0), precision, policy.max_series_terms
                    )
                    for c in cs
                )
                for _, cs in groups
            )
            if any(b is None for cs in bounds for b in cs) or any(
                b.lower < 0 for b in bounds[-1]
            ):
                continue
            lower, remainder = bounds[-1][-1].lower, sp.S.Zero
            for (rate, cs), bs in zip(groups[:-1], bounds[:-1], strict=True):
                delta = groups[-1][0] - rate
                remainder += sum(
                    max(0, -b.lower)
                    * sp.factorial(len(cs) - 1 - k)
                    / delta ** (len(cs) - 1 - k)
                    for k, b in enumerate(bs)
                )
            if lower > remainder:
                leaf = _accepted(
                    context,
                    region,
                    "exponential-tail",
                    0,
                    0,
                    ExponentialTailWitness(
                        direction, threshold, sign, groups, bounds, lower, remainder
                    ),
                )
                if leaf is not None:
                    return leaf
    return None


def integer_endpoint(q, policy):
    """Propose an exact comparison between an indexed endpoint and a cutoff."""

    q = sp.cancel(q)
    value = sp.floor(q)
    if isinstance(value, sp.Integer):
        return IntegerEndpointWitness(q, int(value))
    for precision in policy.precisions:
        b = enclosure_witness(
            q, _AUX, sp.FiniteSet(0), precision, policy.max_series_terms
        )
        if b is not None and sp.floor(b.lower) == sp.floor(b.upper):
            return IntegerEndpointWitness(q, int(sp.floor(b.lower)), b)
    return None


def index_range(offset, step, d, policy):
    """Propose an owned index range for an exhaustive periodic family."""

    from .coverage_checker import _formula_equal

    left = right = None
    if isinstance(d, sp.FiniteSet) and len(d) == 1:
        q = sp.cancel((next(iter(d)) - offset) / step)
        left = integer_endpoint(q, policy)
        if left is None:
            return None
        if q == left.floor or _formula_equal(q, sp.Integer(left.floor)):
            low = high = left.floor
        else:
            if q.is_integer is not False:
                found = None
                for precision in policy.precisions:
                    b = enclosure_witness(
                        q, _AUX, sp.FiniteSet(0), precision, policy.max_series_terms
                    )
                    if (
                        b is not None
                        and b.lower > left.floor
                        and b.upper < left.floor + 1
                    ):
                        found = replace(left, enclosure=b)
                        break
                if found is None:
                    return None
                left = found
            low, high = 1, 0
    elif isinstance(d, sp.Interval):
        low, high = sp.S.NegativeInfinity, sp.oo
        if d.start is not sp.S.NegativeInfinity:
            q = (d.start - offset) / step
            left = integer_endpoint(q if d.left_open else -q, policy)
            if left is None:
                return None
            low = left.floor + 1 if d.left_open else -left.floor
        if d.end is not sp.oo:
            q = (d.end - offset) / step
            right = integer_endpoint(-q if d.right_open else q, policy)
            if right is None:
                return None
            high = -right.floor - 1 if d.right_open else right.floor
    else:
        return None
    w = IndexRangeWitness(d, low, high, left, right)
    return w if _index_data(offset, step, w) is not None else None


def propose_periodic(context, region, policy):
    """Propose an exhaustive root-family leaf for a supported periodic source."""

    record = context.domain_record
    if not isinstance(record, PeriodicDomainWitness) or region != record.effective:
        return None
    n = sp.Poly.from_list(list(record.numerator), _LEVEL, domain=sp.QQ)
    if n.is_zero:
        return _accepted(
            context,
            region,
            "periodic-rational",
            sp.oo,
            None,
            PeriodicRootWitness((), (), True),
        )
    values = tuple(
        (r, int(m))
        for r, m in n.real_roots(multiple=False)
        if record.kind == "tan" or sp.Interval(-1, 1).contains(r) is sp.S.true
    )
    guards = [sp.Poly.from_list(list(c), _LEVEL, domain=sp.QQ) for c in record.guards]
    parts = (
        record.requested.args
        if isinstance(record.requested, sp.Union)
        else (record.requested,)
    )
    parts = tuple(
        p
        for d in parts
        for p in ([sp.FiniteSet(a) for a in d] if isinstance(d, sp.FiniteSet) else [d])
    )
    families, count, mult = [], 0, 0
    from .coverage_checker import _root_at

    for level, m in values:
        if any(_root_at(g, level) for g in guards):
            continue
        m *= 2 if record.kind != "tan" and level in (-1, 1) else 1
        for theta in phases(record.kind, level):
            offset, step = (
                (theta - record.phase) / record.rate,
                period(record.kind, record.rate),
            )
            ranges = tuple(index_range(offset, step, d, policy) for d in parts)
            if any(w is None for w in ranges):
                return None
            family = CoveredRootFamily(offset, step, m, ranges)
            families.append(family)
            nroots = sum(_index_data(offset, step, r) for r in ranges)
            count += nroots
            mult += m * nroots
    return _accepted(
        context,
        region,
        "periodic-rational",
        count,
        mult,
        PeriodicRootWitness(values, tuple(families)),
    )


def split_infinite_task(context, task, policy, cell_budget):
    """Retain failed tails verbatim; certified tails expose a finite core."""
    from .adaptive_roots import CoverageTask, _parts

    region = task.region
    if (
        not isinstance(region, sp.Interval)
        or (region.start.is_finite and region.end.is_finite)
        or cell_budget <= 0
    ):
        return (), (), 0
    from .coverage_checker import cell_expression

    try:
        formula = cell_expression(context, region)
        if (
            formula is None
            or exponential_groups(formula, context.variable, 1, sp.S.One, 1) is None
        ):
            return (), (), 0
    except (
        ValueError,
        TypeError,
        NotImplementedError,
        sp.PolynomialError,
        CoercionFailed,
        DomainError,
    ):
        return (), (), 0
    leaves, tested, remaining = [], 0, region
    cuts = {-1: sp.S.One, 1: sp.S.One}
    for direction in (-1, 1):
        if (direction == -1 and region.start is not sp.S.NegativeInfinity) or (
            direction == 1 and region.end is not sp.oo
        ):
            continue
        for depth in range(policy.max_depth + 1):
            if tested >= cell_budget:
                break
            threshold = sp.Integer(2) ** depth
            tail = (
                sp.Interval(-sp.oo, -threshold)
                if direction == -1
                else sp.Interval(threshold, sp.oo)
            )
            owned = sp.Intersection(remaining, tail)
            if owned is sp.S.EmptySet:
                continue
            tested += 1
            cuts[direction] = threshold
            leaf = propose_tail(context, owned, direction, threshold, policy)
            if leaf is not None:
                leaves.append(leaf)
                remaining = sp.Complement(remaining, owned)
                break
    lower = -cuts[-1] if region.start is sp.S.NegativeInfinity else region.start
    upper = cuts[1] if region.end is sp.oo else region.end
    core = sp.Intersection(remaining, sp.Interval(lower, upper))
    if core is not sp.S.EmptySet:
        parts = (*_parts(core), *_parts(sp.Complement(remaining, core)))
    elif leaves:
        parts = _parts(remaining)
    else:
        parts = ()
    pending = tuple(CoverageTask(p, p, 0) for p in parts)
    return tuple(leaves), pending, tested


def infinite_root_coverage(
    expr, var, domain=sp.S.Reals, *, policy=None, substitutions=()
):
    """Adaptive core/tail or exhaustive periodic coverage for supported classes."""
    from .adaptive_roots import adaptive_root_coverage

    return adaptive_root_coverage(
        expr, var, domain, policy=policy, substitutions=substitutions
    )
