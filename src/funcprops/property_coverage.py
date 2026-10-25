"""Bounded proposals for finite-component range, extrema and sign partitions."""

import itertools
from dataclasses import replace

import sympy as sp

from .adaptive_roots import AdaptiveRootResult, CoverageState, adaptive_root_coverage
from .coverage_checker import _formula_equal
from .coverage_contract import CoverageProof
from .domain_tracking import track_domain
from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness
from .property_checker import (
    _AUX,
    _NAMES,
    candidates,
    cells_between,
    derive_conclusions,
    geometry,
    property_cells,
    value_at,
)
from .property_contract import PropertyConclusion, PropertyCoverageProof, PropertyPiece
from .root_coverage import RootCoverageCertificate


def _seed(expr, var, domain, reason=None):
    f, x = sp.sympify(expr), sp.sympify(var)
    record = track_domain(f, x, domain)
    cells = property_cells(f, x, record.effective) if record.complete else None
    pieces = tuple(
        PropertyPiece(g, D) for g, D in (cells or ()) if D is not sp.S.EmptySet
    )
    conclusions = tuple(
        PropertyConclusion(n, obligations=(reason or "unresolved-property-geometry",))
        for n in _NAMES
    )
    proof = PropertyCoverageProof(
        f,
        x,
        record.requested,
        record,
        sp.srepr(f),
        tuple(sorted(x.assumptions0.items())) if isinstance(x, sp.Symbol) else (),
        pieces,
        conclusions=conclusions,
        exhaustion=reason,
    )
    if record.complete and all(
        not isinstance(p.domain, sp.Interval)
        or (p.domain.start.is_finite is True and p.domain.end.is_finite is True)
        for p in pieces
    ):
        try:
            proof = replace(proof, conclusions=derive_conclusions(proof))
        except (
            AttributeError,
            TypeError,
            ValueError,
            ArithmeticError,
            NotImplementedError,
        ):
            pass
    return proof


def _root_points(coverage, f, x, interior):
    if not coverage.complete or (
        type(coverage.root_count) is not int
        and not isinstance(coverage.root_count, sp.Integer)
    ):
        return None
    if coverage.root_count == 0:
        return ()
    try:
        roots = sp.solveset(f, x, domain=interior)
        if not isinstance(roots, sp.FiniteSet) or len(roots) != coverage.root_count:
            return None
        roots = tuple(sorted(roots))
        if any(
            r.free_symbols
            or r.has(sp.Float)
            or r.is_real is not True
            or r.is_finite is not True
            or not _formula_equal(value_at(f, x, r), sp.S.Zero)
            for r in roots
        ):
            return None
        return roots
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        return None


def certify_property_coverage(
    expr, var, domain=sp.S.Reals, *, policy=None, critical_covers=(), zero_covers=()
):
    """Assemble exact property claims only from exhaustive checked geometry.

    Optional covers are keyed by source-cell order and must bind the exact branch
    derivative/source on its open interior. Unknown locations or ordering leave
    the affected property incomplete. Monotonicity returns a full partition of
    open monotone cells plus singleton seams, instead of a global ordering claim.
    """
    policy = EnclosurePolicy() if policy is None else policy
    for name, covers in (
        ("critical_covers", critical_covers),
        ("zero_covers", zero_covers),
    ):
        if type(covers) is not tuple or any(
            cover is not None
            and type(cover)
            not in (
                CoverageProof,
                RootCoverageCertificate,
                AdaptiveRootResult,
                CoverageState,
            )
            for cover in covers
        ):
            raise TypeError(
                f"{name} must be a tuple of supported root-coverage records"
            )
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_property_coverage",
            expr,
            (var, domain),
            {
                "policy": replace(policy, seconds=None),
                "critical_covers": critical_covers,
                "zero_covers": zero_covers,
            },
            policy.seconds,
        )
    proof = _seed(expr, var, domain)
    if (
        not proof.domain_record.complete
        or not isinstance(proof.variable, sp.Symbol)
        or proof.expression.free_symbols - {proof.variable}
        or proof.expression.has(sp.Float)
    ):
        return proof
    if (
        property_cells(proof.expression, proof.variable, proof.domain_record.effective)
        is None
    ):
        return proof
    if any(
        isinstance(p.domain, sp.Interval)
        and (p.domain.start.is_finite is not True or p.domain.end.is_finite is not True)
        for p in proof.pieces
    ):
        return proof
    if (
        not isinstance(critical_covers, tuple)
        or not isinstance(zero_covers, tuple)
        or (critical_covers and len(critical_covers) != len(proof.pieces))
        or (zero_covers and len(zero_covers) != len(proof.pieces))
    ):
        raise ValueError("supplied covers must be tuples in exact source-cell order")
    tested = 0

    def bound(f, x, D):
        nonlocal tested
        for precision in policy.precisions:
            if tested >= policy.max_cells:
                return None
            tested += 1
            b = enclosure_witness(f, x, D, precision, policy.max_series_terms)
            if b is not None and (b.lower > 0 or b.upper < 0):
                return b
        return None

    pieces = []
    for i, piece in enumerate(proof.pieces):
        f, D, x = piece.expression, piece.domain, proof.variable
        data = geometry(piece, x) if isinstance(D, sp.Interval) else None
        if data is not None:
            _, derivative, interior = data
            for iscritical, g, supplied in (
                (True, derivative, critical_covers),
                (False, f, zero_covers),
            ):
                coverage = supplied[i] if supplied else None
                if coverage is not None:
                    if hasattr(coverage, "proof"):
                        coverage = coverage.proof
                elif tested < policy.max_cells and not _formula_equal(g, sp.S.Zero):
                    result = adaptive_root_coverage(
                        g,
                        x,
                        interior,
                        policy=replace(policy, max_cells=policy.max_cells - tested),
                    )
                    tested += result.state.tested
                    coverage = result.proof
                points = (
                    _root_points(coverage, g, x, interior)
                    if coverage is not None
                    else None
                )
                samples = []
                if points is not None and not _formula_equal(g, sp.S.Zero):
                    for cell in cells_between(D, points):
                        b = bound(g, x, sp.FiniteSet((cell.start + cell.end) / 2))
                        if b is None:
                            samples = []
                            break
                        samples.append(b)
                if iscritical:
                    piece = replace(
                        piece,
                        critical_coverage=coverage,
                        critical_points=points,
                        derivative_samples=tuple(samples),
                    )
                else:
                    piece = replace(
                        piece,
                        zero_coverage=coverage,
                        zero_points=points,
                        sign_samples=tuple(samples),
                    )
        endpoints = (
            tuple(D)
            if isinstance(D, sp.FiniteSet)
            else tuple(
                p
                for p, opened in ((D.start, D.left_open), (D.end, D.right_open))
                if not opened
            )
        )
        endpoint_bounds = []
        for p in endpoints:
            value = value_at(f, x, p)
            if not _formula_equal(value, sp.S.Zero):
                b = bound(value, _AUX, sp.FiniteSet(0))
                if b is not None:
                    endpoint_bounds.append(b)
        piece = replace(piece, sign_samples=piece.sign_samples + tuple(endpoint_bounds))
        pieces.append(piece)
    proof = replace(proof, pieces=tuple(pieces))
    try:
        values = candidates(proof)
        if values is not None:
            order = tuple(
                sorted(
                    range(len(values)),
                    key=lambda i: values[i][2].evalf(policy.precision),
                )
            )
            comparisons = []
            for a, b in itertools.pairwise(order):
                if _formula_equal(values[a][2], values[b][2]):
                    comparisons.append(None)
                else:
                    witness = bound(values[a][2] - values[b][2], _AUX, sp.FiniteSet(0))
                    if witness is None or witness.upper >= 0:
                        order, comparisons = None, []
                        break
                    comparisons.append(witness)
            proof = replace(
                proof, candidate_order=order, comparisons=tuple(comparisons)
            )
        proof = replace(
            proof,
            tested=tested,
            exhaustion="cell-budget" if tested >= policy.max_cells else None,
        )
        return replace(proof, conclusions=derive_conclusions(proof))
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
        sp.PolynomialError,
    ) as exc:
        # Supplied evidence must not be silently discarded and replaced by a
        # different query. A bad caller-provided cover is a rejected premise.
        if critical_covers or zero_covers:
            raise ValueError("invalid supplied property coverage") from exc
        return proof
