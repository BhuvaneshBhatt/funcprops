"""Resumable finite coverage, with owned cells and certified root localization.

Conditional termination applies to cofinal stages on compact C1 simple-root
problems with convergent interval forms; see docs/adaptive-coverage.md.
Every finite invocation may instead return an exact unresolved frontier.
"""

from collections import deque
from dataclasses import dataclass, replace

import sympy as sp

from ._checkpoints import checkpoint_sink
from .coverage_contract import (
    CheckOutcome,
    CheckResult,
    CoverageContext,
    LocatedSubsetWitness,
    NewtonWitness,
    SourceFormulaWitness,
    ZeroSubsetWitness,
)
from .coverage_search import _accepted, _assemble, coverage_context, propose_leaf
from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness, preserve_replace

# Set only inside an isolated budget worker. Checkpoints contain complete
# partitions, never an in-progress mutation of a partition.


def _parts(region):
    if region is sp.S.EmptySet:
        return ()
    if isinstance(region, sp.Union):
        return tuple(p for a in region.args for p in _parts(a))
    if isinstance(region, sp.FiniteSet):
        return tuple(sp.FiniteSet(p) for p in region)
    return (region,)


@dataclass(frozen=True)
class CoverageTask:
    """Retain an owned real region, source component and subdivision depth."""

    region: sp.Set
    support: sp.Set
    depth: int = 0


@dataclass(frozen=True)
class CoverageState:
    """Preserve disjoint accepted leaves and the exact pending real frontier."""

    context: CoverageContext
    leaves: tuple = ()
    pending: tuple = ()
    tested: int = 0
    generation: int = 0
    exhaustion: str | None = None
    schema_version: int = 1

    @property
    def expression(self):
        return self.context.expression

    @property
    def variable(self):
        return self.context.variable

    @property
    def proof(self):
        return _assemble(
            self.context, self.leaves, [a.region for a in self.pending], self.exhaustion
        )

    @property
    def complete(self):
        return self.proof.complete

    @property
    def scope(self):
        return "resumable-finite-real-root-coverage"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .coverage_checker import _empty, _subset

        try:
            if (
                type(self) is not CoverageState
                or type(self.schema_version) is not int
                or self.schema_version != 1
            ):
                return CheckResult(
                    CheckOutcome.UNSUPPORTED, None, False, "unsupported-state-version"
                )
            if (
                not isinstance(self.pending, tuple)
                or not isinstance(self.leaves, tuple)
                or any(
                    type(k) is not int or k < 0 for k in (self.tested, self.generation)
                )
            ):
                raise ValueError("invalid frontier metadata")
            owned = sp.S.EmptySet
            for task in self.pending:
                if (
                    type(task) is not CoverageTask
                    or type(task.depth) is not int
                    or task.depth < 0
                    or not isinstance(task.region, sp.Set)
                    or not isinstance(task.support, sp.Set)
                    or _empty(task.region)
                    or not _subset(task.region, task.support)
                    or not _subset(task.support, self.context.effective)
                    or not _empty(sp.Intersection(owned, task.region))
                ):
                    raise ValueError("invalid or overlapping frontier")
                owned = sp.Union(owned, task.region)
            checked = self.proof.check()
            if self.exhaustion == "wall-budget" and checked.certified is None:
                return CheckResult(
                    CheckOutcome.EXHAUSTED,
                    None,
                    False,
                    "wall-budget-before-domain-proof",
                )
            return checked
        except (AttributeError, TypeError, ValueError, NotImplementedError):
            return CheckResult(CheckOutcome.REJECTED, False, False, "invalid-frontier")

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class AdaptiveRootResult:
    """Expose a real coverage proof together with its resumable search state."""

    state: CoverageState
    schema_version: int = 1

    @property
    def proof(self):
        return self.state.proof

    @property
    def expression(self):
        return self.state.expression

    @property
    def variable(self):
        return self.state.variable

    @property
    def complete(self):
        return self.proof.complete

    @property
    def root_count(self):
        return self.proof.root_count

    @property
    def multiplicity_count(self):
        return self.proof.multiplicity_count

    @property
    def unresolved(self):
        return self.proof.unresolved

    @property
    def scope(self):
        return self.state.scope

    @property
    def obligations(self):
        return self.proof.obligations

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        if (
            type(self) is not AdaptiveRootResult
            or type(self.schema_version) is not int
            or self.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "unsupported-result-version"
            )
        if type(self.state) is not CoverageState:
            return CheckResult(CheckOutcome.REJECTED, False, False, "invalid-state")
        return self.state.check()

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def coverage_policy_stage(stage, *, base=None):
    """A cofinal sequence of finite effort caps, not an unconditional solver."""
    if type(stage) is not int or stage < 0:
        raise ValueError("stage must be a nonnegative integer")
    base = EnclosurePolicy() if base is None else base
    precision = base.precision * 2**stage
    return replace(
        base,
        precision=precision,
        max_precision=max(precision, base.max_precision * 2**stage),
        max_refinements=base.max_refinements + stage,
        max_depth=base.max_depth + stage,
        max_cells=max(1, base.max_cells) * 2**stage,
        max_taylor_order=base.max_taylor_order + stage,
        max_series_terms=max(1, base.max_series_terms) * 2**stage,
    )


def _initial(expr, var, domain, substitutions, policy):
    from .coverage_cells import source_cells
    from .infinite_contract import PeriodicDomainWitness

    context = coverage_context(expr, var, domain, substitutions, policy=policy)
    f = preserve_replace(context.expression, dict(context.substitutions))
    cells = (
        source_cells(f, context.variable, context.effective)
        if context.domain_record.complete
        else None
    )
    parts = (
        [p for _, d in cells for p in _parts(d)]
        if cells is not None
        else _parts(context.effective)
    )
    if isinstance(context.domain_record, PeriodicDomainWitness):
        parts = () if context.effective is sp.S.EmptySet else (context.effective,)
    return CoverageState(context, pending=tuple(CoverageTask(p, p) for p in parts))


def _locator(parent, policy):
    from .coverage_checker import derivative_formula_on_cell
    from .multiple_root_checker import location_base, newton_locus

    if parent.root_count != 1 or not isinstance(parent.region, sp.Interval):
        return None
    if len(parent.roots) == 1:
        return sp.FiniteSet(parent.roots[0][0])
    f, x, support = location_base(parent), parent.variable, parent.region
    for precision in policy.precisions:
        d = derivative_formula_on_cell(
            f,
            x,
            support.closure,
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        if d is None:
            continue
        derivative = enclosure_witness(
            d, x, support.closure, precision, policy.max_series_terms
        )
        mid = (support.start + support.end) / 2
        value = enclosure_witness(
            f, x, sp.FiniteSet(mid), precision, policy.max_series_terms
        )
        if (
            derivative is None
            or value is None
            or derivative.lower <= 0 <= derivative.upper
        ):
            continue
        ratios = [
            a / b
            for a in (value.lower, value.upper)
            for b in (derivative.lower, derivative.upper)
        ]
        w = NewtonWitness(mid, derivative, value, mid - max(ratios), mid - min(ratios))
        if newton_locus(f, x, support, w) is not None:
            return w
    return None


def _contract(parent, policy):
    from .multiple_root_checker import location_base, newton_locus

    locator = _locator(parent, policy)
    if locator is None:
        return (parent,)
    locus = (
        locator
        if isinstance(locator, sp.FiniteSet)
        else newton_locus(
            location_base(parent), parent.variable, parent.region, locator
        )
    )
    if locus is None or locus is sp.S.EmptySet:
        return (parent,)
    a, b = locus.inf, locus.sup
    pad = (parent.region.end - parent.region.start) / 32
    small = sp.Intersection(parent.region, sp.Interval(a - pad, b + pad))
    if small == parent.region or not isinstance(small, sp.Interval):
        return (parent,)
    pieces = []
    for region in (*_parts(sp.Complement(parent.region, small)), small):
        count = int(region == small)
        leaf = _accepted(
            parent.context,
            region,
            "located-subset",
            count,
            parent.multiplicity_count if count else 0,
            LocatedSubsetWitness(parent, locator),
        )
        if leaf is None:
            return (parent,)
        pieces.append(leaf)
    return tuple(pieces)


def _proposal(context, region, policy):
    from .coverage_checker import cell_expression, regular_on_cell
    from .infinite_roots import propose_periodic
    from .multiple_roots import propose_multiple_leaf
    from .source_syntax import normalize_arithmetic

    leaf = propose_periodic(context, region, policy)
    if leaf is not None:
        return leaf
    leaf = propose_leaf(context, region, policy=policy)
    if leaf is not None:
        return leaf
    f = cell_expression(context, region)
    if f is not None and normalize_arithmetic(f) != f:
        formula = normalize_arithmetic(f)
        c = coverage_context(formula, context.variable, region, policy=policy)
        proof = (
            propose_periodic(c, region, policy)
            or propose_leaf(c, region, policy=policy)
            or propose_multiple_leaf(c, region, policy)
        )
        if proof is not None:
            mult = proof.multiplicity_count
            support = region.closure if isinstance(region, sp.Interval) else region
            if proof.root_count and (
                type(mult) is not int
                or not regular_on_cell(f, context.variable, support, mult)
            ):
                mult = None
            leaf = _accepted(
                context,
                region,
                "source-formula",
                proof.root_count,
                mult,
                SourceFormulaWitness(proof),
            )
            if leaf is not None:
                return leaf
    return propose_multiple_leaf(context, region, policy)


def _run(state, policy):
    """Advance breadth-first real coverage with disjoint owned regions.

    Accepted windows are removed from every affected pending cell. Checkpoints
    retain all complements before exposing the updated proof frontier."""

    queue, deferred, leaves = deque(state.pending), [], list(state.leaves)
    tested, reason = 0, None

    def snapshot(exhaustion=None):
        return CoverageState(
            state.context,
            tuple(leaves),
            tuple(queue) + tuple(deferred),
            state.tested + tested,
            state.generation + 1,
            exhaustion,
        )

    def checkpoint():
        if (sink := checkpoint_sink()) is not None:
            sink(snapshot("wall-budget"))

    checkpoint()
    if not state.context.domain_record.complete:
        return AdaptiveRootResult(snapshot())
    while queue and tested < policy.max_cells:
        task = queue.popleft()
        tested += 1
        leaf = _proposal(state.context, task.region, policy)
        if leaf is not None:
            leaves.extend(_contract(leaf, policy))
            checkpoint()
            continue
        # An inflated cell straddles a pending seam. Its certificate is checked
        # on the whole cell; all intersecting complements are then retained.
        found = False
        region = task.region
        compact = (
            isinstance(region, sp.Interval)
            and region.start.is_finite
            and region.end.is_finite
        )
        if compact:
            width = region.end - region.start
            for center in dict.fromkeys(
                ((region.start + region.end) / 2, region.start, region.end)
            ):
                if tested >= policy.max_cells:
                    break
                window = sp.Intersection(
                    task.support, sp.Interval(center - width / 2, center + width / 2)
                )
                if window == region or not isinstance(window, sp.Interval):
                    continue
                if any(
                    a.root_count
                    and sp.Intersection(a.region, window) is not sp.S.EmptySet
                    for a in leaves
                ):
                    continue
                tested += 1
                candidate = _proposal(state.context, window, policy)
                if candidate is None or candidate.root_count != 1:
                    continue
                new_leaves = []
                for old in leaves:
                    if sp.Intersection(old.region, window) is sp.S.EmptySet:
                        new_leaves.append(old)
                    else:
                        for part in _parts(sp.Complement(old.region, window)):
                            smaller = _accepted(
                                state.context,
                                part,
                                "zero-subset",
                                0,
                                0,
                                ZeroSubsetWitness(old),
                            )
                            if smaller is None:
                                raise RuntimeError("failed zero-complement replay")
                            new_leaves.append(smaller)
                leaves = new_leaves + list(_contract(candidate, policy))
                remaining = [task, *queue, *deferred]
                queue = deque(
                    CoverageTask(p, t.support, t.depth)
                    for t in remaining
                    for p in _parts(sp.Complement(t.region, window))
                )
                deferred = []
                found = True
                checkpoint()
                break
        if found:
            continue
        if tested >= policy.max_cells:
            reason = "cell-budget"
        if not compact:
            from .infinite_roots import split_infinite_task

            tail_leaves, pending, cost = split_infinite_task(
                state.context, task, policy, policy.max_cells - tested
            )
            tested += cost
            if cost and tested >= policy.max_cells:
                reason = "cell-budget"
            elif cost and not tail_leaves:
                reason = reason or "depth-budget"
            if tail_leaves or pending:
                leaves.extend(tail_leaves)
                queue.extend(pending)
                checkpoint()
                continue
        if compact and task.depth < policy.max_depth:
            mid = (region.start + region.end) / 2
            queue.extend(
                (
                    CoverageTask(
                        sp.Interval(region.start, mid, region.left_open, True),
                        task.support,
                        task.depth + 1,
                    ),
                    CoverageTask(
                        sp.Interval(mid, region.end, False, region.right_open),
                        task.support,
                        task.depth + 1,
                    ),
                )
            )
        else:
            deferred.append(task)
            if compact:
                reason = "depth-budget"
        if tested % 8 == 0:
            checkpoint()
    if queue:
        reason = "cell-budget"
    return AdaptiveRootResult(snapshot(reason))


def adaptive_root_coverage(expr, var, domain, *, policy=None, substitutions=()):
    """Certify a finite cover or return a resumable exact unresolved frontier."""
    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "adaptive_root_coverage",
            expr,
            (var, domain),
            {"policy": replace(policy, seconds=None), "substitutions": substitutions},
            policy.seconds,
        )
    return _run(_initial(expr, var, domain, substitutions, policy), policy)


def resume_root_coverage(state, *, policy=None):
    """Resume the same partition; already certified leaves are retained."""
    state = state.state if isinstance(state, AdaptiveRootResult) else state
    policy = EnclosurePolicy() if policy is None else policy
    if type(state) is not CoverageState:
        raise TypeError("state must be a CoverageState or AdaptiveRootResult")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "resume_root_coverage",
            state,
            (),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    checked = state.check()
    if checked.certified is False:
        raise ValueError("rejected coverage state")
    if checked.certified is None and checked.reason not in (
        "unresolved-definition-domain",
        "wall-budget-before-domain-proof",
    ):
        raise ValueError(
            "unsupported coverage premises must be resolved before resumption"
        )
    if not state.context.domain_record.complete:
        fresh = _initial(
            state.expression,
            state.variable,
            state.context.requested,
            state.context.substitutions,
            policy,
        )
        return _run(fresh, policy)
    return _run(state, policy)


def _wall_result(state):
    return AdaptiveRootResult(
        replace(state, exhaustion="wall-budget" if state.pending else None)
    )


def _timeout_seed(expr, var, domain, substitutions=()):
    """Cheap query-preserving seed when the worker stops before domain tracking."""
    from .domain_tracking import DomainRecord

    f, x = sp.sympify(expr), sp.sympify(var)
    pairs = tuple(
        sorted(dict(substitutions).items(), key=lambda kv: sp.default_sort_key(kv[0]))
    )
    actual = preserve_replace(f, dict(pairs))
    requested = preserve_replace(domain, dict(pairs))
    record = DomainRecord(
        actual,
        x,
        requested,
        None,
        None,
        False,
        reason="wall-budget-before-domain-proof",
        natural_complete=False,
    )
    context = CoverageContext(
        f,
        x,
        domain,
        requested,
        record,
        sp.srepr(f),
        tuple(sorted(x.assumptions0.items())),
        sp.And(*(sp.Eq(k, v) for k, v in pairs)),
        pairs,
    )
    return CoverageState(
        context, pending=tuple(CoverageTask(p, p) for p in _parts(requested))
    )
