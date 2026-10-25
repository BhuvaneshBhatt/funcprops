"""Finite cofinal quotient stages and a separated-simple-root termination contract.

No finite stage or conditional theorem changes unresolved regions into roots or
exclusions. Completion comes only from the native assembly checker.
"""

from dataclasses import dataclass, field, replace

from . import quotient_isolation as isolation
from ._checkpoints import capture_checkpoints, checkpoint_sink, emit_checkpoint
from .complex_cofinal import complex_isolation_policy_stage
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy
from .quotient_isolation import QuotientIsolationState

_PROTOCOL = "dovetail-prefix-precision"


@dataclass(frozen=True)
class QuotientIsolationRun:
    """Retain the frontier and fair-search policy for a quotient zero/pole ledger."""

    state: QuotientIsolationState
    base_policy: EnclosurePolicy = field(default_factory=EnclosurePolicy)
    next_stage: int = 0
    max_boundary_depth: int = 14
    use_newton: bool = True
    use_multiple: bool = True
    protocol: str = _PROTOCOL
    schema_version: int = 1

    @property
    def expression(self):
        return self.state.expression

    @property
    def variable(self):
        return self.state.variable

    @property
    def proof(self):
        return self.state.proof

    @property
    def complete(self):
        return self.state.complete

    @property
    def coverage_complete(self):
        return self.state.coverage_complete

    @property
    def isolation_complete(self):
        return self.state.isolation_complete

    @property
    def accuracy_complete(self):
        return self.state.accuracy_complete

    @property
    def root_count(self):
        return self.state.root_count

    @property
    def distinct_root_count(self):
        return self.root_count

    @property
    def individual_multiplicities(self):
        return self.proof.individual_multiplicities

    @property
    def refinements(self):
        return self.proof.refinements

    @property
    def unresolved(self):
        return self.proof.unresolved

    @property
    def clusters(self):
        return self.proof.clusters

    @property
    def multiplicity_count(self):
        return self.state.multiplicity_count

    @property
    def total_count(self):
        return self.multiplicity_count

    @property
    def tested(self):
        return self.state.tested

    @property
    def pole_multiplicity_count(self):
        return self.proof.pole_multiplicity_count

    @property
    def distinct_pole_count(self):
        return self.proof.distinct_pole_count

    @property
    def isolating_boxes(self):
        return self.proof.isolating_boxes

    @property
    def exhaustion(self):
        return self.proof.exhaustion

    @property
    def termination_contract(self):
        return QuotientIsolationGuarantee(self)

    @property
    def scope(self):
        return "cofinal-staged-quotient_isolation"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        reject = CheckResult(
            CheckOutcome.REJECTED, False, False, "invalid-cofinal-isolation-run"
        )
        try:
            if (
                type(self) is not QuotientIsolationRun
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
                type(self.state) is not QuotientIsolationState
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
class QuotientIsolationGuarantee:
    """State conditional completion premises for separated simple quotient divisors."""

    run: QuotientIsolationRun
    theorem: str = "compact-simple-separated-quotient-cofinal"
    schema_version: int = 1

    @property
    def expression(self):
        return self.run.expression

    @property
    def variable(self):
        return self.run.variable

    @property
    def conditional(self):
        return True

    @property
    def complete(self):
        return False

    @property
    def scope(self):
        return "conditional-quotient_isolation-termination-theorem"

    @property
    def known_multiple_root(self):
        from .complex_isolation import _individual

        return any(
            r.zero_count > 1 and _individual(r)
            for c in self.run.proof.cells
            for r in (c.numerator, c.denominator)
        )

    @property
    def known_collision(self):
        from .shared_zeros import same_base, shared_base

        return any(
            c.numerator.zero_count
            and (
                c.excluded_guard is not None
                or c.guard_zero is not None
                or (
                    c.denominator.zero_count
                    and (
                        same_base(shared_base(c.numerator), shared_base(c.denominator))
                        or (
                            c.numerator_location is not None
                            and c.denominator_location is not None
                            and c.numerator_location.center
                            == c.denominator_location.center
                        )
                    )
                )
            )
            for c in self.run.proof.cells
        )

    @property
    def unproved_hypotheses(self):
        p = self.run.proof
        result = []
        if not p.outer:
            result.append(
                "zero-free-numerator-denominator-and-source-guard-outer-boundaries"
            )
        if (
            not p.outer
            or p.unresolved
            or any(
                r.zero_count > 1 for c in p.cells for r in (c.numerator, c.denominator)
            )
        ):
            result.append("all-numerator-and-denominator-zeros-simple")
        if not p.coverage_complete:
            result.append(
                "unaccounted-numerator-collisions-absent-or-already-certified"
            )
        result.append("unbounded-completed-cofinal-stages")
        return tuple(result)

    @property
    def applicable(self):
        if self.known_multiple_root or self.run.proof.source.numerator == 0:
            return False
        return (
            True
            if self.unproved_hypotheses == ("unbounded-completed-cofinal-stages",)
            else None
        )

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        if (
            type(self) is not QuotientIsolationGuarantee
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
            type(self.run) is not QuotientIsolationRun
            or self.theorem != "compact-simple-separated-quotient-cofinal"
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
    return QuotientIsolationRun(
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
                run.use_multiple,
                run.use_newton,
                cofinal=True,
            )
        run = replace(run, state=state, next_stage=stage + 1)
        emit_checkpoint(run)
    return run


def adaptive_quotient_isolation(
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
            "adaptive_quotient_isolation",
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


def resume_adaptive_quotient_isolation(run, *, stages=1, seconds=None):
    """Continue a validated cofinal run with persistent geometry and effort state."""
    if type(run) is QuotientIsolationState:
        run = QuotientIsolationRun(run)
    if type(run) is not QuotientIsolationRun:
        raise ValueError("invalid adaptive complex isolation checkpoint")
    if type(stages) is not int or stages < 0:
        raise ValueError("stages must be a nonnegative integer")
    if seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "resume_adaptive_quotient_isolation", run, (), {"stages": stages}, seconds
        )
    if not run.verify():
        raise ValueError("invalid adaptive complex isolation checkpoint")
    return _advance(run, stages)
