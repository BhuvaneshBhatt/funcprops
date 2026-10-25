# Replay and consumer test matrix

All 122 registered concrete replay types have an assigned family. These assignments locate maintained tests and their intended obligations; they are not an assertion of complete semantic coverage. The replay-evidence plugin reports actual accepted/rejected examples by type and test node. Missing observations remain explicit gaps, distinct from these static assignments.

## Family obligations

| Family | Replay | Obligation suites |
| --- | --- | --- |
| native-real | Independent native witness replay | [test_coverage_kernel.py](../../tests/test_coverage_kernel.py), [test_real_enclosures.py](../../tests/test_real_enclosures.py), [test_adaptive_root_coverage.py](../../tests/test_adaptive_root_coverage.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py) |
| infinite-real | Independent native witness replay | [test_periodic_root_coverage.py](../../tests/test_periodic_root_coverage.py), [test_tail_root_coverage.py](../../tests/test_tail_root_coverage.py) |
| parameters | Independent native witness replay | [test_parameter_root_coverage.py](../../tests/test_parameter_root_coverage.py), [test_uniform_parameter_coverage.py](../../tests/test_uniform_parameter_coverage.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py) |
| property-assembly | Independent native witness replay | [test_property_coverage.py](../../tests/test_property_coverage.py) |
| entire-contours | Independent native witness replay | [test_complex_clusters.py](../../tests/test_complex_clusters.py), [test_analytic_contours.py](../../tests/test_analytic_contours.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py) |
| complex-isolation | Independent native witness replay | [test_complex_isolation_soundness.py](../../tests/test_complex_isolation_soundness.py), [test_complex_cover_assembly.py](../../tests/test_complex_cover_assembly.py) |
| complex-multiplicity | Independent native witness replay | [test_complex_completion.py](../../tests/test_complex_completion.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py) |
| complex-newton | Independent native witness replay | [test_complex_newton.py](../../tests/test_complex_newton.py) |
| complex-cofinal | Independent native witness replay | [test_complex_completion.py](../../tests/test_complex_completion.py) |
| quotient-ledger | Independent native witness replay | [test_quotient_isolation.py](../../tests/test_quotient_isolation.py), [test_quotient_soundness_audit.py](../../tests/test_quotient_soundness_audit.py) |
| quotient-shared-orders | Independent native witness replay | [test_quotient_shared_orders.py](../../tests/test_quotient_shared_orders.py), [test_quotient_soundness_audit.py](../../tests/test_quotient_soundness_audit.py) |
| complex-public | Declared factory/backend or route-dependent replay | [test_algroots_complex_adapter.py](../../tests/test_algroots_complex_adapter.py), [test_complex_cover_assembly.py](../../tests/test_complex_cover_assembly.py), [test_quotient_isolation.py](../../tests/test_quotient_isolation.py) |
| algebraic-adapter | Declared factory/backend or route-dependent replay | [test_algroots_complex_adapter.py](../../tests/test_algroots_complex_adapter.py), [test_quotient_soundness_audit.py](../../tests/test_quotient_soundness_audit.py) |
| root-coverage | Declared factory/backend or route-dependent replay | [test_regularity_proof_soundness.py](../../tests/test_regularity_proof_soundness.py), [test_root_coverage_checker.py](../../tests/test_root_coverage_checker.py) |
| local-counts | Declared factory/backend or route-dependent replay | [test_complex_operations_soundness.py](../../tests/test_complex_operations_soundness.py), [test_equation_and_contour_contracts.py](../../tests/test_equation_and_contour_contracts.py) |
| guarded-affine | Declared factory/backend or route-dependent replay | [test_equation_and_contour_contracts.py](../../tests/test_equation_and_contour_contracts.py) |
| inequality-and-piecewise | Declared factory/backend or route-dependent replay | [test_compositional_proof_soundness.py](../../tests/test_compositional_proof_soundness.py), [test_consistent_helper_proofs.py](../../tests/test_consistent_helper_proofs.py), [test_equation_and_contour_contracts.py](../../tests/test_equation_and_contour_contracts.py) |
| global-maps | Declared factory/backend or route-dependent replay | [test_consistent_helper_proofs.py](../../tests/test_consistent_helper_proofs.py), [test_multivariate_certification.py](../../tests/test_multivariate_certification.py) |
| certified_operations | Declared factory/backend or route-dependent replay | [test_certified_operations.py](../../tests/test_certified_operations.py), [test_complex_operations_soundness.py](../../tests/test_complex_operations_soundness.py), [test_compositional_proof_soundness.py](../../tests/test_compositional_proof_soundness.py), [test_integration_parametric_contours.py](../../tests/test_integration_parametric_contours.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py) |
| transformations | Declared factory/backend or route-dependent replay | [test_multivariate_certification.py](../../tests/test_multivariate_certification.py), [test_transformation_geometry.py](../../tests/test_transformation_geometry.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py), [test_differential_soundness.py](../../tests/test_differential_soundness.py), [test_sign_routes.py](../../tests/test_sign_routes.py) |
| domain-and-optimization | Declared factory/backend or route-dependent replay | [test_domain_components_and_replay.py](../../tests/test_domain_components_and_replay.py), [test_domain_components_and_replay.py](../../tests/test_domain_components_and_replay.py) |
| real-root-certificates | Declared factory/backend or route-dependent replay | [test_certified_numerical_analysis.py](../../tests/test_certified_numerical_analysis.py), [test_transcendental_certification.py](../../tests/test_transcendental_certification.py) |
| geometry | Declared factory/backend or route-dependent replay | [test_boundary_and_attainment_geometry.py](../../tests/test_boundary_and_attainment_geometry.py), [test_structural_properties.py](../../tests/test_structural_properties.py) |
| real-property-certificates | Declared factory/backend or route-dependent replay | [test_exported_helpers_and_replay.py](../../tests/test_exported_helpers_and_replay.py), [test_guarded_proofs_and_status.py](../../tests/test_guarded_proofs_and_status.py), [test_structural_properties.py](../../tests/test_structural_properties.py), [test_replay_type_fixtures.py](../../tests/certificates/test_replay_type_fixtures.py), [test_consumer_soundness.py](../../tests/test_consumer_soundness.py), [test_property_models.py](../../tests/property/test_property_models.py), [test_proof_obligations.py](../../tests/test_proof_obligations.py), [test_sign_routes.py](../../tests/test_sign_routes.py) |
| indexed-extrema | Declared factory/backend or route-dependent replay | [test_complex_operations_soundness.py](../../tests/test_complex_operations_soundness.py), [test_exported_helpers_and_replay.py](../../tests/test_exported_helpers_and_replay.py), [test_transcendental_real_analysis.py](../../tests/test_transcendental_real_analysis.py) |
| extrema-bounds | Independent native witness replay | [test_extrema_bounds.py](../../tests/test_extrema_bounds.py) |
| branch_atlas | Independent native witness replay | [test_branch_atlas.py](../../tests/test_branch_atlas.py) |
| implicit_orders | Independent native witness replay | [test_implicit_orders.py](../../tests/test_implicit_orders.py) |
| finite-metric-replay | Independent native witness replay | [test_metric_replay.py](../../tests/test_metric_replay.py), [test_property_models.py](../../tests/property/test_property_models.py), [test_proof_obligations.py](../../tests/test_proof_obligations.py), [test_source_transport_models.py](../../tests/property/test_source_transport_models.py) |
| exact-coefficient-fields | Independent native witness replay | [test_algebraic_coefficient_support.py](../../tests/test_algebraic_coefficient_support.py), [test_property_models.py](../../tests/property/test_property_models.py), [test_proof_obligations.py](../../tests/test_proof_obligations.py) |
| polynomial-parameter-geometry | Independent native witness replay | [test_parameter_geometry.py](../../tests/test_parameter_geometry.py), [test_property_models.py](../../tests/property/test_property_models.py), [test_proof_obligations.py](../../tests/test_proof_obligations.py) |
| holomorphic-branch-gluing | Independent native witness replay | [test_branch_gluing.py](../../tests/test_branch_gluing.py), [test_proof_obligations.py](../../tests/test_proof_obligations.py) |
| bounded-regularity | Independent native witness replay | [test_practical_proofs.py](../../tests/test_practical_proofs.py) |

Each family tracks valid evidence, violated premises or honest decline, source/domain binding, theorem-relevant field mutations, and its declared replay route. The shared [result contracts](../../tests/specification/test_result_contracts.py) and [registered-type rejection tests](../../tests/test_quotient_soundness_audit.py) cover status semantics and self-attesting subclasses. Cluster/unresolved/accuracy cases apply to isolation families; not every factory-based record has these fields.

## Concrete registered types

| Type | Assigned family |
| --- | --- |
| `funcprops.adaptive_roots.AdaptiveRootResult` | native-real |
| `funcprops.adaptive_roots.CoverageState` | native-real |
| `funcprops.algebraic_coefficients.AlgebraicCoefficientEncoding` | exact-coefficient-fields |
| `funcprops.algebraic_complex.AlgebraicComplexRootProof` | algebraic-adapter |
| `funcprops.analytic_contours.AnalyticComplexCoverage` | entire-contours |
| `funcprops.analytic_contours.AnalyticContourCertificate` | entire-contours |
| `funcprops.analytic_contours.ComplexBoxWitness` | entire-contours |
| `funcprops.asymptotic_tails.TailSignCertificate` | inequality-and-piecewise |
| `funcprops.branch_atlas.GluedPowerProof` | branch_atlas |
| `funcprops.branch_atlas.LogAtlasProof` | branch_atlas |
| `funcprops.branch_atlas.LogBranchChart` | branch_atlas |
| `funcprops.branch_gluing.BranchGluingProof` | holomorphic-branch-gluing |
| `funcprops.branch_gluing.HolomorphicBranchChart` | holomorphic-branch-gluing |
| `funcprops.certified_balls.RealBallCertificate` | inequality-and-piecewise |
| `funcprops.certified_inequalities.InequalityCertificate` | inequality-and-piecewise |
| `funcprops.certified_operations.ArgumentPrincipleResult` | certified_operations |
| `funcprops.certified_operations.ContinuationCertificate` | certified_operations |
| `funcprops.certified_operations.ContourDeformationCertificate` | certified_operations |
| `funcprops.certified_operations.EquationSolutionCertificate` | certified_operations |
| `funcprops.certified_operations.HomotopyCertificate` | certified_operations |
| `funcprops.certified_operations.InverseCertificate` | certified_operations |
| `funcprops.certified_operations.LaurentCertificate` | certified_operations |
| `funcprops.certified_operations.ResidueCertificate` | certified_operations |
| `funcprops.certified_operations.SingularityClassificationCertificate` | certified_operations |
| `funcprops.certified_operations.WindingCertificate` | certified_operations |
| `funcprops.certified_optimization.GlobalMinimumCertificate` | domain-and-optimization |
| `funcprops.complex_certification.ArgumentPrincipleCertificate` | local-counts |
| `funcprops.complex_certification.RectangleRoucheCertificate` | local-counts |
| `funcprops.complex_certification.RoucheCertificate` | local-counts |
| `funcprops.complex_clusters.ComplexClusterCertificate` | entire-contours |
| `funcprops.complex_cofinal.ComplexIsolationGuarantee` | complex-cofinal |
| `funcprops.complex_cofinal.ComplexIsolationRun` | complex-cofinal |
| `funcprops.complex_coverage.ComplexRootCoverage` | root-coverage |
| `funcprops.complex_coverage.ComplexRootRegionProof` | root-coverage |
| `funcprops.complex_isolation.ComplexIsolationProof` | complex-isolation |
| `funcprops.complex_isolation.ComplexIsolationState` | complex-isolation |
| `funcprops.complex_multiplicity.ComplexExactMultiplicity` | complex-multiplicity |
| `funcprops.complex_multiplicity.ComplexLocatedRegion` | complex-multiplicity |
| `funcprops.complex_multiplicity.ComplexPowerFactorProof` | complex-multiplicity |
| `funcprops.complex_multiplicity.ComplexPowerRootRegion` | complex-multiplicity |
| `funcprops.complex_multiplicity.ComplexTaylorWitness` | complex-multiplicity |
| `funcprops.complex_multiplicity.ComplexUnitWitness` | complex-multiplicity |
| `funcprops.complex_newton.ComplexDerivativeWitness` | complex-newton |
| `funcprops.complex_newton.ComplexNewtonRefinement` | complex-newton |
| `funcprops.complex_newton.ComplexNewtonRegion` | complex-newton |
| `funcprops.component_optimization.ComponentMinimumResult` | domain-and-optimization |
| `funcprops.coverage_contract.CellDomainWitness` | native-real |
| `funcprops.coverage_contract.CoverageLeaf` | native-real |
| `funcprops.coverage_contract.CoverageProof` | native-real |
| `funcprops.coverage_contract.EnclosureWitness` | native-real |
| `funcprops.coverage_contract.InadmissibleProof` | native-real |
| `funcprops.derivative_inequalities.DerivativeChainCertificate` | inequality-and-piecewise |
| `funcprops.domain_tracking.DomainRecord` | domain-and-optimization |
| `funcprops.enclosures.DerivativeEnclosure` | native-real |
| `funcprops.enclosures.EnclosureResult` | native-real |
| `funcprops.entire_cancellation.EntireCancellationProof` | bounded-regularity |
| `funcprops.extrema_bounds.ExtremaBoundsProof` | extrema-bounds |
| `funcprops.geometry.LevelBoundednessCertificate` | geometry |
| `funcprops.geometry.ModeExistenceCertificate` | geometry |
| `funcprops.global_analysis.GlobalInequalityCertificate` | inequality-and-piecewise |
| `funcprops.global_multivariate.ComposedMapCertificate` | global-maps |
| `funcprops.global_multivariate.GlobalMapCertificate` | global-maps |
| `funcprops.guarded_affine.GuardedAffineContourCertificate` | guarded-affine |
| `funcprops.guarded_affine.GuardedAffineEquationCertificate` | guarded-affine |
| `funcprops.implicit_orders.CommonZeroProof` | implicit_orders |
| `funcprops.implicit_orders.ImplicitJetWitness` | implicit_orders |
| `funcprops.implicit_orders.ImplicitMultiplicityProof` | implicit_orders |
| `funcprops.implicit_orders.ImplicitRootValueProof` | implicit_orders |
| `funcprops.infinite_contract.PeriodicDomainWitness` | infinite-real |
| `funcprops.integration.IntegralResult` | certified_operations |
| `funcprops.meromorphic_contours.MeromorphicContourCertificate` | local-counts |
| `funcprops.metric_proofs.FiniteLipschitzProof` | finite-metric-replay |
| `funcprops.metric_proofs.JumpVariationProof` | finite-metric-replay |
| `funcprops.parameter_contract.BoxEnclosureWitness` | parameters |
| `funcprops.parameter_contract.ParameterCoverageProof` | parameters |
| `funcprops.parameter_contract.SpecializedParameterProof` | parameters |
| `funcprops.parameter_contract.UniformParameterCertificate` | parameters |
| `funcprops.parameter_contract.UniformParameterCover` | parameters |
| `funcprops.parameter_geometry.ParameterGeometryProof` | polynomial-parameter-geometry |
| `funcprops.piecewise_proofs.PiecewiseRegularityCertificate` | inequality-and-piecewise |
| `funcprops.property_contract.PropertyCoverageProof` | property-assembly |
| `funcprops.quotient_cofinal.QuotientIsolationGuarantee` | quotient-shared-orders |
| `funcprops.quotient_cofinal.QuotientIsolationRun` | quotient-shared-orders |
| `funcprops.quotient_isolation.DenominatorExclusionProof` | quotient-ledger |
| `funcprops.quotient_isolation.ExactLocalZeroProof` | quotient-ledger |
| `funcprops.quotient_isolation.QuotientContourCertificate` | quotient-ledger |
| `funcprops.quotient_isolation.QuotientIsolationProof` | quotient-ledger |
| `funcprops.quotient_isolation.QuotientIsolationState` | quotient-ledger |
| `funcprops.quotient_isolation.QuotientRegionProof` | quotient-ledger |
| `funcprops.quotient_isolation.QuotientSourceProof` | quotient-ledger |
| `funcprops.quotient_refinement.QuotientNewtonRefinement` | quotient-shared-orders |
| `funcprops.real_analysis.advanced_convexity.ConvexityCertificate` | real-property-certificates |
| `funcprops.real_analysis.complete_monotonicity.CompleteMonotonicityCertificate` | real-property-certificates |
| `funcprops.real_analysis.monotonic_certificates.MonotonicDecomposition` | real-property-certificates |
| `funcprops.real_analysis.monotonic_certificates.MonotonicPartition` | real-property-certificates |
| `funcprops.real_analysis.regularity_extensions.LipschitzResult` | finite-metric-replay |
| `funcprops.real_analysis.structural_properties.HomogeneityResult` | real-property-certificates |
| `funcprops.real_analysis.structural_properties.PeriodicityResult` | real-property-certificates |
| `funcprops.real_analysis.structural_properties.SymmetryResult` | real-property-certificates |
| `funcprops.real_analysis.variation.VariationResult` | finite-metric-replay |
| `funcprops.root_coverage.RootCoverageCertificate` | root-coverage |
| `funcprops.root_coverage.RootRegionProof` | root-coverage |
| `funcprops.root_coverage.SpecializedRootCoverage` | root-coverage |
| `funcprops.seam_regularity.SeamRegularityProof` | bounded-regularity |
| `funcprops.shared_zeros.ComplexZeroSubsetProof` | quotient-shared-orders |
| `funcprops.shared_zeros.SharedZeroImplication` | quotient-shared-orders |
| `funcprops.shared_zeros.SharedZeroOrderProof` | quotient-shared-orders |
| `funcprops.shared_zeros.SharedZeroRegion` | quotient-shared-orders |
| `funcprops.taylor_models.TaylorModel` | real-root-certificates |
| `funcprops.transcendental.complex_roots.ComplexRootIsolationResult` | complex-public |
| `funcprops.transcendental.extrema.ExtremumFamilyCertificate` | indexed-extrema |
| `funcprops.transcendental.extrema.ExtremumOrderingTheorem` | indexed-extrema |
| `funcprops.transcendental.extrema.ExtremumRange` | indexed-extrema |
| `funcprops.transcendental.roots.RootCertificate` | real-root-certificates |
| `funcprops.transcendental.roots.RootIsolationResult` | real-root-certificates |
| `funcprops.transcendental.zero_geometry.CertifiedIntegerBracket` | indexed-extrema |
| `funcprops.transcendental.zero_geometry.IndexedTailInversionCertificate` | indexed-extrema |
| `funcprops.transcendental.zero_geometry.ZeroGeometryCertificate` | indexed-extrema |
| `funcprops.transformation.ChangeOfVariablesCertificate` | transformations |
| `funcprops.transformation.DeterminantNonvanishingCertificate` | transformations |
| `funcprops.transformation.LocalInvertibilityCertificate` | transformations |
| `funcprops.verified_roots.RealRootInterval` | real-root-certificates |

## Additional coverage dimensions

The constructed-root tests compare prescribed exact roots, orders and held holes across real and algebraic routes. Consumer tests check restricted images and guarded/Piecewise assembly. Kernel mutation probes remove selected source/cover checks in temporary copies. CI adds cold/warm state, hash seeds, platforms, dependencies and installed archives. See [testing](../guides/testing.md).

## Executed premise mutation sentinels

Each baseline must pass; removing its named premise must produce one assertion failure, not a collection or import error. These are selected theorem obligations, not an exhaustive mutation proof.

| Obligation | Owning module | Sentinel |
| --- | --- | --- |
| omitted-domain | `coverage_checker.py` | [test_omitted_domain_is_rejected_even_with_recomputed_totals](../../tests/certificates/test_kernel_obligations.py) |
| overlapping-domain | `coverage_checker.py` | [test_duplicate_domain_is_rejected_even_with_recomputed_totals](../../tests/certificates/test_kernel_obligations.py) |
| source-context | `coverage_checker.py` | [test_changed_source_syntax_cannot_rebind_every_leaf](../../tests/certificates/test_kernel_obligations.py) |
| coefficient-embedding | `algebraic_coefficients.py` | [test_unique_coefficient_root](../../tests/test_proof_obligations.py) |
| owned-value | `metric_proofs.py` | [test_owned_value_with_consistent_total](../../tests/test_proof_obligations.py) |
| parameter-premise | `parameter_geometry.py` | [test_parameter_premise](../../tests/test_proof_obligations.py) |
| geometry-source | `parameter_geometry.py` | [test_geometry_source_events](../../tests/test_proof_obligations.py) |
| overlap-identity | `branch_gluing.py` | [test_anchor_is_not_identity](../../tests/test_proof_obligations.py) |
| held-transport | `work_budget.py` | [test_worker_domain_hole](../../tests/test_source_transport.py) |
