"""Independent, conservative replay checks for exact property certificates.

Verifiers return True only when the certificate's stated conclusion can be
re-established from its payload and current proof primitives. False means the
certificate is internally inconsistent or unsupported; verifiers never turn an
unknown symbolic comparison into success.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from functools import lru_cache

import sympy as sp
from sympy import S

from .exactness import certify_identity_equal
from .exceptions import SYMBOLIC_QUERY_ERRORS
from .results import Sign
from .source_syntax import differentiate, same_data


class _MissingReplayContext(ValueError):
    """A legacy verifier needs source arguments absent from its record."""


def _matches_source_context(record, expr=None, var=None):
    """Compare supplied source arguments in scalar or normalized vector form."""
    from .real_analysis.common import normalize_expressions, normalize_variables

    try:
        if expr is not None:
            supplied = normalize_expressions(expr)
            if hasattr(record, "expressions"):
                if not same_data(record.expressions, supplied):
                    return False
            else:
                actual = getattr(record, "expression", getattr(record, "f", None))
                if len(supplied) != 1 or not same_data(actual, supplied[0]):
                    return False
        if var is not None:
            supplied = normalize_variables(var)
            actual = getattr(record, "variables", None)
            if actual is None:
                actual = (getattr(record, "variable", getattr(record, "var", None)),)
            if not same_data(actual, supplied):
                return False
        return True
    except (AttributeError, TypeError, ValueError):
        return False


def _replay_data(value, substitutions=None):
    substitutions = substitutions or {}
    if isinstance(value, sp.Basic):
        return value.xreplace(substitutions)
    if is_dataclass(value):
        return (
            type(value),
            tuple(
                (field.name, _replay_data(getattr(value, field.name), substitutions))
                for field in fields(value)
            ),
        )
    if isinstance(value, (tuple, list)):
        return tuple(_replay_data(item, substitutions) for item in value)
    return value


def verify_monotonic_decomposition(cert):
    """Check the stored monotonic decomposition premises and report their replay outcome."""

    from .real_analysis.monotonic_certificates import (
        MonotonicDecomposition,
        monotonic_decomposition,
    )

    if not isinstance(cert, MonotonicDecomposition):
        return False
    try:
        actual = monotonic_decomposition(
            cert.expression,
            cert.variable,
            strict=cert.strict,
            continuous=cert.continuous,
            return_result=True,
        )
        if (
            actual is None
            or certify_identity_equal(cert.reconstruct(), cert.expression) is not True
        ):
            return False
        return (
            cert.inner == actual.inner
            and cert.outer.dummy_eq(actual.outer)
            and cert.direction == actual.direction
            and cert.condition == actual.condition
            and cert.strict == actual.strict
            and cert.continuous == actual.continuous
            and (
                (cert.inverse is None and actual.inverse is None)
                or (
                    cert.inverse is not None
                    and actual.inverse is not None
                    and cert.inverse.dummy_eq(actual.inverse)
                )
            )
        )
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_monotonic_partition(expr, var, cert):
    """Check the stored monotonic partition premises and report their replay outcome."""

    from .real_analysis.monotonic_certificates import (
        MonotonicPartition,
        matching_partition,
    )

    if not isinstance(cert, MonotonicPartition):
        return False
    try:
        return matching_partition(cert, expr, var, cert.domain) is not None
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_zero_geometry(cert, *, expr=None, var=None):
    """Check the stored zero geometry premises and report their replay outcome."""

    from .transcendental.zero_geometry import (
        IndexedZero,
        ZeroGeometryCertificate,
        zero_geometry,
    )

    if not isinstance(cert, ZeroGeometryCertificate):
        return False
    if expr is not None and var is not None:
        try:
            return any(
                _replay_data(actual) == _replay_data(cert)
                for actual in zero_geometry(
                    expr, var, derivative_order=cert.derivative_order
                )
            )
        except SYMBOLIC_QUERY_ERRORS:
            return False
    X = sp.Dummy("replay_axis", real=True)
    substitutions = {}
    if (
        cert.family in ("BesselJ", "BesselY", "AiryAi", "AiryBi")
        and cert.indexed_family
    ):
        template = cert.indexed_family[0]
        if (
            not isinstance(template, IndexedZero)
            or not isinstance(template.index, sp.Symbol)
            or template.args[2].has(template.index)
        ):
            return False
        if cert.family == "BesselJ":
            expr = sp.besselj(template.args[2], X)
        elif cert.family == "BesselY":
            expr = sp.bessely(template.args[2], X)
        elif cert.family == "AiryAi":
            expr = sp.airyai(X)
        else:
            expr = sp.airybi(X)
    elif (
        cert.family
        in ("affine-sine-zeros", "affine-cosine-zeros", "affine-tangent-zeros")
        and len(cert.notes) == 4
    ):
        formula, index, index_domain, _multiplicity = cert.notes
        if index_domain is not S.Integers or index.is_integer is not True:
            return False
        coefficient = differentiate(formula, index)
        if coefficient.has(index) or coefficient.is_zero is not False:
            return False
        phase = sp.pi / 2 if cert.family == "affine-cosine-zeros" else S.Zero
        slope = sp.pi / coefficient
        offset = phase - slope * formula.subs(index, 0)
        head = {
            "affine-sine-zeros": sp.sin,
            "affine-cosine-zeros": sp.cos,
            "affine-tangent-zeros": sp.tan,
        }[cert.family]
        expr = head(slope * X + offset)
    else:
        return False  # payload does not bind enough parameters for mathematical replay
    try:
        candidates = zero_geometry(expr, X, derivative_order=cert.derivative_order)
        for actual in candidates:
            if actual.indexed_family and cert.indexed_family:
                substitutions = {
                    actual.indexed_family[0].index: cert.indexed_family[0].index
                }
            elif actual.family.startswith("affine-"):
                substitutions = {actual.notes[1]: cert.notes[1]}
            if _replay_data(actual, substitutions) == _replay_data(cert):
                return True
        return False
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_convexity_certificate(expr, var, cert):
    """Check the stored convexity certificate premises and report their replay outcome."""

    from .proof_cache import property_proof_context
    from .real_analysis.advanced_convexity import ConvexityCertificate

    if not isinstance(cert, ConvexityCertificate):
        return False
    if cert.method in ("exponential-hessian-bound", "interior-hessian-counterexample"):
        from .real_analysis.common import normalize_variables
        from .real_analysis.hessian_bounds import (
            exponential_hessian_data,
            hessian_counterexample_data,
        )

        try:
            check = (
                exponential_hessian_data
                if cert.method == "exponential-hessian-bound"
                else hessian_counterexample_data
            )
            data = check(sp.sympify(expr), normalize_variables(var), cert.domain)
            return data is not None and same_data(
                cert,
                ConvexityCertificate(
                    data[0], cert.domain, cert.method, data[1], data[2]
                ),
            )
        except (TypeError, ValueError, AttributeError, ArithmeticError):
            return False
    if cert.method == "box-hessian-dominance":
        from .real_analysis.common import normalize_variables
        from .real_analysis.hessian_bounds import hessian_dominance_data

        try:
            data = hessian_dominance_data(
                sp.sympify(expr), normalize_variables(var), cert.domain
            )
            if data is None:
                return False
            classification, modulus, proof = data
            return same_data(
                cert,
                ConvexityCertificate(
                    classification, cert.domain, cert.method, modulus, proof
                ),
            )
        except (TypeError, ValueError, AttributeError, ArithmeticError):
            return False
    if cert.modulus is None:
        from .real_analysis.advanced_convexity import convexity_implications
        from .real_analysis.convexity import convexity
        from .results import Convexity, PropertyResult

        if (
            not cert.method
            or not isinstance(cert.classification, Convexity)
            or cert.classification is Convexity.UNKNOWN
        ):
            return False
        try:
            actual = convexity(expr, var, domain=cert.domain)
        except (TypeError, ValueError, NotImplementedError, ArithmeticError):
            return False
        if isinstance(actual, PropertyResult):
            actual = actual.primary
        if actual is None or actual is Convexity.UNKNOWN:
            return False
        return (
            cert.classification is actual
            or cert.classification in convexity_implications(actual)
        )
    from .results import Convexity

    if cert.classification not in (
        Convexity.CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
        Convexity.CONCAVE,
        Convexity.STRICTLY_CONCAVE,
        Convexity.STRONGLY_CONCAVE,
    ):
        return False
    if cert.modulus.is_positive is not True:
        return False
    from .real_analysis.common import condition_to_set
    from .real_analysis.convexity import convexity
    from .results import Convexity, PropertyResult

    if isinstance(var, (tuple, list, sp.Tuple)):
        return False  # scalar second-derivative modulus replay only
    support = (
        cert.domain
        if isinstance(cert.domain, sp.Set)
        else condition_to_set(cert.domain, var)
    )
    if not isinstance(support, sp.Interval):
        return False
    try:
        actual = convexity(expr, var, domain=cert.domain)
    except SYMBOLIC_QUERY_ERRORS:
        return False
    if isinstance(actual, PropertyResult):
        actual = actual.primary
    concave = cert.classification.name.endswith("CONCAVE")
    valid = (
        (Convexity.CONCAVE, Convexity.STRICTLY_CONCAVE, Convexity.STRONGLY_CONCAVE)
        if concave
        else (Convexity.CONVEX, Convexity.STRICTLY_CONVEX, Convexity.STRONGLY_CONVEX)
    )
    if actual not in valid:
        return False
    d2 = property_proof_context(expr, var, domain=cert.domain).derivative(2)
    concave = cert.classification.name.endswith("CONCAVE")
    target = sp.simplify((-d2 if concave else d2) - cert.modulus)
    sg = property_proof_context(target, var, domain=cert.domain).sign(
        domain=cert.domain
    )
    return sg in (Sign.ZERO, Sign.NONNEGATIVE, Sign.POSITIVE)


def verify_extremum_ordering(cert):
    """Check the stored extremum ordering premises and report their replay outcome."""

    from .transcendental.extrema import (
        ExtremumOrderingTheorem,
        extremum_ordering_theorems,
    )

    if not isinstance(cert, ExtremumOrderingTheorem):
        return False
    X = sp.Dummy("replay_axis", real=True)
    if cert.family == "AiryAi":
        expr = sp.airyai(X)
    elif cert.family == "AiryBi":
        expr = sp.airybi(X)
    elif cert.family in ("BesselJ", "BesselY") and cert.parameter is not None:
        expr = (sp.besselj if cert.family == "BesselJ" else sp.bessely)(
            cert.parameter, X
        )
    else:
        return False
    try:
        return any(actual == cert for actual in extremum_ordering_theorems(expr, X))
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_indexed_tail_inversion(cert):
    """Check the stored indexed tail inversion premises and report their replay outcome."""

    from .transcendental.zero_geometry import (
        IndexedTailInversionCertificate,
        indexed_tail_inversion,
    )

    if not isinstance(cert, IndexedTailInversionCertificate):
        return False
    try:
        actual = indexed_tail_inversion(
            cert.zero_template,
            cert.cutoff,
            direction=cert.direction,
            inclusive=cert.inclusive,
        )
        return actual == cert
    except (AttributeError, *SYMBOLIC_QUERY_ERRORS):
        return False


@lru_cache(maxsize=1)
def _certificate_verifiers():
    """Build the concrete-type replay registry and its declared checker dispatch.

    Exact type selection prevents unregistered subclasses from substituting a
    callback for a trusted checker. Some entries replay declared backends."""

    from .adaptive_roots import AdaptiveRootResult, CoverageState
    from .algebraic_coefficients import AlgebraicCoefficientEncoding
    from .algebraic_complex import AlgebraicComplexRootProof
    from .analytic_contours import (
        AnalyticComplexCoverage,
        AnalyticContourCertificate,
        ComplexBoxWitness,
    )
    from .asymptotic_tails import TailSignCertificate
    from .branch_atlas import GluedPowerProof, LogAtlasProof, LogBranchChart
    from .branch_gluing import BranchGluingProof, HolomorphicBranchChart
    from .certified_balls import RealBallCertificate
    from .certified_inequalities import InequalityCertificate
    from .certified_operations import (
        ArgumentPrincipleResult,
        ContinuationCertificate,
        ContourDeformationCertificate,
        EquationSolutionCertificate,
        HomotopyCertificate,
        InverseCertificate,
        LaurentCertificate,
        ResidueCertificate,
        SingularityClassificationCertificate,
        WindingCertificate,
    )
    from .certified_optimization import GlobalMinimumCertificate
    from .complex_certification import (
        ArgumentPrincipleCertificate,
        RectangleRoucheCertificate,
        RoucheCertificate,
    )
    from .complex_clusters import ComplexClusterCertificate
    from .complex_cofinal import ComplexIsolationGuarantee, ComplexIsolationRun
    from .complex_coverage import ComplexRootCoverage, ComplexRootRegionProof
    from .complex_isolation import ComplexIsolationProof, ComplexIsolationState
    from .complex_multiplicity import (
        ComplexExactMultiplicity,
        ComplexLocatedRegion,
        ComplexPowerFactorProof,
        ComplexPowerRootRegion,
        ComplexTaylorWitness,
        ComplexUnitWitness,
    )
    from .complex_newton import (
        ComplexDerivativeWitness,
        ComplexNewtonRefinement,
        ComplexNewtonRegion,
    )
    from .component_optimization import ComponentMinimumResult
    from .coverage_contract import (
        CellDomainWitness,
        CoverageLeaf,
        CoverageProof,
        EnclosureWitness,
        InadmissibleProof,
    )
    from .derivative_inequalities import DerivativeChainCertificate
    from .domain_tracking import DomainRecord
    from .enclosures import DerivativeEnclosure, EnclosureResult
    from .entire_cancellation import EntireCancellationProof
    from .extrema_bounds import ExtremaBoundsProof
    from .geometry import LevelBoundednessCertificate, ModeExistenceCertificate
    from .global_analysis import GlobalInequalityCertificate
    from .global_multivariate import ComposedMapCertificate, GlobalMapCertificate
    from .guarded_affine import (
        GuardedAffineContourCertificate,
        GuardedAffineEquationCertificate,
    )
    from .implicit_orders import (
        CommonZeroProof,
        ImplicitJetWitness,
        ImplicitMultiplicityProof,
        ImplicitRootValueProof,
    )
    from .infinite_contract import PeriodicDomainWitness
    from .integration import IntegralResult
    from .meromorphic_contours import MeromorphicContourCertificate
    from .metric_proofs import FiniteLipschitzProof, JumpVariationProof
    from .parameter_contract import (
        BoxEnclosureWitness,
        ParameterCoverageProof,
        SpecializedParameterProof,
        UniformParameterCertificate,
        UniformParameterCover,
    )
    from .parameter_geometry import ParameterGeometryProof
    from .piecewise_proofs import PiecewiseRegularityCertificate
    from .property_contract import PropertyCoverageProof
    from .quotient_cofinal import QuotientIsolationGuarantee, QuotientIsolationRun
    from .quotient_isolation import (
        DenominatorExclusionProof,
        ExactLocalZeroProof,
        QuotientContourCertificate,
        QuotientIsolationProof,
        QuotientIsolationState,
        QuotientRegionProof,
        QuotientSourceProof,
    )
    from .quotient_refinement import QuotientNewtonRefinement
    from .real_analysis.advanced_convexity import ConvexityCertificate
    from .real_analysis.complete_monotonicity import CompleteMonotonicityCertificate
    from .real_analysis.monotonic_certificates import (
        MonotonicDecomposition,
        MonotonicPartition,
    )
    from .real_analysis.regularity_extensions import LipschitzResult
    from .real_analysis.structural_properties import (
        HomogeneityResult,
        PeriodicityResult,
        SymmetryResult,
    )
    from .real_analysis.variation import VariationResult
    from .root_coverage import (
        RootCoverageCertificate,
        RootRegionProof,
        SpecializedRootCoverage,
    )
    from .seam_regularity import SeamRegularityProof
    from .shared_zeros import (
        ComplexZeroSubsetProof,
        SharedZeroImplication,
        SharedZeroOrderProof,
        SharedZeroRegion,
    )
    from .taylor_models import TaylorModel
    from .transcendental.complex_roots import ComplexRootIsolationResult
    from .transcendental.extrema import (
        ExtremumFamilyCertificate,
        ExtremumOrderingTheorem,
        ExtremumRange,
    )
    from .transcendental.roots import RootCertificate, RootIsolationResult
    from .transcendental.zero_geometry import (
        CertifiedIntegerBracket,
        IndexedTailInversionCertificate,
        ZeroGeometryCertificate,
    )
    from .transformation import (
        ChangeOfVariablesCertificate,
        DeterminantNonvanishingCertificate,
        LocalInvertibilityCertificate,
    )
    from .verified_roots import RealRootInterval

    def self_verifying(cert, expr, var):
        if not _matches_source_context(cert, expr, var):
            return False
        return cert.verify()

    def isolation_replay(cert, expr, var):
        if type(cert) not in (
            QuotientIsolationRun,
            QuotientIsolationGuarantee,
            QuotientNewtonRefinement,
            SharedZeroImplication,
            SharedZeroOrderProof,
            SharedZeroRegion,
            ComplexZeroSubsetProof,
            QuotientSourceProof,
            DenominatorExclusionProof,
            ExactLocalZeroProof,
            QuotientRegionProof,
            QuotientContourCertificate,
            QuotientIsolationProof,
            QuotientIsolationState,
            ComplexIsolationProof,
            ComplexIsolationState,
            ComplexRootIsolationResult,
            ComplexTaylorWitness,
            ComplexUnitWitness,
            ComplexExactMultiplicity,
            ComplexLocatedRegion,
            ComplexPowerFactorProof,
            ComplexPowerRootRegion,
            ComplexIsolationRun,
            ComplexIsolationGuarantee,
            ComplexDerivativeWitness,
            ComplexNewtonRefinement,
            ComplexNewtonRegion,
        ):
            return False
        return self_verifying(cert, expr, var)

    def rouche_circle(cert, expr, var):
        if not _matches_source_context(cert, expr, var):
            return False
        return cert.verify()

    def source_bound(cert, expr, var):
        if not _matches_source_context(cert, expr, var):
            return False
        return cert.verify()

    def composed_map(cert, expr, var):
        if expr is not None or var is not None:
            return False  # this theorem binds its components, not an expanded formula
        return cert.verify()

    def bound_checker(checker):
        def replay(cert, expr, var):
            return _matches_source_context(cert, expr, var) and checker(cert)

        return replay

    def monotonic_partition(cert, expr, var):
        if expr is None or var is None:
            raise _MissingReplayContext(
                "expr and var are required for MonotonicPartition replay"
            )
        return verify_monotonic_partition(expr, var, cert)

    def convexity(cert, expr, var):
        if expr is None or var is None:
            raise _MissingReplayContext(
                "expr and var are required for convexity replay"
            )
        return verify_convexity_certificate(expr, var, cert)

    def periodicity(cert, expr, var):
        if expr is None or var is None:
            raise _MissingReplayContext(
                "expr and var are required for periodicity replay"
            )
        return verify_periodicity_result(expr, var, cert)

    def symmetry(cert, expr, var):
        if expr is None or var is None:
            raise _MissingReplayContext("expr and var are required for symmetry replay")
        return verify_symmetry_result(expr, var, cert)

    def homogeneity(cert, expr, var):
        if expr is None:
            raise _MissingReplayContext("expr is required for homogeneity replay")
        if not _matches_source_context(cert, var=var):
            return False
        return verify_homogeneity_result(expr, cert)

    return (
        (ParameterGeometryProof, self_verifying),
        (BranchGluingProof, self_verifying),
        (HolomorphicBranchChart, self_verifying),
        (AlgebraicCoefficientEncoding, self_verifying),
        (SeamRegularityProof, self_verifying),
        (EntireCancellationProof, self_verifying),
        (FiniteLipschitzProof, self_verifying),
        (JumpVariationProof, self_verifying),
        (LipschitzResult, self_verifying),
        (VariationResult, self_verifying),
        (ExtremaBoundsProof, self_verifying),
        (LogBranchChart, self_verifying),
        (LogAtlasProof, self_verifying),
        (GluedPowerProof, self_verifying),
        (ImplicitRootValueProof, self_verifying),
        (ImplicitMultiplicityProof, self_verifying),
        (ImplicitJetWitness, self_verifying),
        (CommonZeroProof, self_verifying),
        (AlgebraicComplexRootProof, self_verifying),
        (QuotientSourceProof, isolation_replay),
        (DenominatorExclusionProof, isolation_replay),
        (ExactLocalZeroProof, isolation_replay),
        (QuotientRegionProof, isolation_replay),
        (QuotientContourCertificate, isolation_replay),
        (QuotientIsolationProof, isolation_replay),
        (QuotientIsolationState, isolation_replay),
        (ComplexIsolationProof, isolation_replay),
        (ComplexTaylorWitness, isolation_replay),
        (ComplexUnitWitness, isolation_replay),
        (ComplexExactMultiplicity, isolation_replay),
        (ComplexLocatedRegion, isolation_replay),
        (ComplexPowerFactorProof, isolation_replay),
        (ComplexPowerRootRegion, isolation_replay),
        (QuotientIsolationRun, isolation_replay),
        (QuotientIsolationGuarantee, isolation_replay),
        (QuotientNewtonRefinement, isolation_replay),
        (SharedZeroImplication, isolation_replay),
        (SharedZeroOrderProof, isolation_replay),
        (SharedZeroRegion, isolation_replay),
        (ComplexZeroSubsetProof, isolation_replay),
        (ComplexIsolationRun, isolation_replay),
        (ComplexIsolationGuarantee, isolation_replay),
        (ComplexDerivativeWitness, isolation_replay),
        (ComplexNewtonRefinement, isolation_replay),
        (ComplexNewtonRegion, isolation_replay),
        (ComplexIsolationState, isolation_replay),
        (ComplexRootIsolationResult, isolation_replay),
        (BoxEnclosureWitness, self_verifying),
        (UniformParameterCertificate, self_verifying),
        (UniformParameterCover, self_verifying),
        (ParameterCoverageProof, self_verifying),
        (SpecializedParameterProof, self_verifying),
        (PeriodicDomainWitness, self_verifying),
        (ComplexClusterCertificate, self_verifying),
        (AnalyticComplexCoverage, self_verifying),
        (AnalyticContourCertificate, self_verifying),
        (ComplexBoxWitness, self_verifying),
        (PropertyCoverageProof, self_verifying),
        (AdaptiveRootResult, self_verifying),
        (CoverageState, self_verifying),
        (CoverageProof, self_verifying),
        (CellDomainWitness, self_verifying),
        (CoverageLeaf, self_verifying),
        (EnclosureWitness, self_verifying),
        (InadmissibleProof, self_verifying),
        (EnclosureResult, self_verifying),
        (DerivativeEnclosure, self_verifying),
        (RoucheCertificate, rouche_circle),
        (RectangleRoucheCertificate, source_bound),
        (ArgumentPrincipleCertificate, source_bound),
        (GuardedAffineEquationCertificate, source_bound),
        (GuardedAffineContourCertificate, source_bound),
        (TailSignCertificate, source_bound),
        (MeromorphicContourCertificate, source_bound),
        (RealBallCertificate, source_bound),
        (PiecewiseRegularityCertificate, source_bound),
        (InequalityCertificate, source_bound),
        (DerivativeChainCertificate, source_bound),
        (GlobalInequalityCertificate, source_bound),
        (GlobalMapCertificate, source_bound),
        (ComposedMapCertificate, composed_map),
        (IntegralResult, self_verifying),
        (InverseCertificate, self_verifying),
        (EquationSolutionCertificate, self_verifying),
        (LaurentCertificate, self_verifying),
        (ResidueCertificate, self_verifying),
        (WindingCertificate, self_verifying),
        (ArgumentPrincipleResult, self_verifying),
        (HomotopyCertificate, self_verifying),
        (ContinuationCertificate, self_verifying),
        (SingularityClassificationCertificate, self_verifying),
        (ContourDeformationCertificate, self_verifying),
        (ChangeOfVariablesCertificate, self_verifying),
        (DeterminantNonvanishingCertificate, self_verifying),
        (LocalInvertibilityCertificate, self_verifying),
        (RootRegionProof, source_bound),
        (RootCoverageCertificate, source_bound),
        (SpecializedRootCoverage, source_bound),
        (ComplexRootRegionProof, source_bound),
        (ComplexRootCoverage, source_bound),
        (DomainRecord, source_bound),
        (ComponentMinimumResult, source_bound),
        (GlobalMinimumCertificate, source_bound),
        (RootIsolationResult, source_bound),
        (RealRootInterval, source_bound),
        (TaylorModel, source_bound),
        (CompleteMonotonicityCertificate, self_verifying),
        (LevelBoundednessCertificate, self_verifying),
        (ModeExistenceCertificate, self_verifying),
        (
            MonotonicDecomposition,
            bound_checker(verify_monotonic_decomposition),
        ),
        (MonotonicPartition, monotonic_partition),
        (ConvexityCertificate, convexity),
        (
            ZeroGeometryCertificate,
            lambda cert, expr, var: verify_zero_geometry(cert, expr=expr, var=var),
        ),
        (RootCertificate, bound_checker(verify_root_certificate)),
        (
            ExtremumFamilyCertificate,
            bound_checker(verify_extremum_family),
        ),
        (ExtremumRange, bound_checker(verify_extremum_range)),
        (
            ExtremumOrderingTheorem,
            bound_checker(verify_extremum_ordering),
        ),
        (CertifiedIntegerBracket, bound_checker(verify_integer_bracket)),
        (
            IndexedTailInversionCertificate,
            bound_checker(verify_indexed_tail_inversion),
        ),
        (PeriodicityResult, periodicity),
        (SymmetryResult, symmetry),
        (HomogeneityResult, homogeneity),
    )


def verify_certificate(cert, *, expr=None, var=None, work_budget=None):
    """Replay any certificate supported by the package verifier registry."""
    if work_budget is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "verify_certificate", cert, (), {"expr": expr, "var": var}, work_budget
        )
    registry = _certificate_verifiers()
    # Only explicitly registered record types may select a trusted checker.
    # An unregistered subclass can override verify() or other proof properties.
    # Match exact registrations first so a registered derived type can select
    # its own checker even when a base type appears earlier in the registry.
    for certificate_type, verifier in registry:
        if type(cert) is certificate_type:
            try:
                result = verifier(cert, expr, var)
            except _MissingReplayContext:
                raise
            except (
                AttributeError,
                TypeError,
                ValueError,
                IndexError,
                NotImplementedError,
                ArithmeticError,
            ):
                return False
            # Some exact arithmetic checkers return SymPy's Boolean singleton.
            # Accept only literal truth, never an unresolved predicate or a
            # truthy payload such as an integer or a proof object.
            return result is True or result is sp.S.true
    if any(isinstance(cert, certificate_type) for certificate_type, _ in registry):
        return False
    raise TypeError(f"unsupported certificate type: {type(cert).__name__}")


def verify_root_certificate(cert):
    """Check the stored root certificate premises and report their replay outcome."""

    from .transcendental.roots import RootCertificate, transcendental_roots

    if (
        not isinstance(cert, RootCertificate)
        or cert.expression is None
        or cert.variable is None
    ):
        return False
    try:
        actual = transcendental_roots(
            cert.expression, cert.variable, cert.domain, allow_numerical=False
        )
        candidates = actual.certificates + tuple(
            c.certificate for c in actual.isolated_intervals
        )
        return any(_replay_data(c) == _replay_data(cert) for c in candidates)
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_extremum_family(cert):
    """Check the stored extremum family premises and report their replay outcome."""

    from .transcendental.extrema import ExtremumFamilyCertificate, extremum_geometry

    if (
        not isinstance(cert, ExtremumFamilyCertificate)
        or cert.expression is None
        or cert.variable is None
    ):
        return False
    try:
        return any(
            _replay_data(c) == _replay_data(cert)
            for c in extremum_geometry(
                cert.expression, cert.variable, domain=cert.domain
            )
        )
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_extremum_range(cert):
    """Check the stored extremum range premises and report their replay outcome."""

    from .transcendental.extrema import ExtremumRange, symbolic_extremum_range

    if (
        not isinstance(cert, ExtremumRange)
        or cert.expression is None
        or cert.variable is None
    ):
        return False
    try:
        actual = symbolic_extremum_range(cert.expression, cert.variable, cert.domain)
        return actual is not None and _replay_data(actual) == _replay_data(cert)
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_integer_bracket(cert):
    """Check the stored integer bracket premises and report their replay outcome."""

    from .transcendental.zero_geometry import (
        CertifiedIntegerBracket,
        indexed_tail_integer_bracket,
    )

    if (
        not isinstance(cert, CertifiedIntegerBracket)
        or cert.zero_template is None
        or cert.cutoff is None
    ):
        return False
    try:
        actual = indexed_tail_integer_bracket(
            cert.zero_template,
            cert.cutoff,
            direction=cert.direction,
            inclusive=cert.inclusive,
        )
        return actual is not None and _replay_data(actual) == _replay_data(cert)
    except SYMBOLIC_QUERY_ERRORS:
        return False


def verify_periodicity_result(expr, var, cert):
    """Check the stored periodicity result premises and report their replay outcome."""

    from .real_analysis.structural_properties import PeriodicityResult
    from .results import Periodicity

    if not isinstance(cert, PeriodicityResult):
        return False
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if cert.complete is not None or cert.certified is not None:
        from .real_analysis.structural_properties import periodicity

        return (
            periodicity(
                expr,
                var,
                domain=cert.domain,
                assumptions=cert.assumptions,
                return_result=True,
            )
            == cert
        )
    if cert.cases:
        from .real_analysis.structural_properties import periodicity

        actual = periodicity(
            expr,
            var,
            domain=cert.domain,
            assumptions=cert.assumptions,
            return_result=True,
        )
        if (
            actual.cases != cert.cases
            or actual.classification is not cert.classification
            or actual.complete != cert.complete
            or actual.certified != cert.certified
        ):
            return False
        if expr.is_polynomial(var):
            return actual == cert
    if cert.classification is Periodicity.CONSTANT:
        from .real_analysis.structural_properties import _polynomial_periodicity

        return (
            not _substitute_equalities(expr, cert.conditions).has(var)
            or _polynomial_periodicity(expr, var, cert.conditions)
            is Periodicity.CONSTANT
        )
    if cert.classification is Periodicity.PERIODIC:
        if cert.period is None:
            return False
        if (
            cert.period.is_positive is not True
            and "conditional-affine-frequency" not in cert.evidence
        ):
            return False
        try:
            if certify_identity_equal(expr.subs(var, var + cert.period), expr) is True:
                return True
            if "conditional-affine-frequency" in cert.evidence and expr.func in (
                sp.sin,
                sp.cos,
                sp.tan,
                sp.cot,
            ):
                from .engine import simplify_condition

                a = sp.simplify(differentiate(expr.args[0], var))
                if a.has(var):
                    return False
                real_ok = simplify_condition(sp.Q.real(a), assumptions=cert.conditions)
                nonzero_ok = simplify_condition(
                    sp.Ne(a, 0), assumptions=cert.conditions
                )
                base = sp.pi if expr.func in (sp.tan, sp.cot) else 2 * sp.pi
                period_ok = (
                    certify_identity_equal(cert.period, sp.simplify(base / sp.Abs(a)))
                    is True
                )
                return real_ok is S.true and nonzero_ok is S.true and period_ok
            return False
        except SYMBOLIC_QUERY_ERRORS:
            return False
    if cert.classification is Periodicity.APERIODIC:
        try:
            from .real_analysis.structural_properties import _polynomial_periodicity

            if (
                _polynomial_periodicity(expr, var, cert.conditions)
                is Periodicity.APERIODIC
            ):
                return True
            if "incommensurate-component-periods" in cert.evidence:
                from .real_analysis.structural_properties import (
                    _visible_incommensurate_periods,
                )

                return _visible_incommensurate_periods(expr, var)
            return False
        except SYMBOLIC_QUERY_ERRORS:
            return False
    return cert.classification.value == "unknown"


def verify_symmetry_result(expr, var, cert):
    """Check the stored symmetry result premises and report their replay outcome."""

    from .real_analysis.structural_properties import SymmetryResult
    from .results import Symmetry

    if not isinstance(cert, SymmetryResult):
        return False
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    c = sp.sympify(cert.center)
    if c.is_real is not True or c.is_finite is not True:
        return False
    if cert.complete is not None or cert.certified is not None:
        from .real_analysis.structural_properties import symmetry

        return (
            symmetry(
                expr,
                var,
                center=cert.query_center,
                domain=cert.domain,
                assumptions=cert.assumptions,
                return_result=True,
            )
            == cert
        )
    if cert.cases:
        from .real_analysis.structural_properties import symmetry

        actual = symmetry(
            expr,
            var,
            center=cert.center,
            domain=cert.domain,
            assumptions=cert.assumptions,
            return_result=True,
        )
        return actual == cert
    if cert.center_period is not None or cert.center_families:
        from .real_analysis.structural_properties import _trig_center_family

        actual = _trig_center_family(expr, var)
        if (
            actual is None
            or (c, cert.center_period, cert.classification, cert.center_families)
            != actual
        ):
            return False
    if cert.centers is S.Reals:
        if not expr.is_polynomial(var) or sp.Poly(expr, var).degree() > 1:
            return False
    elif cert.centers:
        from .real_analysis.structural_properties import _classify_about

        if any(
            _classify_about(expr, var, sp.sympify(center), allow_central=True)[0]
            not in (Symmetry.EVEN, Symmetry.ODD, Symmetry.BOTH, Symmetry.CENTRAL)
            for center in cert.centers
        ):
            return False
    try:
        ref = sp.simplify(expr.subs(var, 2 * c - var))
        ev = certify_identity_equal(ref, expr)
        od = certify_identity_equal(ref, -expr)
    except SYMBOLIC_QUERY_ERRORS:
        return False
    if cert.classification is Symmetry.BOTH:
        return ev is True and od is True
    if cert.classification is Symmetry.EVEN:
        return ev is True
    if cert.classification is Symmetry.ODD:
        return od is True
    if cert.classification is Symmetry.CENTRAL:
        try:
            return certify_identity_equal(ref + expr, 2 * cert.central_value) is True
        except SYMBOLIC_QUERY_ERRORS:
            return False
    if cert.classification is Symmetry.NEITHER:
        from .real_analysis.structural_properties import _identity_on_axis

        return (
            _identity_on_axis(ref - expr, var) is False
            and _identity_on_axis(ref + expr, var) is False
        )
    return True


def _substitute_equalities(expr, assumptions):
    repl = {}
    atoms = assumptions.args if isinstance(assumptions, sp.And) else (assumptions,)
    for a in atoms:
        if isinstance(a, sp.Equality):
            if getattr(a.lhs, "is_Symbol", False) and not a.rhs.has(a.lhs):
                repl[a.lhs] = a.rhs
            elif getattr(a.rhs, "is_Symbol", False) and not a.lhs.has(a.rhs):
                repl[a.rhs] = a.lhs
    return sp.simplify(expr.xreplace(repl)) if repl else sp.simplify(expr)


def verify_homogeneity_result(expr, cert):
    """Check the stored homogeneity result premises and report their replay outcome."""

    from .real_analysis.structural_properties import HomogeneityResult
    from .results import Homogeneity

    if not isinstance(cert, HomogeneityResult):
        return False
    expr = sp.sympify(expr)
    assumptions = getattr(cert, "assumptions", S.true)
    if cert.classification is Homogeneity.NOT_HOMOGENEOUS:
        from .real_analysis.structural_properties import homogeneity

        try:
            # A requested degree is retained in the guarded case for polynomial queries.
            requested = cert.requested_degree
            actual = homogeneity(
                expr,
                cert.variables,
                degree=requested,
                weights=cert.weights or None,
                assumptions=assumptions,
                return_result=True,
            )
            return (
                actual.classification is Homogeneity.NOT_HOMOGENEOUS
                and actual.cases == cert.cases
                and actual.conditions == cert.conditions
            )
        except SYMBOLIC_QUERY_ERRORS:
            return False
    if (
        cert.classification is Homogeneity.HOMOGENEOUS
        and cert.requested_degree is not None
        and cert.degree != cert.requested_degree
    ):
        return False
    if cert.classification is Homogeneity.UNKNOWN:
        return True
    if cert.degree is None:
        reduced = _substitute_equalities(expr, assumptions)
        return reduced == 0 or not any(reduced.has(v) for v in cert.variables)
    t = sp.Dummy("_verify_scale", positive=True)
    try:
        scaled = expr.xreplace(
            {
                v: t**w * v
                for v, w in zip(
                    cert.variables,
                    cert.weights or (S.One,) * len(cert.variables),
                    strict=False,
                )
            }
        )
        return _substitute_equalities(scaled - t**cert.degree * expr, assumptions) == 0
    except SYMBOLIC_QUERY_ERRORS:
        return False
