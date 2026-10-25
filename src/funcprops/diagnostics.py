"""Uniform unresolved-proof and completeness vocabulary."""

from dataclasses import dataclass
from enum import Enum

import sympy as sp

_NATIVE_REPLAY_MODULES = (
    "extrema_bounds",
    "branch_atlas",
    "implicit_orders",
    "coverage_contract",
    "enclosures",
    "adaptive_roots",
    "complex_clusters",
    "analytic_contours",
    "complex_isolation",
    "complex_newton",
    "complex_multiplicity",
    "complex_cofinal",
    "quotient_isolation",
    "quotient_cofinal",
    "quotient_refinement",
    "shared_zeros",
    "property_contract",
    "infinite_contract",
    "parameter_contract",
    "transcendental.complex_roots",
)

_DIRECT_REPLAY_MODULES = (
    *_NATIVE_REPLAY_MODULES,
    "metric_proofs",
    "algebraic_coefficients",
    "parameter_geometry",
    "branch_gluing",
    "real_analysis.regularity_extensions",
    "real_analysis.variation",
)


class UnknownReason(str, Enum):
    """Identify a missing proof premise or unsupported analysis boundary."""

    UNRESOLVED_REALNESS = "unresolved-realness"
    UNRESOLVED_SIGN = "unresolved-sign"
    INCOMPLETE_ZERO_GEOMETRY = "incomplete-zero-geometry"
    UNSUPPORTED_TRANSCENDENTAL = "unsupported-transcendental"
    PARAMETER_STRATIFICATION_INCOMPLETE = "parameter-stratification-incomplete"
    BACKEND_INCONCLUSIVE = "backend-inconclusive"
    PROOF_BUDGET_EXHAUSTED = "proof-budget-exhausted"
    DOMAIN_GEOMETRY_UNSUPPORTED = "domain-geometry-unsupported"


class Completeness(str, Enum):
    """Describe the scope of a result's coverage claim."""

    COMPLETE = "complete"
    COMPLETE_ON_DOMAIN = "complete-on-domain"
    LOCAL = "local"
    PARTIAL = "partial"
    LOWER_BOUND = "lower-bound"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ReplayStatus:
    """Replay outcome, separately from declared coverage or record presence."""

    supported: bool
    certified: bool | None
    complete: bool | None
    scope: str | None = None
    reason: str | None = None
    outcome: str | None = None
    schema_version: int | None = None
    factory_replay: bool = True


def replay_status(record, *, expr=None, var=None, work_budget=None):
    """Report unknown for unsupported replay and false for failed replay.

    Coverage is exposed only following successful replay. This does not turn a
    pointer or an unverified provider status flag into a verified proof.
    """
    from .verification import (
        _certificate_verifiers,
        _matches_source_context,
        verify_certificate,
    )
    from .work_budget import BudgetedResult

    if isinstance(record, BudgetedResult):
        return ReplayStatus(
            True,
            False,
            False,
            reason=record.source,
            outcome=record.outcome,
            factory_replay=False,
        )

    registered = tuple(t for t, _ in _certificate_verifiers())
    if type(record) not in registered:
        parents = tuple(t for t in registered if isinstance(record, t))
        if parents:
            return ReplayStatus(
                True,
                False,
                False,
                reason="unregistered-certificate-subclass",
                outcome="rejected-evidence",
                factory_replay=not any(
                    t.__module__.endswith(_DIRECT_REPLAY_MODULES) for t in parents
                ),
            )
        return ReplayStatus(False, None, None, reason="unsupported-replay")
    if work_budget is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "replay_status", record, (), {"expr": expr, "var": var}, work_budget
        )
    factory_replay = not type(record).__module__.endswith(_DIRECT_REPLAY_MODULES)
    version = None
    try:
        from .algebraic_complex import AlgebraicComplexRootProof
        from .complex_cofinal import ComplexIsolationGuarantee, ComplexIsolationRun
        from .complex_isolation import ComplexIsolationProof, ComplexIsolationState
        from .complex_multiplicity import (
            ComplexExactMultiplicity,
            ComplexLocatedRegion,
            ComplexPowerFactorProof,
            ComplexPowerRootRegion,
        )
        from .complex_newton import (
            ComplexNewtonRefinement,
            ComplexNewtonRegion,
        )
        from .quotient_cofinal import QuotientIsolationGuarantee, QuotientIsolationRun
        from .quotient_isolation import (
            QuotientContourCertificate,
            QuotientIsolationProof,
            QuotientIsolationState,
        )
        from .quotient_refinement import QuotientNewtonRefinement
        from .shared_zeros import (
            ComplexZeroSubsetProof,
            SharedZeroImplication,
            SharedZeroOrderProof,
            SharedZeroRegion,
        )
        from .transcendental.complex_roots import ComplexRootIsolationResult

        if isinstance(record, (AlgebraicComplexRootProof, ComplexRootIsolationResult)):
            factory_replay = getattr(record, "isolation_state", None) is None
            if not _matches_source_context(record, expr, var):
                return ReplayStatus(
                    True,
                    False,
                    False,
                    getattr(record, "scope", None),
                    "source-mismatch",
                    "rejected-evidence",
                    getattr(record, "schema_version", None),
                    factory_replay,
                )
            checked = record.check()
            return ReplayStatus(
                checked.outcome.value != "unsupported-replay",
                checked.certified,
                checked.complete,
                record.scope,
                checked.reason,
                checked.outcome.value,
                getattr(record, "schema_version", None),
                factory_replay,
            )
        from .branch_atlas import GluedPowerProof, LogAtlasProof, LogBranchChart
        from .coverage_checker import check_leaf
        from .enclosures import DerivativeEnclosure, EnclosureResult
        from .extrema_bounds import ExtremaBoundsProof
        from .implicit_orders import (
            CommonZeroProof,
            ImplicitMultiplicityProof,
            ImplicitRootValueProof,
        )

        native_record = type(record).__module__.endswith(_NATIVE_REPLAY_MODULES)
        version = getattr(
            record, "schema_version", getattr(record, "grammar_version", None)
        )
        if native_record and (type(version) is not int or version != 1):
            return ReplayStatus(
                False,
                None,
                False,
                reason="unsupported-schema-version",
                outcome="unsupported-replay",
                schema_version=version,
                factory_replay=False,
            )
        if isinstance(record, (EnclosureResult, DerivativeEnclosure)) and getattr(
            record, "obligations", ()
        ) == ("cell-budget",):
            return ReplayStatus(
                True,
                False,
                False,
                getattr(record, "scope", None),
                "cell-budget",
                "resource-exhaustion",
                version,
                False,
            )
        if (
            (
                isinstance(record, EnclosureResult)
                and not record.witnesses
                and record.outcome.value == "unsupported-replay"
            )
            or (
                isinstance(record, DerivativeEnclosure)
                and record.enclosure is None
                and record.derivative is None
            )
        ) and record.obligations:
            return ReplayStatus(
                False,
                None,
                False,
                getattr(record, "scope", None),
                "; ".join(record.obligations),
                "unsupported-replay",
                version,
                False,
            )
        from .adaptive_roots import AdaptiveRootResult, CoverageState
        from .analytic_contours import (
            AnalyticComplexCoverage,
            AnalyticContourCertificate,
        )
        from .complex_clusters import ComplexClusterCertificate
        from .coverage_contract import CoverageLeaf, CoverageProof, InadmissibleProof
        from .parameter_contract import (
            ParameterCoverageProof,
            SpecializedParameterProof,
            UniformParameterCertificate,
            UniformParameterCover,
        )
        from .property_contract import PropertyCoverageProof

        if isinstance(
            record,
            (
                ExtremaBoundsProof,
                LogBranchChart,
                LogAtlasProof,
                GluedPowerProof,
                ImplicitRootValueProof,
                ImplicitMultiplicityProof,
                CommonZeroProof,
                CoverageProof,
                CoverageLeaf,
                InadmissibleProof,
                AdaptiveRootResult,
                CoverageState,
                ComplexClusterCertificate,
                AnalyticComplexCoverage,
                AnalyticContourCertificate,
                QuotientContourCertificate,
                QuotientIsolationProof,
                QuotientIsolationState,
                QuotientIsolationRun,
                QuotientIsolationGuarantee,
                QuotientNewtonRefinement,
                SharedZeroImplication,
                SharedZeroOrderProof,
                SharedZeroRegion,
                ComplexZeroSubsetProof,
                ComplexIsolationProof,
                ComplexIsolationState,
                ComplexNewtonRefinement,
                ComplexNewtonRegion,
                ComplexExactMultiplicity,
                ComplexLocatedRegion,
                ComplexPowerFactorProof,
                ComplexPowerRootRegion,
                ComplexIsolationRun,
                ComplexIsolationGuarantee,
                PropertyCoverageProof,
                UniformParameterCertificate,
                UniformParameterCover,
                ParameterCoverageProof,
                SpecializedParameterProof,
            ),
        ):
            if not _matches_source_context(record, expr, var):
                return ReplayStatus(
                    True,
                    False,
                    False,
                    reason="source-mismatch",
                    outcome="rejected-evidence",
                    schema_version=record.schema_version,
                    factory_replay=False,
                )
            checked = (
                check_leaf(record)
                if isinstance(record, CoverageLeaf)
                else record.check()
            )
            return ReplayStatus(
                checked.outcome.value != "unsupported-replay",
                checked.certified,
                checked.complete,
                getattr(record, "scope", None),
                checked.reason,
                checked.outcome.value,
                record.schema_version,
                False,
            )
        certified = verify_certificate(record, expr=expr, var=var) is True
        complete = getattr(record, "complete", None) if certified else False
        if complete is sp.S.true:
            complete = True
        elif complete is sp.S.false:
            complete = False
        if type(complete) is not bool and complete is not None:
            complete = None
        scope = getattr(record, "scope", None)
        return ReplayStatus(
            True,
            certified,
            complete,
            scope,
            None if certified else "replay-failed",
            "valid-local-proof" if certified else "rejected-evidence",
            getattr(record, "schema_version", getattr(record, "grammar_version", None)),
            factory_replay,
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        IndexError,
        NotImplementedError,
        ArithmeticError,
    ):
        return ReplayStatus(
            True,
            False,
            False,
            reason="replay-failed",
            outcome="rejected-evidence",
            schema_version=version if type(version) is int else None,
            factory_replay=factory_replay,
        )
