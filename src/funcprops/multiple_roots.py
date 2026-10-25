"""Bounded proposals for explicit real multiplicity witnesses."""

import sympy as sp

from .coverage_checker import derivative_formula_on_cell
from .coverage_contract import PowerFactorWitness, TaylorDeflationWitness
from .coverage_search import _accepted, coverage_context, propose_leaf
from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness
from .source_syntax import differentiate, normalize_arithmetic


def _deflation(context, region, center, order, policy):
    from .coverage_checker import cell_expression

    if (
        not isinstance(center, sp.Expr)
        or center.has(sp.Float)
        or center.free_symbols
        or center.is_real is not True
        or center.is_finite is not True
    ):
        return None
    f, x = cell_expression(context, region), context.variable
    if f is None or context.expression.has(sp.Piecewise):
        return None
    support = region.closure if isinstance(region, sp.Interval) else region
    if support.contains(center) is not sp.S.true:
        return None
    jets = tuple(
        differentiate(normalize_arithmetic(f), x, k).subs(x, center)
        for k in range(order)
    )
    if any(a != 0 for a in jets):
        return None
    for precision in policy.precisions:
        derivative = derivative_formula_on_cell(
            f,
            x,
            support,
            order,
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        if derivative is None:
            continue
        bound = enclosure_witness(
            derivative, x, support, precision, policy.max_series_terms
        )
        if bound is None or bound.lower <= 0 <= bound.upper:
            continue
        count = int(region.contains(center) is sp.S.true)
        witness = TaylorDeflationWitness(
            center,
            order,
            jets,
            bound,
            bound.lower / sp.factorial(order),
            bound.upper / sp.factorial(order),
        )
        roots = ((center, order),) if count else ()
        leaf = _accepted(
            context,
            region,
            "taylor-deflation",
            count,
            order if count else 0,
            witness,
            roots,
        )
        if leaf is not None:
            return leaf
    return None


def deflate_real_root(expr, var, domain, center, order, *, policy=None):
    """Prove a finite-order zero by exact jets and a nonzero Taylor unit.

    Return a checked local leaf, or None when any premise remains unproved.
    A small derivative or a numerical zero is never an exact jet witness.
    """
    policy = EnclosurePolicy() if policy is None else policy
    if type(order) is not int or not 2 <= order <= policy.max_taylor_order + 1:
        raise ValueError("order must be between 2 and max_taylor_order + 1")
    if policy.seconds is not None:
        from dataclasses import replace

        from .work_budget import bounded_query

        return bounded_query(
            "deflate_real_root",
            expr,
            (var, domain, center, order),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    context = coverage_context(expr, var, domain, policy=policy)
    return _deflation(context, domain, sp.sympify(center), order, policy)


def propose_multiple_leaf(context, region, policy):
    """Propose a supported factor or Taylor-deflation multiplicity witness."""

    from .coverage_checker import cell_expression

    f, x = cell_expression(context, region), context.variable
    if (
        f is None
        or context.expression.has(sp.Piecewise)
        or not isinstance(region, sp.Interval)
        or not region.start.is_finite
        or not region.end.is_finite
    ):
        return None
    formula = normalize_arithmetic(f)
    try:
        factors = sp.Mul.make_args(sp.factor(formula))
        for factor in factors:
            base, exponent = factor.as_base_exp()
            if not exponent.is_Integer or exponent <= 0 or not base.has(x):
                continue
            exponent = int(exponent)
            # Exponent one also isolates a simple factor next to multiple roots.
            unit = sp.cancel(formula / base**exponent)
            if unit == formula or base == formula:
                continue
            base_context = coverage_context(base, x, region, policy=policy)
            proof = propose_leaf(base_context, region, policy=policy)
            if proof is None or proof.root_count not in (0, 1):
                continue
            for precision in policy.precisions:
                bound = enclosure_witness(
                    unit, x, region.closure, precision, policy.max_series_terms
                )
                if bound is None or bound.lower <= 0 <= bound.upper:
                    continue
                count = proof.root_count
                leaf = _accepted(
                    context,
                    region,
                    "power-factor",
                    count,
                    exponent if count else 0,
                    PowerFactorWitness(base, exponent, unit, proof, bound),
                )
                if leaf is not None:
                    return leaf
        for center in dict.fromkeys(
            (sp.S.Zero, (region.start + region.end) / 2, region.start, region.end)
        ):
            for order in range(2, policy.max_taylor_order + 2):
                leaf = _deflation(context, region, center, order, policy)
                if leaf is not None:
                    return leaf
    except (ValueError, TypeError, NotImplementedError, sp.PolynomialError):
        return None
    return None
