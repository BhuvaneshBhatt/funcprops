"""Finite cofinal isolation stages and an explicit conditional termination contract.

No finite stage or conditional theorem changes unresolved regions into roots or
exclusions. Completion comes only from the native assembly checker.
"""

from dataclasses import dataclass, field, replace

from . import complex_isolation as isolation
from ._checkpoints import capture_checkpoints, checkpoint_sink, emit_checkpoint
from .complex_isolation import ComplexIsolationState
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy

_PROTOCOL = "dovetail-prefix-precision"


def complex_isolation_policy_stage(stage, *, base=None):
    """Grow all caps while retaining every earlier precision in the portfolio."""
    if type(stage) is not int or stage < 0:
        raise ValueError("stage must be a nonnegative integer")
    base = EnclosurePolicy() if base is None else base
    if type(base) is not EnclosurePolicy:
        raise TypeError("base must be an EnclosurePolicy")
    return replace(
        base,
        precision=base.precision,
        max_precision=base.max_precision * 2**stage,
        max_refinements=base.max_refinements + stage,
        max_depth=base.max_depth + stage,
        max_cells=max(1, base.max_cells) * 2**stage,
        max_series_terms=max(1, base.max_series_terms) * 2**stage,
        max_taylor_order=base.max_taylor_order + stage,
        seconds=None,
    )


@dataclass(frozen=True)
class ComplexIsolationRun:
    """Retain the frontier, policy and fair-search index of a complex isolation run."""

    state: ComplexIsolationState
    base_policy: EnclosurePolicy = field(default_factory=EnclosurePolicy)
    next_stage: int = 0
    max_boundary_depth: int = 14
    use_newton: bool = True
    use_multiple: bool = True
    protocol: str = _PROTOCOL
    schema_version: int = 1

    @property
    def expression(self):
        """Expression to which the stored evidence applies."""
        return self.state.expression

    @property
    def variable(self):
        """Coordinate used by the source and its evidence."""
        return self.state.variable

    @property
    def proof(self):
        """Coverage evidence retained by the result."""
        return self.state.proof

    @property
    def complete(self):
        """Completion status for this record's stated scope; replay validity is separate."""
        return self.state.complete

    @property
    def coverage_complete(self):
        """Whether the evidence covers the entire requested region."""
        return self.state.coverage_complete

    @property
    def isolation_complete(self):
        """Whether every covered root is individually isolated."""
        return self.state.isolation_complete

    @property
    def accuracy_complete(self):
        """Whether the requested enclosure accuracy has been reached."""
        return self.state.accuracy_complete

    @property
    def root_count(self):
        """Distinct-root count supplied by the record, or None when unresolved."""
        return self.state.root_count

    @property
    def distinct_root_count(self):
        """Distinct-root count supplied by the record, or None when unresolved."""
        return self.root_count

    @property
    def individual_multiplicities(self):
        """Per-root multiplicities when individually established."""
        return self.proof.individual_multiplicities

    @property
    def refinements(self):
        """Refinement records retained by the search or proof."""
        return self.proof.refinements

    @property
    def unresolved(self):
        """Requested regions whose proof obligations remain open."""
        return self.proof.unresolved

    @property
    def clusters(self):
        """Covered root clusters that have not been separated individually."""
        return self.proof.clusters

    @property
    def multiplicity_count(self):
        """Root count with multiplicity, or None when unresolved."""
        return self.state.multiplicity_count

    @property
    def total_count(self):
        """Total count established by the coverage evidence."""
        return self.multiplicity_count

    @property
    def tested(self):
        """Number of candidate cells or attempts examined."""
        return self.state.tested

    @property
    def termination_contract(self):
        """Conditional completion theorem attached to the search."""
        return ComplexIsolationGuarantee(self)

    @property
    def scope(self):
        """Scope identifier: ``cofinal-staged-native_complex_isolation``."""
        return "cofinal-staged-native_complex_isolation"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        reject = CheckResult(
            CheckOutcome.REJECTED, False, False, "invalid-cofinal-isolation-run"
        )
        try:
            if (
                type(self) is not ComplexIsolationRun
                or type(self.schema_version) is not int
                or self.schema_version != 1
            ):
                return CheckResult(
                    CheckOutcome.UNSUPPORTED,
                    None,
                    False,
                    "unsupported-cofinal-isolation-schema",
                )
            if (
                type(self.state) is not ComplexIsolationState
                or type(self.base_policy) is not EnclosurePolicy
                or self.base_policy.seconds is not None
                or EnclosurePolicy(**vars(self.base_policy)) != self.base_policy
                or any(
                    type(n) is not int or n < 0
                    for n in (self.next_stage, self.max_boundary_depth)
                )
                or any(
                    type(v) is not bool for v in (self.use_newton, self.use_multiple)
                )
                or self.protocol != _PROTOCOL
            ):
                return reject
            return self.state.check()
        except isolation._ERRORS:
            return reject

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class ComplexIsolationGuarantee:
    """State the checked hypotheses for conditional simple-root completion."""

    run: ComplexIsolationRun
    theorem: str = "compact-simple-entire-cofinal"
    schema_version: int = 1

    @property
    def expression(self):
        """Expression to which the stored evidence applies."""
        return self.run.expression

    @property
    def variable(self):
        """Coordinate used by the source and its evidence."""
        return self.run.variable

    @property
    def conditional(self):
        """Whether the conclusion depends on unproved hypotheses."""
        return True

    @property
    def complete(self):
        """Completion status for this record's stated scope; replay validity is separate."""
        return False

    @property
    def scope(self):
        """Scope identifier: ``conditional-complex-isolation-termination-theorem``."""
        return "conditional-complex-isolation-termination-theorem"

    @property
    def known_multiple_root(self):
        """Whether the retained evidence identifies a repeated root."""
        return any(c.zero_count > 1 for c in self.run.proof.root_regions)

    @property
    def unproved_hypotheses(self):
        """Premises of the conditional theorem that remain unproved."""
        result = []
        if self.run.proof.outer is None:
            result.append("zero-free-outer-boundary")
        if not self.run.proof.isolation_complete or self.known_multiple_root:
            result.append("all-zeros-simple")
        result.append("unbounded-completed-cofinal-stages")
        return tuple(result)

    @property
    def applicable(self):
        """Whether the theorem's supported input conditions are established."""
        return (
            False
            if self.known_multiple_root
            else None
            if "all-zeros-simple" in self.unproved_hypotheses
            or self.run.proof.outer is None
            else True
        )

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        if (
            type(self) is not ComplexIsolationGuarantee
            or type(self.schema_version) is not int
            or self.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED,
                None,
                False,
                "unsupported-termination-contract-schema",
            )
        if (
            type(self.run) is not ComplexIsolationRun
            or self.theorem != "compact-simple-entire-cofinal"
        ):
            return CheckResult(
                CheckOutcome.REJECTED, False, False, "false-termination-contract"
            )
        checked = self.run.check()
        if checked.certified is not True:
            return checked
        return CheckResult(
            CheckOutcome.LOCAL_VALID,
            True,
            False,
            "conditional-only: " + ", ".join(self.unproved_hypotheses),
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def _seed_run(
    expr,
    var,
    lower_left,
    upper_right,
    *,
    policy=None,
    max_box_width=None,
    max_box_diameter=None,
    max_boundary_depth=14,
    use_newton=True,
    use_multiple=True,
):
    policy = EnclosurePolicy() if policy is None else policy
    if (
        type(policy) is not EnclosurePolicy
        or type(max_boundary_depth) is not int
        or max_boundary_depth < 0
        or type(use_newton) is not bool
        or type(use_multiple) is not bool
    ):
        raise ValueError("invalid cofinal policy, boundary depth or mode")
    state = isolation._seed(
        expr, var, lower_left, upper_right, max_box_width, max_box_diameter
    )
    return ComplexIsolationRun(
        state,
        replace(policy, seconds=None),
        max_boundary_depth=max_boundary_depth,
        use_newton=use_newton,
        use_multiple=use_multiple,
    )


def _wall_run(run):
    return replace(run, state=isolation._wall_state(run.state))


def _advance(run, stages):
    if type(stages) is not int or stages < 0:
        raise ValueError("stages must be a nonnegative integer")
    if not run.verify():
        return run
    for _ in range(stages):
        if run.complete:
            break
        stage = run.next_stage

        sink = checkpoint_sink()

        def capture(state, run=run, sink=sink):
            if sink is not None:
                sink(replace(run, state=state))

        with capture_checkpoints(capture):
            state = isolation._run(
                run.state,
                complex_isolation_policy_stage(stage, base=run.base_policy),
                run.max_boundary_depth + stage,
                run.use_newton,
                run.use_multiple,
                cofinal=True,
            )
        run = replace(run, state=state, next_stage=stage + 1)
        emit_checkpoint(run)
    return run


def adaptive_complex_isolation(
    expr,
    var,
    lower_left,
    upper_right,
    *,
    stages=1,
    policy=None,
    max_box_width=None,
    max_box_diameter=None,
    max_boundary_depth=14,
    use_newton=True,
    use_multiple=True,
):
    """Run finitely many cofinal stages; unresolved work always stays incomplete."""
    from .quotient_isolation import quotient_source_supported

    if quotient_source_supported(expr, var):
        from .quotient_cofinal import adaptive_quotient_isolation

        return adaptive_quotient_isolation(
            expr,
            var,
            lower_left,
            upper_right,
            stages=stages,
            policy=policy,
            max_box_width=max_box_width,
            max_box_diameter=max_box_diameter,
            max_boundary_depth=max_boundary_depth,
            use_newton=use_newton,
            use_multiple=use_multiple,
        )
    policy = EnclosurePolicy() if policy is None else policy
    run = _seed_run(
        expr,
        var,
        lower_left,
        upper_right,
        policy=policy,
        max_box_width=max_box_width,
        max_box_diameter=max_box_diameter,
        max_boundary_depth=max_boundary_depth,
        use_newton=use_newton,
        use_multiple=use_multiple,
    )
    if type(stages) is not int or stages < 0:
        raise ValueError("stages must be a nonnegative integer")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "adaptive_complex_isolation",
            expr,
            (var, lower_left, upper_right),
            {
                "stages": stages,
                "policy": replace(policy, seconds=None),
                "max_box_width": max_box_width,
                "max_box_diameter": max_box_diameter,
                "max_boundary_depth": max_boundary_depth,
                "use_newton": use_newton,
                "use_multiple": use_multiple,
            },
            policy.seconds,
        )
    return _advance(run, stages)


def resume_adaptive_complex_isolation(run, *, stages=1, seconds=None):
    """Continue a validated cofinal run with persistent geometry and effort state."""
    from .quotient_cofinal import (
        QuotientIsolationRun,
        resume_adaptive_quotient_isolation,
    )
    from .quotient_isolation import QuotientIsolationState

    if type(run) in (QuotientIsolationRun, QuotientIsolationState):
        return resume_adaptive_quotient_isolation(run, stages=stages, seconds=seconds)
    if type(run) is ComplexIsolationState:
        run = ComplexIsolationRun(run)
    if type(run) is not ComplexIsolationRun:
        raise ValueError("invalid adaptive complex isolation checkpoint")
    if type(stages) is not int or stages < 0:
        raise ValueError("stages must be a nonnegative integer")
    if seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "resume_adaptive_complex_isolation", run, (), {"stages": stages}, seconds
        )
    if not run.verify():
        raise ValueError("invalid adaptive complex isolation checkpoint")
    return _advance(run, stages)
