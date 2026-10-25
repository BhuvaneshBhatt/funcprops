"""Replayable infimum/supremum brackets at implicit stationary points."""

from dataclasses import dataclass, replace

import sympy as sp

from .coverage_checker import _bound_matches, check_coverage, derivative_formula_on_cell
from .coverage_contract import (
    CheckOutcome,
    CheckResult,
    CoverageProof,
    EnclosureWitness,
)
from .domain_tracking import DomainRecord, track_domain
from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness
from .property_checker import property_cells
from .source_syntax import normalize_arithmetic, same_data

_ERRORS = (AttributeError, TypeError, ValueError, ArithmeticError, NotImplementedError)


@dataclass(frozen=True)
class ExtremumSite:
    """Bound a critical or endpoint value with source ownership information."""

    region: sp.Set
    kind: str
    enclosure: object


@dataclass(frozen=True)
class ExtremumPiece:
    """Record value bounds and critical coverage on one source component."""

    expression: sp.Expr
    domain: sp.Set
    critical_cover: object = None
    sites: tuple = ()


def _parts(region):
    if region is sp.S.EmptySet:
        return ()
    if isinstance(region, sp.Union):
        return tuple(p for r in region.args for p in _parts(r))
    return (region,)


def _sites(f, x, D, cover):
    if isinstance(D, sp.FiniteSet):
        if cover is not None:
            raise ValueError("point-cover-not-needed")
        return tuple(
            (sp.FiniteSet(p), "point") for p in sorted(D, key=sp.default_sort_key)
        )
    if not isinstance(D, sp.Interval) or not all(
        p.is_finite is True for p in (D.start, D.end)
    ):
        raise ValueError("finite-components-required")
    derivative = derivative_formula_on_cell(normalize_arithmetic(f), x, D.closure, 1)
    if derivative is None:
        raise ValueError("C1-closure-required")
    if derivative == 0:
        if cover is not None:
            raise ValueError("constant-cover-not-needed")
        return ((sp.FiniteSet((D.start + D.end) / 2), "constant"),)
    endpoints = ((sp.FiniteSet(D.start), "limit"), (sp.FiniteSet(D.end), "limit"))
    if cover is None:
        return (*endpoints, (D.closure, "unresolved"))
    interior = sp.Interval.open(D.start, D.end)
    if (
        type(cover) is not CoverageProof
        or cover.expression != derivative
        or cover.variable != x
        or cover.context.requested != interior
        or cover.context.effective != interior
        or cover.context.substitutions
        or cover.context.parameter_guard is not sp.S.true
        or cover.context.branch_context is not None
        or check_coverage(cover).certified is not True
    ):
        raise ValueError("critical-cover-mismatch")
    return (
        endpoints
        + tuple(
            (r.closure if isinstance(r, sp.Interval) else r, "critical")
            for leaf in cover.leaves
            if leaf.root_count != 0
            for r in (
                tuple(sp.FiniteSet(point) for point, _ in leaf.roots)
                if leaf.roots and len(leaf.roots) == leaf.root_count
                else _parts(leaf.region)
            )
        )
        + tuple(
            (r.closure if isinstance(r, sp.Interval) else r, "unresolved")
            for r in _parts(cover.unresolved)
        )
    )


def _bounds(pieces):
    sites = tuple(s for p in pieces for s in p.sites)
    if not sites:
        return None, None
    return (
        (min(s.enclosure.lower for s in sites), min(s.enclosure.upper for s in sites)),
        (max(s.enclosure.lower for s in sites), max(s.enclosure.upper for s in sites)),
    )


@dataclass(frozen=True)
class ExtremaBoundsProof:
    """Bind infimum/supremum brackets to component and critical-root evidence."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: sp.Set
    domain_record: DomainRecord
    tolerance: sp.Rational
    pieces: tuple = ()
    minimum_bounds: tuple | None = None
    maximum_bounds: tuple | None = None
    tested: int = 0
    reason: str | None = None
    schema_version: int = 1

    @property
    def source_syntax(self):
        return sp.srepr(self.expression)

    @property
    def coverage_complete(self):
        return bool(self.pieces) and all(p.sites for p in self.pieces)

    @property
    def critical_coverage_complete(self):
        return self.coverage_complete and all(
            s.kind != "unresolved" for p in self.pieces for s in p.sites
        )

    @property
    def accuracy_complete(self):
        return self.coverage_complete and all(
            b is not None and b[1] - b[0] <= self.tolerance
            for b in (self.minimum_bounds, self.maximum_bounds)
        )

    @property
    def exact_complete(self):
        return self.coverage_complete and all(
            b is not None and b[0] == b[1]
            for b in (self.minimum_bounds, self.maximum_bounds)
        )

    @property
    def complete(self):
        return bool(self.coverage_complete and self.accuracy_complete)

    @property
    def scope(self):
        return "finite-component-infimum-supremum-enclosures"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_extrema_bounds(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def certified(self):
        return self.verify()


def check_extrema_bounds(c):
    """Check the stored extrema bounds premises and report their replay outcome."""

    reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-extrema-bounds")
    try:
        if (
            type(c) is not ExtremaBoundsProof
            or type(c.schema_version) is not int
            or c.schema_version != 1
            or type(c.domain_record) is not DomainRecord
            or not isinstance(c.variable, sp.Symbol)
            or c.expression.free_symbols - {c.variable}
            or c.expression.has(sp.Float)
            or not isinstance(c.tolerance, sp.Rational)
            or c.tolerance <= 0
            or type(c.pieces) is not tuple
            or type(c.tested) is not int
            or c.tested < 0
        ):
            return reject
        r = c.domain_record
        if (
            r.expression != c.expression
            or r.variable != c.variable
            or r.requested != c.requested
        ):
            return reject
        if not r.complete:
            return (
                CheckResult(CheckOutcome.UNSUPPORTED, None, False, r.reason)
                if not c.pieces
                and c.minimum_bounds is None
                and c.maximum_bounds is None
                else reject
            )
        if not r.verify():
            return reject
        cells = property_cells(c.expression, c.variable, r.effective)
        if cells is None:
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED,
                    None,
                    False,
                    "unsupported-component-geometry",
                )
                if not c.pieces
                and c.minimum_bounds is None
                and c.maximum_bounds is None
                else reject
            )
        if (
            cells
            and not c.pieces
            and c.minimum_bounds is None
            and c.maximum_bounds is None
        ):
            return CheckResult(CheckOutcome.UNSUPPORTED, None, False, c.reason)
        if tuple((p.expression, p.domain) for p in c.pieces) != cells:
            return reject
        all_present = True
        for p in c.pieces:
            if type(p) is not ExtremumPiece or type(p.sites) is not tuple:
                return reject
            expected = _sites(p.expression, c.variable, p.domain, p.critical_cover)
            if not p.sites:
                all_present = False
                continue
            if len(p.sites) != len(expected):
                return reject
            for s, (D, kind) in zip(p.sites, expected, strict=True):
                if (
                    type(s) is not ExtremumSite
                    or s.region != D
                    or s.kind != kind
                    or type(s.enclosure) is not EnclosureWitness
                    or type(s.enclosure.grammar_version) is not int
                    or not _bound_matches(
                        s.enclosure, normalize_arithmetic(p.expression), c.variable, D
                    )
                ):
                    return reject
        actual = _bounds(c.pieces) if all_present else (None, None)
        if not same_data((c.minimum_bounds, c.maximum_bounds), actual):
            return reject
        return CheckResult(
            CheckOutcome.COMPLETE if c.complete else CheckOutcome.LOCAL_VALID,
            True,
            c.complete,
            c.reason,
        )
    except _ERRORS:
        return reject


def certify_extrema_bounds(
    expr,
    var,
    domain,
    *,
    tolerance=None,
    policy=None,
    critical_covers=(),
):
    """Bound infimum/supremum without requiring explicit stationary coordinates.

    Coverage may use enclosures of unresolved stationary regions. Accuracy is a
    separate, checked goal. Open endpoints contribute limits of C1 extensions,
    never a claim that the bounds or extrema are attained.
    """
    from .adaptive_roots import _contract, adaptive_root_coverage
    from .coverage_search import _assemble

    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_extrema_bounds",
            expr,
            (var, domain),
            {
                "tolerance": tolerance,
                "policy": replace(policy, seconds=None),
                "critical_covers": critical_covers,
            },
            policy.seconds,
        )
    f, x, tol = map(
        sp.sympify,
        (expr, var, sp.Rational(1, 10**6) if tolerance is None else tolerance),
    )
    if not isinstance(tol, sp.Rational) or tol <= 0:
        raise ValueError("tolerance must be an exact positive rational")
    record = track_domain(f, x, domain)
    c = ExtremaBoundsProof(f, x, domain, record, tol)
    if not record.complete:
        return replace(c, reason=record.reason)
    cells = property_cells(f, x, record.effective)
    if cells is None:
        return replace(c, reason="unsupported-component-geometry")
    if type(critical_covers) is not tuple or (
        critical_covers and len(critical_covers) != len(cells)
    ):
        raise ValueError("critical_covers must follow source-cell order")
    pieces, tested = [], 0
    for i, (g, D) in enumerate(cells):
        cover = critical_covers[i] if critical_covers else None
        if hasattr(cover, "proof"):
            cover = cover.proof
        try:
            _sites(g, x, D, cover)
            if isinstance(D, sp.Interval):
                d = derivative_formula_on_cell(normalize_arithmetic(g), x, D.closure, 1)
                if d != 0 and cover is None and tested < policy.max_cells:
                    result = adaptive_root_coverage(
                        d,
                        x,
                        sp.Interval.open(D.start, D.end),
                        policy=replace(policy, max_cells=policy.max_cells - tested),
                    )
                    cover = result.proof
                    tested += result.state.tested
            _sites(g, x, D, cover)
        except _ERRORS as error:
            if critical_covers:
                raise ValueError("invalid supplied critical cover") from error
            # Unsupported closure regularity is an honest unsupported result.
            return replace(c, reason=str(error))
        pieces.append(ExtremumPiece(g, D, cover))
    c = replace(c, pieces=tuple(pieces))
    for stage in range(policy.max_depth + 1):
        precision = policy.precisions[min(stage, len(policy.precisions) - 1)]
        updated = []
        for p in c.pieces:
            sites = []
            for D, kind in _sites(p.expression, x, p.domain, p.critical_cover):
                if tested >= policy.max_cells:
                    sites = []
                    break
                tested += 1
                w = enclosure_witness(
                    normalize_arithmetic(p.expression),
                    x,
                    D,
                    precision,
                    policy.max_series_terms,
                )
                if w is None:
                    sites = []
                    break
                sites.append(ExtremumSite(D, kind, w))
            # Preserve checked older bounds when refinement cannot finish.
            updated.append(replace(p, sites=tuple(sites)) if sites else p)
        c = replace(c, pieces=tuple(updated), tested=tested)
        if c.coverage_complete:
            c = replace(
                c,
                minimum_bounds=_bounds(c.pieces)[0],
                maximum_bounds=_bounds(c.pieces)[1],
            )
        if c.complete or tested >= policy.max_cells:
            break
        refined = []
        for p in c.pieces:
            cover = p.critical_cover
            if cover is not None and tested < policy.max_cells:
                leaves = []
                for leaf in cover.leaves:
                    if leaf.root_count == 1 and tested < policy.max_cells:
                        tested += 1
                        leaves.extend(
                            _contract(
                                leaf,
                                replace(
                                    policy,
                                    precision=precision,
                                    max_precision=max(precision, policy.max_precision),
                                ),
                            )
                        )
                    else:
                        leaves.append(leaf)
                # Existing unresolved cells remain explicitly enclosed.
                cover = _assemble(
                    cover.context, leaves, _parts(cover.unresolved), cover.exhaustion
                )
            refined.append(replace(p, critical_cover=cover, sites=()))
        if any(p.sites for p in c.pieces):
            previous = c
        c = replace(c, pieces=tuple(refined), minimum_bounds=None, maximum_bounds=None)
    if not c.coverage_complete and "previous" in locals():
        c = replace(previous, tested=tested)
    return replace(
        c,
        tested=tested,
        reason=None
        if c.complete
        else "empty-effective-domain"
        if not cells
        else "cell-budget"
        if tested >= policy.max_cells
        else "accuracy-or-enclosure-unresolved",
    )
