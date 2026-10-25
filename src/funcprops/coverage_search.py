"""Proposers for source-bound coverage evidence; all proposals face the checker.

Adaptive fair subdivision and resumable search live in adaptive_roots.
"""

from dataclasses import replace

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .coverage_checker import (
    cell_expression,
    check_leaf,
    derivative_formula_on_cell,
    regular_on_cell,
)
from .coverage_contract import (
    CellDomainWitness,
    CoverageContext,
    CoverageLeaf,
    CoverageProof,
    InadmissibleProof,
    MonotoneWitness,
    NewtonWitness,
    RationalWitness,
    TaylorWitness,
)
from .domain_tracking import track_domain
from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness, grammar_obligations, preserve_replace
from .source_syntax import differentiate, normalize_arithmetic


def coverage_context(expr, var, domain, substitutions=(), *, policy=None):
    """Bind a real root query to exact source, domain and coordinate premises."""

    f, x = sp.sympify(expr), sp.sympify(var)
    if not isinstance(x, sp.Symbol) or not isinstance(domain, sp.Set):
        raise ValueError("coverage requires a scalar Symbol and an exact Set")
    pairs = tuple(
        sorted(
            ((sp.sympify(k), sp.sympify(v)) for k, v in dict(substitutions).items()),
            key=lambda kv: sp.default_sort_key(kv[0]),
        )
    )
    actual, requested = (preserve_replace(item, dict(pairs)) for item in (f, domain))
    from .infinite_roots import periodic_domain

    record = periodic_domain(actual, x, requested) or track_domain(actual, x, requested)
    if not record.complete and not grammar_obligations(actual, x):
        policy = EnclosurePolicy() if policy is None else policy
        cells = []
        parts = requested.args if isinstance(requested, sp.Union) else (requested,)
        parts = (
            [sp.FiniteSet(p) for part in parts for p in part]
            if all(isinstance(part, sp.FiniteSet) for part in parts)
            else parts
        )
        for part in parts:
            found = None
            for precision in policy.precisions:
                found = enclosure_witness(
                    actual, x, part, precision, policy.max_series_terms
                )
                if found is not None:
                    break
            if found is None:
                break
            cells.append(found)
        if len(cells) == len(parts):
            record = CellDomainWitness(actual, x, requested, tuple(cells))
    effective = record.effective if record.complete else requested
    return CoverageContext(
        f,
        x,
        domain,
        effective,
        record,
        sp.srepr(f),
        tuple(sorted(x.assumptions0.items())),
        sp.And(*(sp.Eq(k, v) for k, v in pairs)),
        pairs,
    )


def _accepted(context, region, theorem, count, mult, witness, roots=()):
    if count and context.expression.has(sp.Piecewise):
        mult = None
        roots = tuple((point, None) for point, _ in roots)
    leaf = CoverageLeaf(context, region, theorem, count, mult, witness, roots)
    return leaf if check_leaf(leaf).certified is True else None


def propose_leaf(context, region, *, method=None, policy=None, taylor_order=None):
    """Propose a particular theorem or try the declared finite-cell portfolio."""
    policy = EnclosurePolicy() if policy is None else policy
    if taylor_order is not None and (
        type(taylor_order) is not int
        or not 0 <= taylor_order <= policy.max_taylor_order
    ):
        raise ValueError("taylor_order must be within the query order budget")
    f, x = cell_expression(context, region), context.variable
    if f is None:
        return None
    if (
        method in (None, "rational-sturm")
        and not f.free_symbols - {x}
        and not f.has(sp.Float)
    ):
        try:
            from .root_coverage import _exact_rational_roots

            num, den = sp.fraction(sp.cancel(normalize_arithmetic(f)))
            n, d = sp.Poly(num, x, domain=sp.QQ), sp.Poly(den, x, domain=sp.QQ)
            data = _exact_rational_roots(normalize_arithmetic(f), x, region)
            if data is not None:
                count, mult, roots = data
                leaf = _accepted(
                    context,
                    region,
                    "rational-sturm",
                    count,
                    mult,
                    RationalWitness(tuple(n.all_coeffs()), tuple(d.all_coeffs())),
                    roots,
                )
                if leaf is not None:
                    return leaf
        except (
            TypeError,
            ValueError,
            NotImplementedError,
            sp.PolynomialError,
            CoercionFailed,
            DomainError,
        ):
            pass
    if isinstance(region, sp.FiniteSet) and len(region) == 1:
        if method in (None, "point-zero"):
            value = f.subs(x, next(iter(region)))
            if value.is_zero is True:
                leaf = _accepted(context, region, "point-zero", 1, None, value)
                if leaf is not None:
                    return leaf
    if grammar_obligations(f, x):
        return None
    compact = (
        isinstance(region, sp.Interval)
        and region.start.is_finite is True
        and region.end.is_finite is True
    )
    for precision in policy.precisions:

        def bound(g, support, precision=precision):
            return enclosure_witness(g, x, support, precision, policy.max_series_terms)

        if method in (None, "interval-exclusion", "point-exclusion"):
            ball = bound(f, region)
            if ball is not None and (ball.lower > 0 or ball.upper < 0):
                theorem = (
                    "point-exclusion"
                    if isinstance(region, sp.FiniteSet)
                    else "interval-exclusion"
                )
                leaf = _accepted(context, region, theorem, 0, 0, ball)
                if leaf is not None:
                    return leaf
        if not compact:
            continue
        closed = region.closure
        if method in (
            None,
            "monotone-crossing",
            "interval-newton",
        ) and regular_on_cell(
            f, x, closed, precision=precision, max_series_terms=policy.max_series_terms
        ):
            formula = derivative_formula_on_cell(
                f,
                x,
                closed,
                precision=precision,
                max_series_terms=policy.max_series_terms,
            )
            derivative = bound(formula, closed) if formula is not None else None
            if derivative is not None and not derivative.lower <= 0 <= derivative.upper:
                if method in (None, "monotone-crossing"):
                    a, b = (
                        bound(f, sp.FiniteSet(region.start)),
                        bound(f, sp.FiniteSet(region.end)),
                    )
                    if a is not None and b is not None:
                        witness = MonotoneWitness(derivative, a, b)
                        for count in (1, 0):
                            leaf = _accepted(
                                context,
                                region,
                                "monotone-crossing",
                                count,
                                count,
                                witness,
                            )
                            if leaf is not None:
                                return leaf
                if method in (None, "interval-newton"):
                    midpoint = (region.start + region.end) / 2
                    value = bound(f, sp.FiniteSet(midpoint))
                    if value is not None:
                        ratios = [
                            a / b
                            for a in (value.lower, value.upper)
                            for b in (derivative.lower, derivative.upper)
                        ]
                        witness = NewtonWitness(
                            midpoint,
                            derivative,
                            value,
                            midpoint - max(ratios),
                            midpoint - min(ratios),
                        )
                        for count in (1, 0):
                            leaf = _accepted(
                                context,
                                region,
                                "interval-newton",
                                count,
                                count,
                                witness,
                            )
                            if leaf is not None:
                                return leaf
        if method in (None, "taylor-exclusion"):
            for order in (
                (taylor_order,)
                if taylor_order is not None
                else range(policy.max_taylor_order + 1)
            ):
                if not regular_on_cell(
                    f,
                    x,
                    closed,
                    order + 1,
                    precision=precision,
                    max_series_terms=policy.max_series_terms,
                ):
                    continue
                center = (region.start + region.end) / 2
                coefficients = tuple(
                    differentiate(normalize_arithmetic(f), x, k).subs(x, center)
                    / sp.factorial(k)
                    for k in range(order + 1)
                )
                polynomial = sp.expand(
                    sum(c * (x - center) ** k for k, c in enumerate(coefficients))
                )
                derivative = bound(
                    differentiate(normalize_arithmetic(f), x, order + 1), closed
                )
                poly_bound = bound(polynomial, region)
                if derivative is None or poly_bound is None:
                    continue
                n = order + 1
                powers = [(region.start - center) ** n, (region.end - center) ** n]
                if n % 2 == 0:
                    powers.append(sp.S.Zero)
                products = [
                    a * b / sp.factorial(n)
                    for a in (derivative.lower, derivative.upper)
                    for b in (min(powers), max(powers))
                ]
                witness = TaylorWitness(
                    center,
                    order,
                    coefficients,
                    polynomial,
                    derivative,
                    poly_bound,
                    min(products),
                    max(products),
                )
                leaf = _accepted(context, region, "taylor-exclusion", 0, 0, witness)
                if leaf is not None:
                    return leaf
    return None


def _assemble(context, leaves, missing, exhaustion=None):
    unresolved = sp.Union(*missing)
    complete = unresolved is sp.S.EmptySet
    count = sum((a.root_count for a in leaves), sp.S.Zero) if complete else None
    ms = [a.multiplicity_count for a in leaves]
    mult = sum(ms, sp.S.Zero) if complete and all(a is not None for a in ms) else None
    return CoverageProof(
        context,
        tuple(leaves),
        unresolved,
        complete,
        count,
        mult,
        exhaustion if not complete else None,
    )


def prove_root_coverage(expr, var, domain=sp.S.Reals, *, policy=None, substitutions=()):
    """Build coverage evidence, preserving exact unresolved regions at every cap.

    Infinite nonrational regions, arbitrary parameter strata, selected complex
    sheets and unsupported primitives remain explicit obligations.
    """
    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "prove_root_coverage",
            expr,
            (var, domain),
            {"policy": replace(policy, seconds=None), "substitutions": substitutions},
            policy.seconds,
        )
    f, x = sp.sympify(expr), sp.sympify(var)
    if (
        not f.free_symbols
        and not f.has(sp.Float)
        and f.is_real is False
        and f.is_finite is True
    ):
        return InadmissibleProof(f, x, domain, sp.srepr(f))
    context = coverage_context(f, x, domain, substitutions, policy=policy)
    D = context.effective
    if not context.domain_record.complete:
        return CoverageProof(context, unresolved=D)
    if D is sp.S.EmptySet:
        return _assemble(context, [], [])
    from .coverage_cells import source_cells

    data = (
        source_cells(preserve_replace(f, dict(context.substitutions)), x, D)
        if f.has(sp.Piecewise)
        else None
    )
    if f.has(sp.Piecewise) and data is None:
        return CoverageProof(context, unresolved=D)
    parts = (
        [part for _, part in data]
        if data
        else list(D.args)
        if isinstance(D, sp.Union)
        else [D]
    )
    queue = [(part, 0) for part in reversed(parts)]
    leaves, missing, tested, exhaustion = [], [], 0, None
    while queue:
        region, depth = queue.pop()
        if tested >= policy.max_cells:
            missing.append(region)
            exhaustion = "cell-budget"
            continue
        tested += 1
        if isinstance(region, sp.FiniteSet) and len(region) > 1:
            queue.extend((sp.FiniteSet(p), depth) for p in region)
            continue
        leaf = propose_leaf(context, region, policy=policy)
        if leaf is not None:
            leaves.append(leaf)
        elif (
            isinstance(region, sp.Interval)
            and region.start.is_finite is True
            and region.end.is_finite is True
            and depth < policy.max_depth
        ):
            mid = (region.start + region.end) / 2
            queue.extend(
                (
                    (sp.Interval(mid, region.end, False, region.right_open), depth + 1),
                    (sp.Interval(region.start, mid, region.left_open, True), depth + 1),
                )
            )
        else:
            missing.append(region)
            # Unsupported grammar/domain is an obligation, not evidence that a
            # numerical precision limit was the cause of failure.
            g = cell_expression(context, region)
            if (
                g is not None
                and not grammar_obligations(g, x)
                and isinstance(region, sp.Interval)
                and region.start.is_finite
                and region.end.is_finite
            ):
                exhaustion = exhaustion or "depth-budget"
    return _assemble(context, leaves, missing, exhaustion)


def export_coverage_proof(certificate, *, policy=None):
    """Construct independent coverage witnesses from supported finite root records.

    Each region is re-proved and checked. Tails or families without a matching
    witness theorem remain unresolved; a provider status flag is insufficient.
    """
    context = coverage_context(
        certificate.expression,
        certificate.variable,
        certificate.domain_record.requested,
    )
    leaves, missing = [], [certificate.unresolved]
    methods = {
        "exact-rational": "rational-sturm",
        "interval-newton": "interval-newton",
        "taylor-exclusion": "taylor-exclusion",
        "point": None,
        "interval": None,
    }
    for old in certificate.regions:
        if old.method not in methods:
            missing.append(old.region)
            continue
        leaf = propose_leaf(
            context, old.region, method=methods[old.method], policy=policy
        )
        if leaf is None or leaf.root_count != old.root_count:
            missing.append(old.region)
        else:
            leaves.append(leaf)
    return _assemble(context, leaves, missing)
