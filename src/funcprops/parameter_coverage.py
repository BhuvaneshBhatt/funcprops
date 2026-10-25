"""Exact algebraic strata and bounded uniform proofs on real parameter boxes."""

from collections import deque
from dataclasses import replace

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness
from .parameter_checker import (
    _sign_at,
    box_derivative,
    exponential_parameter_counts,
    exponential_parameter_data,
    monotone_parameter_counts,
    polynomial_events,
    polynomial_parameter_counts,
    translation_source_regular,
)
from .parameter_contract import (
    BoxEnclosureWitness,
    ExponentialParameterWitness,
    MonotoneParameterWitness,
    ParameterCoverageProof,
    ParameterRootCell,
    PolynomialParameterWitness,
    PolynomialSignWitness,
    SpecializedParameterProof,
    UniformParameterCertificate,
    UniformParameterCover,
    UniformParameterWitness,
    UniformZeroSubsetWitness,
)
from .source_syntax import normalize_arithmetic
from .transcendental.real_interval import certified_real_box_evaluate


def _parts(d):
    if d is sp.S.EmptySet:
        return ()
    if isinstance(d, sp.Union):
        return tuple(p for a in d.args for p in _parts(a))
    if isinstance(d, sp.FiniteSet):
        return tuple(sp.FiniteSet(a) for a in d)
    return (d,)


def _box_bound(f, domains, precision, terms):
    data = certified_real_box_evaluate(
        f, domains, precision=precision, max_series_terms=terms
    )
    return (
        BoxEnclosureWitness(f, domains, *data, precision, terms)
        if data is not None
        else None
    )


def _uniform_seed(expr, var, parameter_domains, domain, obligation):
    f, x = sp.sympify(expr), sp.sympify(var)
    pairs = tuple(
        sorted(
            ((sp.sympify(a), d) for a, d in dict(parameter_domains).items()),
            key=lambda kv: sp.default_sort_key(kv[0]),
        )
    )
    symbols = (x, *tuple(a for a, _ in pairs))
    assumptions = tuple((a, tuple(sorted(a.assumptions0.items()))) for a in symbols)
    return UniformParameterCertificate(
        f, x, domain, pairs, sp.srepr(f), assumptions, obligations=(obligation,)
    )


def _certify_parameter_cell(expr, var, parameter_domains, domain, *, policy=None):
    """Prove a uniform count on a finite box, or retain an explicit obligation.

    Any finite number of real parameters is supported. Every coefficient,
    derivative, endpoint and branch bound is valid on the entire box.
    """
    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_parameter_box",
            expr,
            (var, parameter_domains, domain),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    cert = _uniform_seed(
        expr,
        var,
        parameter_domains,
        domain,
        "uniform-domain-branch-or-root-separation-obligation",
    )
    if policy.max_cells == 0:
        return replace(cert, obligations=("cell-budget",))
    if (
        not isinstance(domain, sp.Interval)
        or not domain.start.is_finite
        or not domain.end.is_finite
    ):
        return cert
    f, x, pairs = cert.expression, cert.variable, cert.parameter_domains
    domains = ((x, domain.closure), *pairs)
    for precision in policy.precisions:
        value = _box_bound(f, domains, precision, policy.max_series_terms)
        if value is None:
            continue
        if value.lower > 0 or value.upper < 0:
            candidate = replace(
                cert,
                root_count=0,
                multiplicity_count=0,
                witness=UniformParameterWitness(value),
                obligations=(),
            )
            if candidate.verify():
                return candidate
        derivative = box_derivative(f, x, domains, precision, policy.max_series_terms)
        if derivative is None:
            continue
        d = _box_bound(derivative, domains, precision, policy.max_series_terms)
        if d is None or d.lower <= 0 <= d.upper:
            continue
        left = _box_bound(
            f,
            ((x, sp.FiniteSet(domain.start)), *pairs),
            precision,
            policy.max_series_terms,
        )
        right = _box_bound(
            f,
            ((x, sp.FiniteSet(domain.end)), *pairs),
            precision,
            policy.max_series_terms,
        )
        if left is None or right is None:
            continue
        for count in (1, 0):
            candidate = replace(
                cert,
                root_count=count,
                multiplicity_count=count,
                witness=UniformParameterWitness(value, d, left, right),
                obligations=(),
            )
            if candidate.verify():
                return candidate
    return cert


def certify_parameter_box(expr, var, parameter_domains, domain, *, policy=None):
    """Certify a full variable cover uniformly on a finite parameter box.

    Simple whole-box counts use one leaf. Otherwise disjoint owned variable
    cells and inflated root windows are assembled without losing complements.
    """
    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_parameter_box",
            expr,
            (var, parameter_domains, domain),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    first = _certify_parameter_cell(expr, var, parameter_domains, domain, policy=policy)
    if (
        first.complete
        or policy.max_cells <= 1
        or not isinstance(domain, sp.Interval)
        or not domain.start.is_finite
        or not domain.end.is_finite
    ):
        return first
    queue, deferred, leaves, tested, reason = deque([(domain, 0)]), [], [], 1, None
    skip_first = True
    while queue and tested < policy.max_cells:
        region, depth = queue.popleft()
        cert = (
            first
            if skip_first
            else _certify_parameter_cell(
                expr, var, parameter_domains, region, policy=policy
            )
        )
        if not skip_first:
            tested += 1
        skip_first = False
        if cert.complete and cert.verify():
            leaves.append(cert)
            continue
        found = False
        width = region.end - region.start
        for center in dict.fromkeys(
            ((region.start + region.end) / 2, region.start, region.end)
        ):
            if tested >= policy.max_cells:
                break
            window = sp.Intersection(
                domain, sp.Interval(center - width / 2, center + width / 2)
            )
            if (
                window == region
                or not isinstance(window, sp.Interval)
                or any(
                    a.root_count
                    and sp.Intersection(a.domain, window) is not sp.S.EmptySet
                    for a in leaves
                )
            ):
                continue
            tested += 1
            candidate = _certify_parameter_cell(
                expr, var, parameter_domains, window, policy=policy
            )
            if (
                not candidate.complete
                or candidate.root_count != 1
                or not candidate.verify()
            ):
                continue
            old_leaves = []
            for old in leaves:
                if sp.Intersection(old.domain, window) is sp.S.EmptySet:
                    old_leaves.append(old)
                else:
                    for part in _parts(sp.Complement(old.domain, window)):
                        sub = replace(
                            old, domain=part, witness=UniformZeroSubsetWitness(old)
                        )
                        if not sub.verify():
                            raise RuntimeError("failed uniform zero-complement replay")
                        old_leaves.append(sub)
            leaves = [*old_leaves, candidate]
            remaining = [(region, depth), *queue, *deferred]
            queue = deque(
                (p, d) for r, d in remaining for p in _parts(sp.Complement(r, window))
            )
            deferred, found = [], True
            break
        if found:
            continue
        if depth < policy.max_depth:
            mid = (region.start + region.end) / 2
            queue.extend(
                (
                    (sp.Interval(region.start, mid, region.left_open, True), depth + 1),
                    (sp.Interval(mid, region.end, False, region.right_open), depth + 1),
                )
            )
        else:
            deferred.append((region, depth))
            reason = reason or "depth-budget"
    if queue:
        reason = "cell-budget"
    unresolved = sp.Union(*(r for r, _ in (*queue, *deferred)))
    complete = unresolved is sp.S.EmptySet
    return UniformParameterCover(
        first.expression,
        first.variable,
        domain,
        first.parameter_domains,
        first.source_syntax,
        first.coordinate_assumptions,
        tuple(leaves),
        unresolved,
        complete,
        sum(a.root_count for a in leaves) if complete else None,
        sum(a.multiplicity_count for a in leaves) if complete else None,
        tested,
        reason if not complete else None,
    )


def _parameter_seed(expr, var, parameter, domain, parameter_domain):
    f, x, a = map(sp.sympify, (expr, var, parameter))
    if not isinstance(x, sp.Symbol) or not isinstance(a, sp.Symbol) or x == a:
        raise ValueError("variable and parameter must be distinct Symbols")
    return ParameterCoverageProof(
        f,
        x,
        a,
        domain,
        parameter_domain,
        sp.srepr(f),
        tuple((s, tuple(sorted(s.assumptions0.items()))) for s in (x, a)),
        unresolved=parameter_domain,
        complete=parameter_domain is sp.S.EmptySet,
    )


def _sample(region):
    if isinstance(region, sp.FiniteSet) and len(region) == 1:
        return next(iter(region))
    if isinstance(region, sp.Interval):
        if region.start is sp.S.NegativeInfinity:
            return sp.S.Zero if region.end is sp.oo else sp.floor(region.end) - 1
        if region.end is sp.oo:
            return sp.ceiling(region.start) + 1
        return (region.start + region.end) / 2
    return None


def _polynomial_cells(proof):
    if proof.domain != sp.S.Reals:
        return None
    events = polynomial_events(proof.expression, proof.variable, proof.parameter)
    if events is None or proof.domain != sp.S.Reals:
        return None
    critical = sp.Poly(
        sp.prod(p.as_expr() for p in events if not p.is_zero),
        proof.parameter,
        domain=sp.QQ,
    )
    roots = (
        tuple(r for r, _ in critical.real_roots(multiple=False))
        if critical.degree() > 0
        else ()
    )
    bands, previous = [], -sp.oo
    for root in roots:
        bands.extend((sp.Interval.open(previous, root), sp.FiniteSet(root)))
        previous = root
    bands.append(sp.Interval.open(previous, sp.oo))
    regions = [
        p
        for band in bands
        for p in _parts(sp.Intersection(proof.parameter_domain, band))
    ]
    result = []
    for region in regions:
        sample = _sample(region)
        signs = tuple(
            PolynomialSignWitness(
                tuple(p.all_coeffs()), sample, _sign_at(p.eval(sample))
            )
            for p in events
        )
        witness = PolynomialParameterWitness(signs)
        dummy = ParameterRootCell(region, "polynomial-parameter", 0, 0, witness)
        data = polynomial_parameter_counts(proof, dummy)
        result.append(
            replace(dummy, root_count=data[0], multiplicity_count=data[1])
            if data is not None
            else region
        )
    return result


def _monotone_cells(proof, policy):
    from .coverage_checker import derivative_formula_on_cell

    f, x, a, D = proof.expression, proof.variable, proof.parameter, proof.domain
    if not isinstance(D, sp.Interval) or not D.start.is_finite or not D.end.is_finite:
        return None
    base = normalize_arithmetic(f + a)
    if base.free_symbols - {x}:
        return None
    for precision in policy.precisions:
        if not translation_source_regular(
            f, x, a, D.closure, precision, policy.max_series_terms
        ):
            continue
        formula = derivative_formula_on_cell(
            base,
            x,
            D.closure,
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        if formula is None:
            continue
        d = enclosure_witness(formula, x, D.closure, precision, policy.max_series_terms)
        if d is None or d.lower <= 0 <= d.upper:
            continue
        left, right = base.subs(x, D.start), base.subs(x, D.end)
        if any(
            v.free_symbols
            or v.has(sp.Float)
            or v.is_real is not True
            or v.is_finite is not True
            for v in (left, right)
        ):
            continue
        low, high = (left, right) if d.lower > 0 else (right, left)
        w = MonotoneParameterWitness(base, d, left, right)
        bands = (
            sp.Interval.open(-sp.oo, low),
            sp.FiniteSet(low),
            sp.Interval.open(low, high),
            sp.FiniteSet(high),
            sp.Interval.open(high, sp.oo),
        )
        result = []
        for band in bands:
            for region in _parts(sp.Intersection(proof.parameter_domain, band)):
                cell = ParameterRootCell(region, "monotone-parameter", 0, 0, w)
                data = monotone_parameter_counts(proof, cell)
                result.append(
                    replace(cell, root_count=data[0], multiplicity_count=data[1])
                    if data is not None
                    else region
                )
        return result
    return None


def _exponential_cells(proof):
    if proof.domain != sp.S.Reals:
        return None
    data = exponential_parameter_data(proof.expression, proof.variable, proof.parameter)
    if data is None:
        return None
    w = ExponentialParameterWitness(*data)
    cells = []
    for band in (
        sp.Interval.open(-sp.oo, w.offset),
        sp.FiniteSet(w.offset),
        sp.Interval.open(w.offset, sp.oo),
    ):
        for region in _parts(sp.Intersection(proof.parameter_domain, band)):
            cell = ParameterRootCell(region, "exponential-parameter", 0, 0, w)
            count, mult = exponential_parameter_counts(proof, cell)
            cells.append(replace(cell, root_count=count, multiplicity_count=mult))
    return cells


def parameter_root_coverage(
    expr, var, parameter, domain=sp.S.Reals, *, parameter_domain=sp.S.Reals, policy=None
):
    """Cover exact one-parameter strata, retaining all exceptional/unproved cells.

    Full-space degree <=2 polynomials over QQ[parameter] and compact monotone
    translations have exact finite strata. Other finite parameter intervals use
    bounded uniform-box subdivision; collisions need not admit a finite proof.
    """
    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "parameter_root_coverage",
            expr,
            (var, parameter, domain),
            {
                "parameter_domain": parameter_domain,
                "policy": replace(policy, seconds=None),
            },
            policy.seconds,
        )
    proof = _parameter_seed(expr, var, parameter, domain, parameter_domain)
    if not isinstance(parameter_domain, sp.Set) or not isinstance(domain, sp.Set):
        raise ValueError("domain and parameter_domain must be exact Sets")
    if policy.max_cells == 0:
        return replace(proof, exhaustion="cell-budget" if not proof.complete else None)
    candidates = None
    try:
        candidates = _polynomial_cells(proof)
        if candidates is None:
            candidates = _exponential_cells(proof)
        if candidates is None:
            candidates = _monotone_cells(proof, policy)
    except (
        ValueError,
        TypeError,
        NotImplementedError,
        sp.PolynomialError,
        CoercionFailed,
        DomainError,
    ):
        candidates = None
    cells, missing, reason = [], [], None
    if candidates is not None:
        for i, item in enumerate(candidates):
            region = item.region if isinstance(item, ParameterRootCell) else item
            if i >= policy.max_cells or not isinstance(item, ParameterRootCell):
                missing.append(region)
                if i >= policy.max_cells:
                    reason = "cell-budget"
            else:
                cells.append(item)
    else:
        queue, tested = deque((p, 0) for p in _parts(parameter_domain)), 0
        while queue:
            region, depth = queue.popleft()
            if tested >= policy.max_cells:
                missing.append(region)
                reason = "cell-budget"
                continue
            cert = certify_parameter_box(
                expr,
                var,
                {proof.parameter: region.closure},
                domain,
                policy=replace(policy, max_cells=policy.max_cells - tested),
            )
            tested += cert.tested if isinstance(cert, UniformParameterCover) else 1
            if cert.complete and cert.verify():
                cells.append(
                    ParameterRootCell(
                        region,
                        "uniform-parameter-box",
                        cert.root_count,
                        cert.multiplicity_count,
                        cert,
                    )
                )
            elif (
                isinstance(region, sp.Interval)
                and region.start.is_finite
                and region.end.is_finite
                and depth < policy.max_depth
            ):
                mid = (region.start + region.end) / 2
                queue.extend(
                    (
                        (
                            sp.Interval(region.start, mid, region.left_open, True),
                            depth + 1,
                        ),
                        (
                            sp.Interval(mid, region.end, False, region.right_open),
                            depth + 1,
                        ),
                    )
                )
            else:
                missing.append(region)
                if (
                    isinstance(region, sp.Interval)
                    and region.start.is_finite
                    and region.end.is_finite
                ):
                    reason = reason or "depth-budget"
    unresolved = sp.Union(*missing)
    return replace(
        proof,
        cells=tuple(cells),
        unresolved=unresolved,
        complete=unresolved is sp.S.EmptySet,
        exhaustion=reason if unresolved is not sp.S.EmptySet else None,
    )


def specialize_parameter_coverage(proof, value):
    """Bind an exact value to a checked stratum; no fresh numerical search."""
    if not isinstance(proof, ParameterCoverageProof):
        raise TypeError("proof must be a ParameterCoverageProof")
    return SpecializedParameterProof(proof, sp.sympify(value))
