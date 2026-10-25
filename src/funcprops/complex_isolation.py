"""Native entire-function isolation, exact assembly and resumable fair search.

Counts use checked contour witnesses. Search decisions never enter replay, and
failed subdivisions never replace a counted parent in the frontier.
"""

from collections import deque
from dataclasses import dataclass, replace
from math import isqrt

import sympy as sp

from ._checkpoints import checkpoint_sink
from .analytic_contours import (
    AnalyticContourCertificate,
    ComplexBoxWitness,
    _header,
    certify_analytic_contour,
    check_analytic_contour,
)
from .complex_coverage import CoverageRectangle, _partition
from .complex_interval import complex_box_evaluate, entire_source
from .complex_multiplicity import (
    ComplexExactMultiplicity,
    ComplexLocatedRegion,
    ComplexPowerRootRegion,
    _propose_multiple,
)
from .complex_newton import (
    ComplexNewtonRegion,
    _layout,
    _propose_refinement,
    _valid_region,
)
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    RecursionError,
)


def _width(rectangle):
    a, b, c, d = rectangle.bounds()
    return max(c - a, d - b)


def _accurate(c, width, diameter=None):
    a, b, x, y = c.rectangle.bounds()
    return (width is None or max(x - a, y - b) <= width) and (
        diameter is None or (x - a) ** 2 + (y - b) ** 2 <= diameter**2
    )


def _summary(outer, zeros, roots, clusters, unresolved, width, diameter=None):
    coverage = outer is not None and not unresolved
    isolation = coverage and not clusters
    accuracy = isolation and all(_accurate(c, width, diameter) for c in roots)
    total = sum(c.zero_count for c in (*zeros, *roots, *clusters)) if coverage else None
    distinct = len(roots) if isolation else None
    obligations = tuple(
        text
        for test, text in (
            (outer is None, "unresolved-outer-boundary"),
            (bool(unresolved), "unresolved-regions"),
            (bool(clusters), "unseparated-clusters"),
            (any(not _accurate(c, width) for c in roots), "requested-box-width"),
            (
                any(not _accurate(c, None, diameter) for c in roots),
                "requested-box-diameter",
            ),
        )
        if test
    )
    return coverage, isolation, accuracy, total, distinct, obligations


def _individual(c):
    from .shared_zeros import SharedZeroOrderProof, SharedZeroRegion

    return c.zero_count == 1 or (
        type(c)
        in (
            ComplexExactMultiplicity,
            ComplexLocatedRegion,
            ComplexPowerRootRegion,
            SharedZeroOrderProof,
            SharedZeroRegion,
        )
        and c.known_distinct == 1
    )


@dataclass(frozen=True)
class ComplexIsolationProof:
    """Bind isolated roots, clusters and unresolved regions to an exact rectangle cover."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    source_syntax: str
    coordinate_assumptions: tuple
    outer: AnalyticContourCertificate | None = None
    zero_regions: tuple = ()
    root_regions: tuple = ()
    clusters: tuple = ()
    unresolved: tuple = ()
    max_box_width: sp.Rational | None = None
    coverage_complete: bool = False
    isolation_complete: bool = False
    accuracy_complete: bool = False
    multiplicity_count: int | None = None
    distinct_root_count: int | None = None
    obligations: tuple = ()
    exhaustion: str | None = None
    schema_version: int = 1
    max_box_diameter: sp.Rational | None = None

    @property
    def complete(self):
        return (
            self.coverage_complete
            and self.isolation_complete
            and self.accuracy_complete
        )

    @property
    def root_count(self):
        return self.distinct_root_count

    @property
    def total_count(self):
        return self.multiplicity_count

    @property
    def regions(self):
        return self.zero_regions + self.root_regions + self.clusters

    @property
    def isolating_boxes(self):
        return tuple(c.rectangle for c in self.root_regions)

    @property
    def refinements(self):
        found, seen = [], set()
        nodes = list(self.regions)
        stack = []
        while nodes:
            node = nodes.pop()
            if type(node) is ComplexNewtonRegion:
                stack.append(node.refinement)
            elif type(node) is ComplexPowerRootRegion:
                nodes.append(node.base_region)
        while stack:
            c = stack.pop()
            if id(c) not in seen:
                seen.add(id(c))
                found.append(c)
                if type(c.parent) is ComplexNewtonRegion:
                    stack.append(c.parent.refinement)
        return tuple(found)

    @property
    def real_root_count(self):
        return 0 if self.multiplicity_count == 0 else None

    @property
    def individual_multiplicities(self):
        return (
            tuple(c.zero_count for c in self.root_regions)
            if self.isolation_complete
            else None
        )

    @property
    def scope(self):
        return "native-entire-complex-root-isolation"

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_complex_isolation(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def _contour_shape(c, proof):
    # Concrete records prevent subclass callbacks from replacing the contour checker.
    return (
        type(c) is AnalyticContourCertificate
        and type(c.rectangle) is CoverageRectangle
        and c.expression == proof.expression
        and c.variable == proof.variable
        and c.complete
        and type(c.zero_count) is int
        and all(type(w) is ComplexBoxWitness for w in c.images)
    )


def check_complex_isolation(proof):
    """Check the stored complex isolation premises and report their replay outcome."""

    from .quotient_isolation import QuotientIsolationProof, check_quotient_isolation

    if type(proof) is QuotientIsolationProof:
        return check_quotient_isolation(proof)
    rejected = CheckResult(
        CheckOutcome.REJECTED, False, False, "false-complex-isolation-premise"
    )
    try:
        if (
            type(proof) is not ComplexIsolationProof
            or type(proof.schema_version) is not int
            or proof.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "unsupported-isolation-schema"
            )
        if not _header(proof) or type(proof.rectangle) is not CoverageRectangle:
            return rejected
        if not entire_source(proof.expression, proof.variable):
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED, None, False, "unsupported-entire-source"
                )
                if not proof.regions
                and not proof.complete
                and proof.multiplicity_count is None
                else rejected
            )
        if any(
            v is not None and (not isinstance(v, sp.Rational) or v <= 0)
            for v in (proof.max_box_width, proof.max_box_diameter)
        ):
            return rejected
        if (
            any(
                not isinstance(t, tuple)
                for t in (
                    proof.zero_regions,
                    proof.root_regions,
                    proof.clusters,
                    proof.unresolved,
                    proof.obligations,
                )
            )
            or any(
                type(t) is not bool
                for t in (
                    proof.coverage_complete,
                    proof.isolation_complete,
                    proof.accuracy_complete,
                )
            )
            or proof.exhaustion
            not in (None, "cell-budget", "depth-budget", "wall-budget")
            or (proof.complete and proof.exhaustion is not None)
            or any(
                n is not None and (type(n) is not int or n < 0)
                for n in (proof.multiplicity_count, proof.distinct_root_count)
            )
            or any(type(r) is not CoverageRectangle for r in proof.unresolved)
        ):
            return rejected
        for regions, kind in (
            (proof.zero_regions, 0),
            (proof.root_regions, 1),
            (proof.clusters, 2),
        ):
            if any(
                type(c)
                not in (
                    AnalyticContourCertificate,
                    ComplexNewtonRegion,
                    ComplexExactMultiplicity,
                    ComplexLocatedRegion,
                    ComplexPowerRootRegion,
                )
                or c.expression != proof.expression
                or c.variable != proof.variable
                or (
                    c.zero_count != 0
                    if kind == 0
                    else not _individual(c)
                    if kind == 1
                    else c.zero_count < 2 or _individual(c)
                )
                for c in regions
            ):
                return rejected
        if proof.outer is None:
            if proof.regions or proof.unresolved != (proof.rectangle,):
                return rejected
        elif (
            not _contour_shape(proof.outer, proof)
            or proof.outer.rectangle != proof.rectangle
            or check_analytic_contour(proof.outer).certified is not True
        ):
            return rejected
        summary = _summary(
            proof.outer,
            proof.zero_regions,
            proof.root_regions,
            proof.clusters,
            proof.unresolved,
            proof.max_box_width,
            proof.max_box_diameter,
        )
        if summary != (
            proof.coverage_complete,
            proof.isolation_complete,
            proof.accuracy_complete,
            proof.multiplicity_count,
            proof.distinct_root_count,
            proof.obligations,
        ):
            return rejected
        if not _partition(
            proof.rectangle,
            tuple(c.rectangle for c in proof.regions) + proof.unresolved,
        ):
            return rejected
        memo = {}
        if any(
            not _valid_region(c, proof.expression, proof.variable, memo)
            for c in proof.regions
        ):
            return rejected
        if (
            proof.coverage_complete
            and proof.multiplicity_count != proof.outer.zero_count
        ):
            return rejected
        return CheckResult(
            CheckOutcome.COMPLETE
            if proof.complete
            else CheckOutcome.EXHAUSTED
            if proof.exhaustion
            else CheckOutcome.LOCAL_VALID,
            True,
            proof.complete,
            proof.exhaustion or "; ".join(proof.obligations) or None,
        )
    except _ERRORS:
        return rejected


def _assembled(
    proof,
    *,
    outer=None,
    zeros=None,
    roots=None,
    clusters=None,
    unresolved=None,
    exhaustion=None,
):
    outer = proof.outer if outer is None else outer
    zeros = proof.zero_regions if zeros is None else tuple(zeros)
    roots = proof.root_regions if roots is None else tuple(roots)
    clusters = proof.clusters if clusters is None else tuple(clusters)
    unresolved = proof.unresolved if unresolved is None else tuple(unresolved)
    coverage, isolation, accuracy, total, distinct, obligations = _summary(
        outer,
        zeros,
        roots,
        clusters,
        unresolved,
        proof.max_box_width,
        proof.max_box_diameter,
    )
    return replace(
        proof,
        outer=outer,
        zero_regions=zeros,
        root_regions=roots,
        clusters=clusters,
        unresolved=unresolved,
        coverage_complete=coverage,
        isolation_complete=isolation,
        accuracy_complete=accuracy,
        multiplicity_count=total,
        distinct_root_count=distinct,
        obligations=obligations,
        exhaustion=None if coverage and isolation and accuracy else exhaustion,
    )


def _children(rectangle, axis, ratio):
    a, b, c, d = rectangle.bounds()
    if axis == 0:
        mid = a + ratio * (c - a)
        return CoverageRectangle(a + b * sp.I, mid + d * sp.I), CoverageRectangle(
            mid + b * sp.I, c + d * sp.I
        )
    mid = b + ratio * (d - b)
    return CoverageRectangle(a + b * sp.I, c + mid * sp.I), CoverageRectangle(
        a + mid * sp.I, c + d * sp.I
    )


def _split_choice(rectangle, attempt):
    # Van der Corput fractions are dense; restricting cuts to the central third
    # guarantees contraction. Always cut a longest side: accepting a shorter-axis
    # fallback repeatedly could otherwise leave the requested width unchanged.
    n = attempt + 1
    numerator, denominator = 0, 1
    while n:
        numerator = 2 * numerator + n % 2
        denominator *= 2
        n //= 2
    ratio = sp.Rational(1, 3) + sp.Rational(numerator, 3 * denominator)
    a, b, c, d = rectangle.bounds()
    long_axis = 0 if c - a >= d - b else 1
    return long_axis, ratio


@dataclass(frozen=True)
class ComplexIsolationTask:
    """Retain an owned subdivision region, path and retry effort."""

    rectangle: CoverageRectangle
    path: tuple = ()
    attempt: int = 0

    @property
    def depth(self):
        return len(self.path)


def _targets(proof):
    return (
        proof.unresolved
        + tuple(c.rectangle for c in proof.clusters)
        + tuple(
            c.rectangle
            for c in proof.root_regions
            if not _accurate(c, proof.max_box_width, proof.max_box_diameter)
        )
    )


@dataclass(frozen=True)
class ComplexIsolationState:
    """Preserve a complex proof and its exact pending frontier for resumption."""

    proof: ComplexIsolationProof
    pending: tuple = ()
    tested: int = 0
    generation: int = 0
    schema_version: int = 1

    @property
    def state(self):
        return self

    @property
    def expression(self):
        return self.proof.expression

    @property
    def variable(self):
        return self.proof.variable

    @property
    def scope(self):
        return "resumable-native-entire-complex-isolation"

    @property
    def complete(self):
        return self.proof.complete

    @property
    def coverage_complete(self):
        return self.proof.coverage_complete

    @property
    def isolation_complete(self):
        return self.proof.isolation_complete

    @property
    def accuracy_complete(self):
        return self.proof.accuracy_complete

    @property
    def multiplicity_count(self):
        return self.proof.multiplicity_count

    @property
    def total_count(self):
        return self.proof.total_count

    @property
    def distinct_root_count(self):
        return self.proof.distinct_root_count

    @property
    def root_count(self):
        return self.proof.root_count

    @property
    def unresolved(self):
        return self.proof.unresolved

    @property
    def isolating_boxes(self):
        return self.proof.isolating_boxes

    @property
    def clusters(self):
        return self.proof.clusters

    @property
    def refinements(self):
        return self.proof.refinements

    @property
    def exhaustion(self):
        return self.proof.exhaustion

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        rejected = CheckResult(
            CheckOutcome.REJECTED, False, False, "invalid-isolation-checkpoint"
        )
        try:
            if (
                type(self) is not ComplexIsolationState
                or type(self.schema_version) is not int
                or self.schema_version != 1
            ):
                return CheckResult(
                    CheckOutcome.UNSUPPORTED,
                    None,
                    False,
                    "unsupported-isolation-state-schema",
                )
            if (
                type(self.proof) is not ComplexIsolationProof
                or not isinstance(self.pending, tuple)
                or any(
                    type(n) is not int or n < 0 for n in (self.tested, self.generation)
                )
            ):
                return rejected
            rectangles = []
            for task in self.pending:
                if (
                    type(task) is not ComplexIsolationTask
                    or type(task.rectangle) is not CoverageRectangle
                    or not isinstance(task.path, tuple)
                    or type(task.attempt) is not int
                    or task.attempt < 0
                ):
                    return rejected
                rectangle = self.proof.rectangle
                for step in task.path:
                    if not isinstance(step, tuple) or len(step) != 3:
                        return rejected
                    axis, ratio, side = step
                    if (
                        type(axis) is not int
                        or axis not in (0, 1)
                        or type(side) is not int
                        or side not in (0, 1)
                        or not isinstance(ratio, sp.Rational)
                        or not 0 < ratio < 1
                    ):
                        return rejected
                    rectangle = _children(rectangle, axis, ratio)[side]
                if rectangle != task.rectangle or task.rectangle in rectangles:
                    return rejected
                rectangles.append(task.rectangle)
            if set(rectangles) != set(_targets(self.proof)):
                return rejected
            return self.proof.check()
        except _ERRORS:
            return rejected


def _seed(
    expr, var, lower_left, upper_right, max_box_width=None, max_box_diameter=None
):
    f, z, lo, hi = map(sp.sympify, (expr, var, lower_left, upper_right))
    width = None if max_box_width is None else sp.sympify(max_box_width)
    if width is not None and (not isinstance(width, sp.Rational) or width <= 0):
        raise ValueError("max_box_width must be a positive exact rational")
    diameter = None if max_box_diameter is None else sp.sympify(max_box_diameter)
    if diameter is not None and (
        not isinstance(diameter, sp.Rational) or diameter <= 0
    ):
        raise ValueError("max_box_diameter must be a positive exact rational")
    rectangle = CoverageRectangle(lo, hi)
    proof = ComplexIsolationProof(
        f,
        z,
        rectangle,
        sp.srepr(f),
        tuple(sorted(z.assumptions0.items())) if isinstance(z, sp.Symbol) else (),
        unresolved=(rectangle,),
        max_box_width=width,
        max_box_diameter=diameter,
    )
    proof = _assembled(proof)
    return ComplexIsolationState(proof, (ComplexIsolationTask(rectangle),))


def _wall_state(state):
    return replace(state, proof=_assembled(state.proof, exhaustion="wall-budget"))


def _needed(c, width, diameter=None):
    return c.zero_count > 0 and (
        not _individual(c) or not _accurate(c, width, diameter)
    )


def _dovetail(attempt):
    diagonal = (isqrt(8 * attempt + 1) - 1) // 2
    candidate = attempt - diagonal * (diagonal + 1) // 2
    return candidate, diagonal - candidate


def _run(
    state, policy, max_boundary_depth, use_newton=True, use_multiple=True, cofinal=False
):
    """Advance rectangle subdivision while preserving counts and every complement.

    A task changes ownership only after its child counts or contraction replay.
    Snapshots therefore remain valid even when the wall-budget worker stops."""

    if type(max_boundary_depth) is not int or max_boundary_depth < 0:
        raise ValueError("max_boundary_depth must be a nonnegative integer")
    if type(use_newton) is not bool:
        raise ValueError("use_newton must be a bool")
    if type(use_multiple) is not bool:
        raise ValueError("use_multiple must be a bool")
    proof = _assembled(state.proof)
    if (
        proof.complete
        or not _header(proof)
        or not entire_source(proof.expression, proof.variable)
    ):
        return replace(state, proof=proof)
    tasks, blocked = deque(state.pending), []
    zeros, roots, clusters, unresolved = map(
        list, (proof.zero_regions, proof.root_regions, proof.clusters, proof.unresolved)
    )
    outer, used = proof.outer, 0
    generation = state.generation + 1

    def snapshot(exhaustion=None):
        p = _assembled(
            proof,
            outer=outer,
            zeros=zeros,
            roots=roots,
            clusters=clusters,
            unresolved=unresolved,
            exhaustion=exhaustion,
        )
        return ComplexIsolationState(
            p, tuple(tasks) + tuple(blocked), state.tested + used, generation
        )

    def checkpoint():
        if (sink := checkpoint_sink()) is not None:
            sink(snapshot("wall-budget"))

    def count(rectangle, quota, expression=None, local_policy=None):
        nonlocal used
        c = certify_analytic_contour(
            proof.expression if expression is None else expression,
            proof.variable,
            rectangle.lower_left,
            rectangle.upper_right,
            policy=replace(
                policy if local_policy is None else local_policy,
                max_cells=min(quota, policy.max_cells - used),
                max_depth=boundary_limit,
                seconds=None,
            ),
        )
        used += c.tested
        return (
            c
            if c.complete
            and _valid_region(
                c,
                proof.expression if expression is None else expression,
                proof.variable,
                {},
            )
            and check_analytic_contour(c).certified is True
            else None
        )

    def insert(c):
        (zeros if c.zero_count == 0 else roots if _individual(c) else clusters).append(
            c
        )

    def child_path(task, child):
        a, b, c, d = task.rectangle.bounds()
        e, f, g, h = child.bounds()
        return (
            *task.path,
            (0, (e - a) / (c - a), 1),
            (0, (g - e) / (c - e), 0),
            (1, (f - b) / (d - b), 1),
            (1, (h - f) / (d - f), 0),
        )

    def commit(parent, children, task, paths):
        (roots if _individual(parent) else clusters).remove(parent)
        for c, path in zip(children, paths, strict=True):
            insert(c)
            if _needed(c, proof.max_box_width, proof.max_box_diameter):
                tasks.append(ComplexIsolationTask(c.rectangle, path))

    boundary_limit = max_boundary_depth
    checkpoint()
    while tasks and used < policy.max_cells:
        task = tasks.popleft()
        candidate, effort = (
            _dovetail(task.attempt) if cofinal else (task.attempt, task.attempt // 4)
        )
        quantum = 64 * (effort + 1) ** 2 if cofinal else 64 * (1 + task.attempt // 4)
        unresolved_task = task.rectangle in unresolved
        reserve = quantum if unresolved_task else 4 * quantum + 1
        if cofinal and policy.max_cells - used < reserve:
            tasks.appendleft(task)
            break
        quota = min(policy.max_cells - used, quantum)
        attempt_policy = (
            replace(policy, max_refinements=min(policy.max_refinements, effort))
            if cofinal
            else policy
        )
        boundary_limit = (
            min(max_boundary_depth, 14 + effort) if cofinal else max_boundary_depth
        )
        if unresolved_task:
            c = count(task.rectangle, quota, local_policy=attempt_policy)
            if c is None:
                tasks.append(replace(task, attempt=task.attempt + 1))
            else:
                unresolved.remove(task.rectangle)
                insert(c)
                if outer is None and task.rectangle == proof.rectangle:
                    outer = c
                if _needed(c, proof.max_box_width, proof.max_box_diameter):
                    tasks.append(replace(task, attempt=0))
            checkpoint()
            continue
        parent = next(c for c in (*roots, *clusters) if c.rectangle == task.rectangle)
        if use_multiple and not _individual(parent) and task.attempt % 4 == 0:
            multiple, spent = _propose_multiple(
                parent,
                replace(
                    attempt_policy,
                    max_cells=min(quota, policy.max_cells - used),
                    max_depth=boundary_limit,
                    seconds=None,
                ),
            )
            used += spent
            if multiple is not None:
                clusters.remove(parent)
                insert(multiple)
                if _needed(multiple, proof.max_box_width, proof.max_box_diameter):
                    tasks.append(replace(task, attempt=0))
                checkpoint()
                continue
            if used >= policy.max_cells:
                tasks.append(replace(task, attempt=task.attempt + 1))
                checkpoint()
                continue
        if task.depth >= policy.max_depth:
            blocked.append(task)
            continue
        if (
            type(parent) in (ComplexExactMultiplicity, ComplexLocatedRegion)
            and task.depth + 4 <= policy.max_depth
        ):
            used += 1
            a, b, c, d = task.rectangle.bounds()
            x, y = sp.re(parent.center), sp.im(parent.center)
            caps = [
                v / 4
                for v in (proof.max_box_width, proof.max_box_diameter)
                if v is not None
            ]
            hx = min((x - a) / 2, (c - x) / 2, (c - a) / 8, *caps)
            hy = min((y - b) / 2, (d - y) / 2, (d - b) / 8, *caps)
            child = CoverageRectangle(
                x - hx + sp.I * (y - hy), x + hx + sp.I * (y + hy)
            )
            children = tuple(
                ComplexLocatedRegion(parent, r) for r in _layout(task.rectangle, child)
            )
            if all(
                _valid_region(c, proof.expression, proof.variable, {}) for c in children
            ):
                commit(
                    parent,
                    children,
                    task,
                    (
                        child_path(task, child),
                        task.path,
                        task.path,
                        task.path,
                        task.path,
                    ),
                )
                checkpoint()
                continue
        if used >= policy.max_cells:
            tasks.append(replace(task, attempt=task.attempt + 1))
            checkpoint()
            continue
        base_parent = (
            parent.base_region if type(parent) is ComplexPowerRootRegion else parent
        )
        if (
            use_newton
            and base_parent.zero_count == 1
            and task.attempt % 4 == 0
            and task.depth + 4 <= policy.max_depth
        ):
            refinement, spent = _propose_refinement(
                base_parent,
                replace(
                    attempt_policy,
                    max_cells=min(quota, policy.max_cells - used),
                    seconds=None,
                ),
                proof.max_box_width,
                proof.max_box_diameter,
            )
            used += spent
            if refinement is not None:
                children = refinement.regions
                if type(parent) is ComplexPowerRootRegion:
                    children = tuple(
                        ComplexPowerRootRegion(parent.factorization, c)
                        for c in children
                    )
                commit(
                    parent,
                    children,
                    task,
                    (
                        child_path(task, refinement.child_rectangle),
                        task.path,
                        task.path,
                        task.path,
                        task.path,
                    ),
                )
                checkpoint()
                continue
            if used >= policy.max_cells:
                tasks.append(replace(task, attempt=task.attempt + 1))
                checkpoint()
                continue
        axis, ratio = _split_choice(task.rectangle, candidate)
        child_boxes = _children(task.rectangle, axis, ratio)
        children = []
        if type(parent) in (ComplexExactMultiplicity, ComplexLocatedRegion):
            used += 1
            children = [ComplexLocatedRegion(parent, box) for box in child_boxes]
            if any(
                not _valid_region(c, proof.expression, proof.variable, {})
                for c in children
            ):
                children = []
        else:
            a, b, c, d = task.rectangle.bounds()
            point = (
                a + ratio * (c - a) + sp.I * (b + d) / 2
                if axis == 0
                else (a + c) / 2 + sp.I * (b + ratio * (d - b))
            )
            count_source = (
                parent.factorization.base
                if type(parent) is ComplexPowerRootRegion
                else proof.expression
            )
            bounds = complex_box_evaluate(
                count_source,
                proof.variable,
                (sp.re(point), sp.im(point), sp.re(point), sp.im(point)),
                precision=attempt_policy.precision,
                max_series_terms=attempt_policy.max_series_terms,
            )
            used += 1
            if bounds != (0, 0, 0, 0):
                for box in child_boxes:
                    if used >= policy.max_cells:
                        break
                    c = count(
                        box,
                        min(quota, policy.max_cells - used),
                        expression=count_source,
                        local_policy=attempt_policy,
                    )
                    if c is None:
                        break
                    if type(parent) is ComplexPowerRootRegion:
                        c = ComplexPowerRootRegion(parent.factorization, c)
                    children.append(c)
        if (
            len(children) == 2
            and sum(c.zero_count for c in children) == parent.zero_count
        ):
            paths = tuple((*task.path, (axis, ratio, side)) for side in range(2))
            commit(parent, children, task, paths)
        else:
            tasks.append(replace(task, attempt=task.attempt + 1))
        checkpoint()
    return snapshot("cell-budget" if tasks else "depth-budget" if blocked else None)


def certify_complex_isolation(
    expr,
    var,
    lower_left,
    upper_right,
    *,
    max_box_width=None,
    max_box_diameter=None,
    policy=None,
    max_boundary_depth=14,
    use_newton=True,
    use_multiple=True,
):
    """Isolate supported entire/quotient zeros with exact coverage and bounded work."""
    from .quotient_isolation import (
        certify_quotient_isolation,
        quotient_source_supported,
    )

    if type(use_newton) is not bool:
        raise ValueError("use_newton must be a bool")
    if quotient_source_supported(expr, var):
        return certify_quotient_isolation(
            expr,
            var,
            lower_left,
            upper_right,
            max_box_width=max_box_width,
            max_box_diameter=max_box_diameter,
            policy=policy,
            max_boundary_depth=max_boundary_depth,
            use_multiple=use_multiple,
            use_newton=use_newton,
        )
    policy = EnclosurePolicy() if policy is None else policy
    seed = _seed(expr, var, lower_left, upper_right, max_box_width, max_box_diameter)
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_complex_isolation",
            expr,
            (var, lower_left, upper_right),
            {
                "max_box_width": max_box_width,
                "max_box_diameter": max_box_diameter,
                "max_boundary_depth": max_boundary_depth,
                "policy": replace(policy, seconds=None),
                "use_newton": use_newton,
                "use_multiple": use_multiple,
            },
            policy.seconds,
        )
    return _run(seed, policy, max_boundary_depth, use_newton, use_multiple)


def resume_complex_isolation(
    state, *, policy=None, max_boundary_depth=14, use_newton=True, use_multiple=True
):
    """Validate a source-bound checkpoint before continuing its exact frontier."""
    state = getattr(state, "state", state)
    from .quotient_isolation import QuotientIsolationState, resume_quotient_isolation

    if type(use_newton) is not bool:
        raise ValueError("use_newton must be a bool")
    if type(state) is QuotientIsolationState:
        return resume_quotient_isolation(
            state,
            policy=policy,
            max_boundary_depth=max_boundary_depth,
            use_multiple=use_multiple,
            use_newton=use_newton,
        )
    if type(state) is not ComplexIsolationState:
        raise TypeError(
            "expected a ComplexIsolationState or an isolation result with state"
        )
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "resume_complex_isolation",
            state,
            (),
            {
                "max_boundary_depth": max_boundary_depth,
                "policy": replace(policy, seconds=None),
                "use_newton": use_newton,
                "use_multiple": use_multiple,
            },
            policy.seconds,
        )
    if not state.verify():
        raise ValueError("invalid or unsupported complex isolation checkpoint")
    return _run(state, policy, max_boundary_depth, use_newton, use_multiple)
