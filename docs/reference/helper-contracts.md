# Helper and proof contracts

Use the [helper reference](helpers.md) for signatures and full implementation docstrings, the [property reference](../properties/index.md) for compact queries, and the [result contracts](result-contracts.md) for shared meanings. The contracts below describe common assembly interfaces; each concrete record retains its own theorem scope.

## Scoped helper interfaces

### certify_finite_lipschitz

| Contract | Meaning |
| --- | --- |
| Accepted inputs | An exact real finite requested set (or EmptySet), a scalar Symbol compatible with every retained point, and a real-valued source on its defined points. |
| Return value | FiniteLipschitzProof or None; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | The proof checks all defined values and all pairwise secants. Its nonnegative optimal constant is zero on at most one effective point. Undefined requested points are retained as exclusions, not assigned values. |
| Failure and limits | Unresolved point collisions, inexact inputs or nonreal values decline. This constructor returns None for unsupported exact data. |

### certify_jump_variation

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A bounded exact real interval, a compatible scalar Symbol and a source defined throughout that interval, with a supported finite monotone branch decomposition. |
| Return value | JumpVariationProof or None; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | Motion on open cells and every owned cut value determine the total. Replay checks source coverage, derivatives, signs, one-sided limits and all point excursions without the variation/partition proposers. |
| Failure and limits | Unsupported domains, unproved signs, unbounded one-sided limits and source holes decline with None. |

### encode_algebraic_coefficients

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A tuple of source expressions/conditions and declared query coordinates. All remaining constants must be finite exact real algebraic values. Up to four nonrational constants, field degree at most four, and total input operation count at most 80 are supported. |
| Return value | AlgebraicCoefficientEncoding or None; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | The minimal polynomial, unique rational isolating interval, exact representations and source-preserving replacements replay without number-field discovery. |
| Failure and limits | Larger fields, extra symbolic coefficient parameters, nonreal/inexact/transcendental constants and unsupported embeddings decline with None. |

### certify_parameter_geometry

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A raw rational polynomial of degree at most four in one real root coordinate, one to four real parameters, a rational-endpoint interval and rational polynomial parameter guards. Intrinsic parameter assumptions remain premises. |
| Return value | ParameterGeometryProof; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | Counts are distinct real roots, including repeated-root and degree-loss strata. Exact sign-prefix coverage is checked. Unresolved prefixes prevent completeness. |
| Failure and limits | ValueError rejects invalid source, guards, coordinates, intervals and negative/noninteger cell budgets; NotImplementedError rejects the degree or coefficient-complexity limit. |

### resume_parameter_geometry

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A checked ParameterGeometryProof and an additional nonnegative integer cell budget. |
| Return value | A refined proof, or the original object if already complete; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | Established cells are retained, and only the checked unresolved frontier is refined. Source and parameter domain cannot be replaced. |
| Failure and limits | ValueError rejects an invalid proof or cell budget. An unresolved-guard frontier can remain partial after more work. |

### certify_branch_chart

| Contract | Meaning |
| --- | --- |
| Accepted inputs | An entire parameter-free implicit relation in two unconstrained Symbols, a valid rational CoverageRectangle and a supplied local formula. Selected logarithms use checked LogBranchChart values; supported denominators need nonzero ComplexBoxWitness records. |
| Return value | HolomorphicBranchChart; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | Replay checks local holomorphy, every source denominator, chart compatibility and the exact implicit identity. The formula denotes a selected local solution. |
| Failure and limits | ValueError rejects an unproved recipe, missing denominator witness, mismatched log chart or narrowed coordinate. |

### glue_branch_charts

| Contract | Meaning |
| --- | --- |
| Accepted inputs | Checked HolomorphicBranchChart records for one relation, requested rational rectangles and optional explicitly unresolved rectangles. |
| Return value | BranchGluingProof; a wall timeout returns an uncertified BudgetedResult. |
| Replay and completion | Every touching chart pair is represented exactly once. Equality needs log-sheet transfer or a derivative identity plus anchor. Coverage and compatible gluing have separate fields. |
| Failure and limits | ValueError rejects invalid assemblies, omitted overlaps, incompatible families or incorrect coverage. Valid disagreement/unresolved evidence returns a partial proof, not an exception. |

### monotonic_partition

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A scalar real function and a supported exact requested domain; use return_result=True to retain the structured record. |
| Return value | A compact tuple-compatible partition or MonotonicPartition. |
| Replay and completion | Coverage and local cell order do not imply global monotonicity. Owned singleton values, seams and gaps enter the global order check; derivative critical-point completeness is separate. Replay uses the bound cached construction. |
| Failure and limits | Unresolved domain, derivative or seam premises produce an incomplete record. Source-changing/foreign supplied partitions cannot establish a consumer result. |

### verify_certificate

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A registered concrete proof/summary object; optional source and coordinate restrictions must match its bound theorem. |
| Return value | Python bool. |
| Replay and completion | True validates the supplied evidence under its declared replay route. It does not imply complete coverage. False can mean unsupported or rejected evidence and never proves the mathematical negation. |
| Failure and limits | Unregistered self-attesting objects and subclasses do not select a checker. Use replay_status for diagnostic status and scope. |

### replay_status

| Contract | Meaning |
| --- | --- |
| Accepted inputs | A supplied proof/summary and optional binding arguments supported by verification. |
| Return value | ReplayStatus with supported, certified, complete, scope, reason, outcome, schema_version and factory_replay. |
| Replay and completion | Inspect completion only after successful replay, under the concrete theorem contract. Factory/backend replay dependencies differ from native premise checking. |
| Failure and limits | Unsupported replay reports certified=None. Rejected or exhausted evidence reports certified=False; this is not a mathematical counterexample. |

## Concrete replay records

The following inventory includes every registered concrete replay type, inventoried proof record and public dataclass. Nested data records require their owning checker and do not gain standalone replay from appearing here. Fields shown are constructor data, not a universal result schema. Derived properties such as coverage_complete and gluing_complete are described by the owning contract and class docstring. A record can verify while remaining incomplete. Search metadata is not automatically a theorem premise.

### funcprops.adaptive_roots.AdaptiveRootResult

Expose a real coverage proof together with its resumable search state.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `state` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/adaptive_roots.py).

### funcprops.adaptive_roots.CoverageState

Preserve disjoint accepted leaves and the exact pending real frontier.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `context` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `leaves` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `pending` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `generation` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/adaptive_roots.py).

### funcprops.adaptive_roots.CoverageTask

Retain an owned real region, source component and subdivision depth.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `support` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `depth` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/adaptive_roots.py).

### funcprops.algebraic_coefficients.AlgebraicCoefficientEncoding

Represent a bounded real number field by its minimal polynomial and root interval.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `inputs` | `required` | Original expressions and restrictions bound to the encoding. |
| `variables` | `required` | Declared query coordinates. |
| `generator` | `required` | Auxiliary real algebraic coordinate. |
| `root` | `required` | Selected exact root or algebraic embedding under this concrete theorem. |
| `polynomial` | `required` | Rational polynomial constraining the auxiliary generator or local source. |
| `interval` | `required` | Exact interval supporting this local claim or root selection. |
| `representations` | `required` | Exact coefficient formulas in the selected generator. |
| `transformed` | `required` | Source-preserving auxiliary expressions. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/algebraic_coefficients.py).

### funcprops.algebraic_complex.AlgebraicComplexRootProof

Adapt exact algebraic enumeration to source-preserving complex root coverage.

Replay contract: `backend-adapter`; mode: `algroots-exact-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `condition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `system` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `representation` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `decisions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `roots` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `multiplicities` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `obligations` | `('unresolved-algebraic-backend',)` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_auxiliary_variables` | `8` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_quotient_dimension` | `256` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `backend` | `algroots-exact-rur` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/algebraic_complex.py).

### funcprops.algebraic_complex.AlgebraicRootDecision

Record whether an algebraic candidate satisfies source, domain and branch guards.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `disposition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `multiplicity` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/algebraic_complex.py).

### funcprops.analytic_contours.AnalyticComplexCoverage

Assemble certified contour counts over an exact complex rectangle cover.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `regions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/analytic_contours.py).

### funcprops.analytic_contours.AnalyticContourCertificate

Bind an entire-function winding count to a rectangle and image witnesses.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `knots` | `(0, 1, 2, 3, 4)` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `images` | `(None, None, None, None)` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `vertices` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_count` | `None` | Local zero count under this concrete contour/root theorem. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/analytic_contours.py).

### funcprops.analytic_contours.ComplexBoxWitness

Enclose an entire function's image on a complex boundary segment.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `box` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `bounds` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/analytic_contours.py).

### funcprops.assumption_closure.AssumptionClosure

Retain assumptions and the additional facts they entail.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `original` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `facts` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `condition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/assumption_closure.py).

### funcprops.assumptions.PropertyDecision

Pair a property conclusion with its condition and provenance.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `predicate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `verdict` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `knowledge` | `PropertyKnowledge.EXACT` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `provenance` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `reasons` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/assumptions.py).

### funcprops.assumptions.PropertyProvenance

Identify the assumptions or theorem supporting a property decision.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `reference` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `note` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/assumptions.py).

### funcprops.asymptotic_tails.TailSignCertificate

Bind a tail sign to exact source data and dominance inequalities.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `threshold` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `sign` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `dominance` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/asymptotic_tails.py).

### funcprops.branch_atlas.GluedPowerProof

Bind a selected power to compatible logarithm-chart transitions.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `atlas` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exponent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_atlas.py).

### funcprops.branch_atlas.LogAtlasProof

Check rectangle coverage, overlap transitions and logarithm gluing obstructions.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `charts` | `required` | Supplied local chart records bound to this assembly. |
| `transitions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `gluing_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_atlas.py).

### funcprops.branch_atlas.LogBranchChart

Define a logarithm on a rectangle whose base image lies in a rotated half-plane.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `enclosure` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `phase` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `sheet` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_atlas.py).

### funcprops.branch_atlas.LogChartTransition

Record the exact integer sheet difference on a chart overlap.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `turns` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_atlas.py).

### funcprops.branch_atlas._Replay

See the owning module for this concrete theorem.

Replay contract: `witness-kernel`; mode: `unsupported-unified-replay`.

Constructor data and derived fields are documented by the class and its owning interface.

Available status/check interfaces: `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_atlas.py).

### funcprops.branch_gluing.BranchGluingProof

Cover a requested region and check every local-germ overlap for one relation.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `relation` | `required` | Entire implicit equation defining the local branch family. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `value_symbol` | `required` | Dependent coordinate in the implicit relation. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `charts` | `required` | Supplied local chart records bound to this assembly. |
| `overlaps` | `required` | Every required touching overlap and its equality/disagreement status. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |

Available status/check interfaces: `complete`, `coverage_complete`, `gluing_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_gluing.py).

### funcprops.branch_gluing.BranchOverlapProof

Prove equality or disagreement of two local germs, or retain an unresolved overlap.

Replay contract: `witness-kernel`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `anchor` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `status` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `turns` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_gluing.py).

### funcprops.branch_gluing.HolomorphicBranchChart

Select a holomorphic solution of an entire implicit relation on a rectangle.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `relation` | `required` | Entire implicit equation defining the local branch family. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `value_symbol` | `required` | Dependent coordinate in the implicit relation. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `formula` | `required` | Supplied local recipe before selected logarithms are substituted. |
| `logarithms` | `()` | Placeholder/selected-logarithm chart pairs. |
| `units` | `()` | Source-bound zero-exclusion witnesses for supported denominators. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/branch_gluing.py).

### funcprops.certified_balls.RealBallCertificate

Bound a real expression by outward rational arithmetic.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `backend` | `outward-interval` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_balls.py).

### funcprops.certified_inequalities.InequalityCertificate

Bind a real inequality to its expression, domain and sufficient theorem.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `relation` | `required` | Entire implicit equation defining the local branch family. |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `None` | Route-specific witnesses; their presence alone is not successful replay. |
| `source_expression` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_inequalities.py).

### funcprops.certified_inequalities._FiniteSignCertificate

_FiniteSignCertificate(expression: 'sp.Expr', variable: 'sp.Symbol', domain: 'sp.FiniteSet', relation: 'str')

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `relation` | `required` | Entire implicit equation defining the local branch family. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_inequalities.py).

### funcprops.certified_operations.ArgumentPrincipleResult

Record a contour's zero, pole and winding counts with its evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `contour` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zeros_minus_poles` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certified` | `required` | Stored or derived certification status, meaningful under the replay contract. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.ContinuationCertificate

Record an analytic continuation path and its selected branch data.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `contour` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `continued` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `substitutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.ContourDeformationCertificate

Bind a contour deformation to geometric and analytic premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `first` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `second` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `punctures` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.EquationSolutionCertificate

Bind a solution set to source definition and exhaustive equation evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `solutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `effective_domain` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.HomotopyCertificate

Certificate for based-loop homotopy in a finitely punctured plane.

``word`` is the signed crossing word for a certified system of pairwise disjoint parallel cuts from the punctures to infinity.  ``reduced_word`` is its free reduction.  Equality of reduced words is the complete invariant for based loops in ``C \ punctures``.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `first` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `second` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `punctures` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cut_direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `first_word` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `second_word` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `reduced_word` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.InverseCertificate

Bind an inverse formula to domain, image and two-sided identity premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inverse` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `image` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.LaurentCertificate

Record a checked local Laurent expansion with branch and order premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `series` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_context` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.ResidueCertificate

Bind a residue to a checked local expansion or exact order theorem.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `residue` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_context` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.SingularityClassificationCertificate

Bind a local singularity kind to source definition and isolated order data.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_context` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations.WindingCertificate

Bind an integer winding to a supported closed nonvanishing path.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `contour` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `winding` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `integral` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_operations._ReplayedOperation

See the owning module for this concrete theorem.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

Constructor data and derived fields are documented by the class and its owning interface.

Available status/check interfaces: `complete`, `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_operations.py).

### funcprops.certified_optimization.GlobalMinimumCertificate

Bind a minimum value, location and uniqueness to sufficient global premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unique` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `coercive` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `component_result` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/certified_optimization.py).

### funcprops.complex_certification.ArgumentPrincipleCertificate

Store a contour count with its route-specific boundary premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `lower_left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper_right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `polynomial-argument-principle` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_certification.py).

### funcprops.complex_certification.RectangleRoucheCertificate

Bind a polynomial rectangle count to Rouché boundary bounds.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `lower_left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper_right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `dominant` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `polynomial-rectangle-rouche` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_certification.py).

### funcprops.complex_certification.RoucheCertificate

Bind a polynomial disk count to a strict Rouché inequality.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `f` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `g` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `var` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `radius` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `polynomial-circle-rouche` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_certification.py).

### funcprops.complex_clusters.ComplexClusterCertificate

Count zeros with multiplicity in a supported analytic disk.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `radius` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outer_radius` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coefficients` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coefficient_bounds` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `majorant_bound` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `remainder` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_count` | `None` | Local zero count under this concrete contour/root theorem. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_clusters.py).

### funcprops.complex_cofinal.ComplexIsolationGuarantee

State the checked hypotheses for conditional simple-root completion.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `run` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem` | `compact-simple-entire-cofinal` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_cofinal.py).

### funcprops.complex_cofinal.ComplexIsolationRun

Retain the frontier, policy and fair-search index of a complex isolation run.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `state` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_policy` | `factory` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `next_stage` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_boundary_depth` | `14` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `use_newton` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `use_multiple` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `protocol` | `dovetail-prefix-precision` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_cofinal.py).

### funcprops.complex_coverage.ComplexRootCoverage

Assemble counted and unresolved regions of a complex root query.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `regions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `root_count` | `None` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_coverage.py).

### funcprops.complex_coverage.ComplexRootRegionProof

Bind a rectangle's root count to its declared complex evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `required` | Count with multiplicity when established. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_coverage.py).

### funcprops.complex_coverage.CoverageRectangle

Represent a rational closed rectangle by opposite complex corners.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `lower_left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper_right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_coverage.py).

### funcprops.complex_isolation.ComplexIsolationProof

Bind isolated roots, clusters and unresolved regions to an exact rectangle cover.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outer` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_regions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_regions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `clusters` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `max_box_width` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coverage_complete` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `isolation_complete` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `accuracy_complete` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `distinct_root_count` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |
| `max_box_diameter` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_isolation.py).

### funcprops.complex_isolation.ComplexIsolationState

Preserve a complex proof and its exact pending frontier for resumption.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `proof` | `required` | Underlying proof that must agree with this public summary. |
| `pending` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `generation` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_isolation.py).

### funcprops.complex_isolation.ComplexIsolationTask

Retain an owned subdivision region, path and retry effort.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `path` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `attempt` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_isolation.py).

### funcprops.complex_multiplicity.ComplexExactMultiplicity

Prove an exact root location and multiplicity from Taylor data.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `multiplicity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `jets` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `taylor` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_multiplicity.ComplexLocatedRegion

Transfer a counted region using an exact certified root location.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_multiplicity.ComplexPowerFactorProof

Relate complex zero orders to a power and an analytic unit.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `multiplicity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unit` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unit_witness` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_multiplicity.ComplexPowerRootRegion

Isolate one multiple zero through its checked power-factor base.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `factorization` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_multiplicity.ComplexTaylorWitness

Enclose exact Taylor coefficients at a specified complex point.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coefficients` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_multiplicity.ComplexUnitWitness

Prove a complex analytic factor nonzero throughout a rectangle.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `enclosure` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_multiplicity._CountRecord

See the owning module for this concrete theorem.

Replay contract: `witness-kernel`; mode: `unsupported-unified-replay`.

Constructor data and derived fields are documented by the class and its owning interface.

Available status/check interfaces: `complete`, `certified`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_multiplicity.py).

### funcprops.complex_newton.ComplexDerivativeWitness

Enclose the complex derivative on a rational rectangle.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `box` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `bounds` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `1` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_newton.py).

### funcprops.complex_newton.ComplexNewtonRefinement

Bind a Krawczyk contraction to its parent, child and four complements.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center_derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inverse` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `residual` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `image` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `contraction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `child_rectangle` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `2` | Recorded search work; it is not proof of coverage. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_newton.py).

### funcprops.complex_newton.ComplexNewtonRegion

Transfer a parent's count to a checked Newton child or complement.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `refinement` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `index` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/complex_newton.py).

### funcprops.component_optimization.ComponentMinimumResult

Combine finite-component minimum candidates and attainment data.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain_record` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `infimum` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `minimizers` | `EmptySet` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `candidates` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/component_optimization.py).

### funcprops.component_optimization.OptimizationCandidate

Record a component endpoint, limit or stationary value candidate.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `attained` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `component` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/component_optimization.py).

### funcprops.coverage_contract.CellDomainWitness

Full requested-cell definition from raw-source outward evaluations.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `cells` | `required` | Certified local cells; their union and ownership are separate obligations. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.CheckResult

Report replay validity separately from exhaustive coverage and its reason.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `outcome` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certified` | `required` | Stored or derived certification status, meaningful under the replay contract. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.CoverageContext

Bind a real root query to its source, domains, assumptions and branch premises.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `effective` | `required` | Source-defined subset of the requested domain. |
| `domain_record` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parameter_guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `substitutions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_context` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.CoverageLeaf

Bind a local real root count to a theorem, region and witness.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `context` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `required` | Count with multiplicity when established. |
| `witness` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `roots` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.CoverageProof

Assemble local counts and unresolved regions over an effective real domain.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `context` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `leaves` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `EmptySet` | Regions or obligations with no exhaustive conclusion. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `root_count` | `None` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.EnclosureWitness

Bound the source image on one real cell by exact rational endpoints.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `grammar_version` | `1` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_context` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.InadmissibleProof

A real-valued query whose exact constant source is nonreal.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `reason` | `nonreal-constant-source` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.LocatedSubsetWitness

Locate a parent's unique root and retain its excluded complement.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `locator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.MonotoneWitness

Store derivative and endpoint bounds for a monotone root count.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.NewtonWitness

Store the midpoint, interval derivative and checked real Newton image.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `midpoint` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `image_lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `image_upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.PowerFactorWitness

Relate root multiplicity to a power factor and a nonvanishing unit.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `base` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exponent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unit` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_proof` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unit_bound` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.RationalWitness

Bind a rational function to exact numerator and denominator coefficients.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `numerator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `denominator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.SourceFormulaWitness

Bind a local count to an exact source-formula proof.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `proof` | `required` | Underlying proof that must agree with this public summary. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.TaylorDeflationWitness

Prove an exact root order from jets and a bounded Taylor remainder.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `jets` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unit_lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unit_upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.TaylorWitness

Store a Taylor polynomial and outward Lagrange remainder bounds.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coefficients` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `polynomial` | `required` | Rational polynomial constraining the auxiliary generator or local source. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `polynomial_bound` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `remainder_lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `remainder_upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.coverage_contract.ZeroSubsetWitness

Transfer a zero count from a checked parent to a subset.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/coverage_contract.py).

### funcprops.derivative_inequalities.DerivativeChainCertificate

Prove a derivative sign by induction from endpoint data.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `depth` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `endpoint` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_certificate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/derivative_inequalities.py).

### funcprops.diagnostics.ReplayStatus

Replay outcome, separately from declared coverage or record presence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `supported` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certified` | `required` | Stored or derived certification status, meaningful under the replay contract. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `scope` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outcome` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `None` | Record schema identifier; a matching number is not a proof. |
| `factory_replay` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `scope`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/diagnostics.py).

### funcprops.domain_tracking.DomainRecord

Preserve requested, natural and effective domains with raw source restrictions.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `natural` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `effective` | `required` | Source-defined subset of the requested domain. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `exclusions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `natural_complete` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/domain_tracking.py).

### funcprops.enclosure_policy.EnclosurePolicy

Bound precision refinement, subdivision, series work and elapsed time.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `precision` | `30` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_precision` | `240` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_refinements` | `3` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_depth` | `10` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_cells` | `1024` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_taylor_order` | `2` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `seconds` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/enclosure_policy.py).

### funcprops.enclosures.DerivativeEnclosure

Bind derivative bounds to the original source and regularity premises.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `enclosure` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `regularity_precision` | `30` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/enclosures.py).

### funcprops.enclosures.EnclosureResult

Intersect checked value enclosures and retain unresolved arithmetic obligations.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `witnesses` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outcome` | `CheckOutcome.UNSUPPORTED` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/enclosures.py).

### funcprops.entire_cancellation.EntireCancellationProof

Prove an entire composition by an everywhere convergent even series.

cos(sqrt(w)) and cosh(sqrt(w)) have series in integer powers of w with infinite radius. The squared odd templates follow from the double-angle identities. Composing with an entire inner source preserves this property.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `inner` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `template` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/entire_cancellation.py).

### funcprops.explanations.ResultExplanation

Present a query's value, cases, evidence and unresolved obligations.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `conclusion` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `route` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `established` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/explanations.py).

### funcprops.extrema_bounds.ExtremaBoundsProof

Bind infimum/supremum brackets to component and critical-root evidence.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `domain_record` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tolerance` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `pieces` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `minimum_bounds` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `maximum_bounds` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `accuracy_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/extrema_bounds.py).

### funcprops.geometry.BoundaryBehavior

Describe limits at the boundary of an effective source domain.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `limits` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).

### funcprops.geometry.BoundaryLimit

Record a one-sided endpoint limit and its owned source boundary.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `endpoint` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certified` | `required` | Stored or derived certification status, meaningful under the replay contract. |
| `source` | `symbolic-limit` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).

### funcprops.geometry.FunctionGeometry

Combine boundary, level-boundedness and mode-existence conclusions.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variables` | `required` | Declared query coordinates. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `continuity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `ck_order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `c2` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `analytic` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `convexity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `singularities` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `boundary_behavior` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `level_boundedness` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `minimum_exists` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `maximum_exists` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).

### funcprops.geometry.LevelBoundednessCertificate

Record sufficient level-boundedness premises on a source domain.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `boundary_behavior` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variables` | `()` | Declared query coordinates. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).

### funcprops.geometry.ModeExistenceCertificate

Bind existence of a maximum to boundedness and boundary behavior.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `sense` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exists` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `continuity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `level_boundedness` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_closed` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variables` | `()` | Declared query coordinates. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).

### funcprops.global_analysis.GlobalInequalityCertificate

Combine a compact inequality proof with rigorous tail bounds.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `relation` | `required` | Entire implicit equation defining the local branch family. |
| `core` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `core_certificate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_tail` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_tail` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |

Available status/check interfaces: `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/global_analysis.py).

### funcprops.global_multivariate.ComposedMapCertificate

Transport checked global mapping properties through a composition.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `components` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `composition-of-certified-maps` | Route identifier or source-context record; consult this type's docstring. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/global_multivariate.py).

### funcprops.global_multivariate.GlobalMapCertificate

Record global affine mapping properties under coefficient and rank premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `expressions` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `None` | Declared query coordinates. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/global_multivariate.py).

### funcprops.guarded_affine.AffineContourCount

Record a guarded affine contour count and its divisor data.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `admissible` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/guarded_affine.py).

### funcprops.guarded_affine.AffineSolution

Represent an affine equation's solution under a parameter guard.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `solutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/guarded_affine.py).

### funcprops.guarded_affine.GuardedAffineContourCertificate

Assemble affine contour counts under explicit parameter conditions.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `contour` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/guarded_affine.py).

### funcprops.guarded_affine.GuardedAffineEquationCertificate

Bind exhaustive affine solution cases to real-coefficient premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/guarded_affine.py).

### funcprops.implicit_orders.CommonZeroProof

Relate two implicit roots with explicit shared-value and order evidence.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `base_region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `orders` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/implicit_orders.py).

### funcprops.implicit_orders.ImplicitJetWitness

Enclose an analytic derivative jet on a whole complex root box.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `box` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coefficients` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/implicit_orders.py).

### funcprops.implicit_orders.ImplicitMultiplicityProof

Prove an implicit root's order using zero jets and a nonzero leading jet.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `base_region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_jets` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `taylor` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |
| `leading_value` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `coverage_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/implicit_orders.py).

### funcprops.implicit_orders.ImplicitRootValueProof

Prove a value at an implicit root through exact analytic congruence identities.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `base_region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `quotient` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `children` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `power` | `1` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/implicit_orders.py).

### funcprops.implicit_orders._Local

See the owning module for this concrete theorem.

Replay contract: `witness-kernel`; mode: `unsupported-unified-replay`.

Constructor data and derived fields are documented by the class and its owning interface.

Available status/check interfaces: `complete`, `coverage_complete`, `certified`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/implicit_orders.py).

### funcprops.infinite_contract.CoveredRootFamily

Represent an exhaustive indexed family with multiplicities and index bounds.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `offset` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `period` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `multiplicity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `ranges` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_contract.py).

### funcprops.infinite_contract.ExponentialTailWitness

Prove eventual root exclusion for a supported exponential-polynomial tail.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `threshold` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `sign` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `groups` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coefficient_bounds` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `constant_lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `remainder_upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_contract.py).

### funcprops.infinite_contract.IndexRangeWitness

Bind an indexed root family to its owned domain range.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_contract.py).

### funcprops.infinite_contract.IntegerEndpointWitness

Decide an exact lattice endpoint comparison.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `quotient` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `floor` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `enclosure` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_contract.py).

### funcprops.infinite_contract.PeriodicDomainWitness

Preserve source exclusions under a periodic rational-trigonometric substitution.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `effective` | `required` | Source-defined subset of the requested domain. |
| `excluded` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `rate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `phase` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `numerator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `denominator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guards` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `poles` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_contract.py).

### funcprops.infinite_contract.PeriodicRootWitness

Bind rational-trigonometric zeros to exhaustive periodic families.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `levels` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `families` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_function` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_contract.py).

### funcprops.infinite_root_families.IndexedRootFamily

Describe a root formula, index set, multiplicities and support premises.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `formula` | `required` | Supplied local recipe before selected logarithms are substituted. |
| `index` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `index_domain` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `simple` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `multiplicity` | `1` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/infinite_root_families.py).

### funcprops.integration.IntegralResult

Pair an integral value or enclosure with its path and certification data.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `path` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `certified` | `required` | Stored or derived certification status, meaningful under the replay contract. |
| `error_bound` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/integration.py).

### funcprops.integration.ParametricContour

Oriented contour ``gamma(t)``, ``a <= t <= b``.

The parameterization is retained: reversing the parameter interval reverses orientation even when the geometric image is unchanged.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `gamma` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parameter` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/integration.py).

### funcprops.local_branches.LocalBranchContext

Choose log(base(point)) explicitly for selected Log/power bases.

``logarithms`` is a tuple of (source base expression, chosen log value). exp(value)=base(point) must be proved exactly. All entries must be used. The resulting theorem concerns this analytic germ, not the principal expression throughout a neighborhood crossing its old cut.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `logarithms` | `required` | Placeholder/selected-logarithm chart pairs. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/local_branches.py).

### funcprops.meromorphic_contours.MeromorphicContourCertificate

Record zeros, poles and winding of a source-preserving quotient.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `lower_left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper_right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zeros` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `poles` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `winding` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `rational-argument-principle` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/meromorphic_contours.py).

### funcprops.metric_proofs.FiniteLipschitzProof

Bind an optimal pairwise constant to all defined points of a finite query.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `effective` | `required` | Source-defined subset of the requested domain. |
| `values` | `required` | Exact values at every retained finite source point. |
| `ratios` | `required` | All retained finite pairwise secant slopes. |
| `constant` | `required` | The claimed metric constant; optimality requires its own theorem. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/metric_proofs.py).

### funcprops.metric_proofs.JumpVariationProof

Cover a bounded interval by monotone motions and all owned point values.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `cells` | `required` | Certified local cells; their union and ownership are separate obligations. |
| `points` | `required` | Every retained owned coordinate/value pair, in the checked order. |
| `total_variation` | `required` | Claimed sum of certified motion and all owned excursions. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/metric_proofs.py).

### funcprops.metric_proofs.VariationMotion

Store a C1 monotone formula and its two limits on an open interval.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `interval` | `required` | Exact interval supporting this local claim or root selection. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variation` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/metric_proofs.py).

### funcprops.multivariate_intervals.KrawczykBoxCertificate

Bind a multivariate polynomial root box to a checked contraction.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `required` | Declared query coordinates. |
| `box` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `unique` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `interval-krawczyk` | Route identifier or source-context record; consult this type's docstring. |
| `enclosure` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/multivariate_intervals.py).

### funcprops.parameter_contract.BoxEnclosureWitness

Enclose an expression over a real coordinate/parameter box.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `domains` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_series_terms` | `4096` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.ExponentialParameterWitness

Count a supported exponential family on a parameter stratum.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `phase` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `scale` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `offset` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.MonotoneParameterWitness

Prove a uniform monotone root count under a parameter guard.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `base` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.ParameterCoverageProof

Assemble guarded root counts over exhaustive parameter strata.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `parameter` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `parameter_domain` | `required` | Explicit guard restricting the parameter family. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cells` | `()` | Certified local cells; their union and ownership are separate obligations. |
| `unresolved` | `EmptySet` | Regions or obligations with no exhaustive conclusion. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.ParameterRootCell

Record one guarded parameter cell and its root count witness.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `required` | Count with multiplicity when established. |
| `witness` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.PolynomialParameterWitness

Count polynomial roots under a checked parameter condition.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `signs` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.PolynomialSignWitness

Prove a polynomial coefficient or discriminant sign on a stratum.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `coefficients` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `sample` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `sign` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.SpecializedParameterProof

Bind a parameter proof to exact substitutions satisfying its guard.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.UniformParameterCertificate

Bind a uniform root count to parameter and coordinate premises.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `parameter_domains` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_count` | `None` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `witness` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.UniformParameterCover

Assemble a complete coordinate cover over a parameter box.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `parameter_domains` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `leaves` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `EmptySet` | Regions or obligations with no exhaustive conclusion. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `root_count` | `None` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.UniformParameterWitness

Prove a root count uniformly across a parameter box.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_contract.UniformZeroSubsetWitness

Transfer uniform root exclusion to a subset.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_contract.py).

### funcprops.parameter_discriminants.ParameterTransitionLocus

Record a polynomial family's exceptional parameter locus.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `parameters` | `required` | Parameter coordinates, including their intrinsic assumptions. |
| `locus` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_discriminants.py).

### funcprops.parameter_discriminants.TranscendentalDiscriminant

Describe parameter transitions for a supported transcendental family.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `condition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `transition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_discriminants.py).

### funcprops.parameter_geometry.ParameterGeometryCell

A constant distinct-root count or a proved empty parameter region.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_count` | `None` | Distinct-root count when established, separate from multiplicity. |
| `empty` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_geometry.py).

### funcprops.parameter_geometry.ParameterGeometryProof

Bind a multi-parameter root-count partition and its unresolved sign trees.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `parameters` | `required` | Parameter coordinates, including their intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `parameter_domain` | `required` | Explicit guard restricting the parameter family. |
| `events` | `()` | Bound polynomial coefficients and exact trace/discriminant event data. |
| `cells` | `()` | Certified local cells; their union and ownership are separate obligations. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_geometry.py).

### funcprops.parameter_geometry.ParameterGeometryRegion

A prefix of the exact sign/endpoint partition on a fixed-degree stratum.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `degree` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `choices` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/parameter_geometry.py).

### funcprops.piecewise_proofs.PiecewiseRegularityCertificate

Assemble branch regularity and first-match seam evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `cells` | `required` | Certified local cells; their union and ownership are separate obligations. |
| `seams` | `required` | Owned branch-boundary and one-sided data. |
| `domain_record` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `order` | `1` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/piecewise_proofs.py).

### funcprops.proof_budget.ProofBudget

Limit symbolic proof routes by effort and expression size.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `max_cost` | `100` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `spent` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `attempted` | `factory` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `skipped` | `factory` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/proof_budget.py).

### funcprops.proof_explanations.ProofExplanation

Summarize a proof's scope, premises, replay outcome and unresolved work.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `conclusion` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem_ids` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `routes` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `established` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `completeness` | `Completeness.UNKNOWN` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certificate_status` | `not-recorded` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/proof_explanations.py).

### funcprops.proof_telemetry.ProofTelemetry

Collect proof-route observations without changing their conclusions.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `enabled` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `observations` | `factory` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/proof_telemetry.py).

### funcprops.proof_telemetry.RouteObservation

Record the outcome and effort of one attempted proof route.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `route` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `estimated_cost` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `elapsed` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outcome` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cache_hit` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/proof_telemetry.py).

### funcprops.property_composition.CompositionFact

Record a property transported through a supported composition rule.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `property` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem_id` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `True` | Stored completion claim; its theorem premises still require replay. |
| `bound` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/property_composition.py).

### funcprops.property_contract.PropertyConclusion

Store an assembled mathematical value and its proof status.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `name` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `obligations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/property_contract.py).

### funcprops.property_contract.PropertyCoverageProof

Bind property conclusions to source domains, root coverage and value bounds.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested` | `required` | Original requested set or rectangle cover. |
| `domain_record` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `pieces` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `candidate_order` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `comparisons` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conclusions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/property_contract.py).

### funcprops.property_contract.PropertyPiece

Record a supported property conclusion on an owned domain component.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `critical_coverage` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `critical_points` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_coverage` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_points` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative_samples` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `sign_samples` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/property_contract.py).

### funcprops.quotient_cofinal.QuotientIsolationGuarantee

State conditional completion premises for separated simple quotient divisors.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `run` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem` | `compact-simple-separated-quotient-cofinal` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_cofinal.py).

### funcprops.quotient_cofinal.QuotientIsolationRun

Retain the frontier and fair-search policy for a quotient zero/pole ledger.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `state` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_policy` | `factory` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `next_stage` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_boundary_depth` | `14` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `use_newton` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `use_multiple` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `protocol` | `dovetail-prefix-precision` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_cofinal.py).

### funcprops.quotient_isolation.DenominatorExclusionProof

Prove that a quotient denominator and its source guards stay nonzero.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `contour` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.ExactLocalZeroProof

Exact vanishing jets plus an exhaustive local count locate all its zeros.

If the count is m and the first m jets vanish at c, the analytic order is at least m. The finite count then proves exact order m and no other zero.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `jets` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.QuotientCellProof

Account for source zeros, extension zeros and poles on one checked cell.

Replay contract: `witness-kernel`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `numerator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `denominator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exclusions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `numerator_location` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `denominator_location` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `excluded_guard` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard_cofactor` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |
| `guard_zero` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.QuotientContourCertificate

Divisor counts of the extension; original-source zeros stay explicit.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `proof` | `required` | Underlying proof that must agree with this public summary. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.QuotientIsolationProof

Assemble a source-preserving zero/pole ledger over a rectangle.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate_assumptions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `outer` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cells` | `()` | Certified local cells; their union and ownership are separate obligations. |
| `unresolved` | `()` | Regions or obligations with no exhaustive conclusion. |
| `max_box_width` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `max_box_diameter` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exhaustion` | `None` | Resource limit or unresolved-obligation reason. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |
| `refinements` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.QuotientIsolationState

Retain a quotient proof and every pending subdivision task.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `proof` | `required` | Underlying proof that must agree with this public summary. |
| `pending` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `generation` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.QuotientRegionProof

Bind a local quotient divisor conclusion to count and shared-order proofs.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `cell` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `zero` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |
| `guard_contours` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_isolation.QuotientSourceProof

Bind an entire numerator/denominator representation to original source guards.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `numerator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `denominator` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `common` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guards` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_syntax` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_isolation.py).

### funcprops.quotient_refinement.QuotientNewtonRefinement

Refine a joint zero/pole cell while retaining source guards and counts.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `refinement` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cells` | `required` | Certified local cells; their union and ownership are separate obligations. |
| `guard_contours` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `tested` | `0` | Recorded search work; it is not proof of coverage. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/quotient_refinement.py).

### funcprops.real_analysis.advanced_convexity.ConvexityCertificate

Bind a curvature classification to its route and optional uniform modulus.

Box-Hessian records retain source/C2 and entry-bound data. Other methods use their declared scalar or factory replay routes.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `method` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `modulus` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `proof` | `()` | Underlying proof that must agree with this public summary. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/advanced_convexity.py).

### funcprops.real_analysis.complete_monotonicity.CompleteMonotonicityCertificate

Bind alternating derivative signs to a supported sufficient theorem.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `insufficient-evidence` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/complete_monotonicity.py).

### funcprops.real_analysis.integrability.IntegrabilityResult

Distinguish supported integral notions and their values or obstructions.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `riemann` | `TruthValue.UNKNOWN` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `locally_integrable` | `TruthValue.UNKNOWN` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `absolutely_integrable` | `TruthValue.UNKNOWN` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `improper_integrable` | `TruthValue.UNKNOWN` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `integral` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `absolute_integral` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `exceptional_loci` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/integrability.py).

### funcprops.real_analysis.monotonic_certificates.IndexedMonotonicPartition

Describe an indexed monotonic pattern between a certified root family.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `boundary_geometry` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `direction_pattern` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `first_direction` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `indexed-derivative-zero-geometry` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.monotonic_certificates.InverseSolutionCertificate

Bind inverse solutions to an owned monotonic partition.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `equation` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `solutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `partition` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `monotonic-partition-inverse` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `isolated_intervals` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.monotonic_certificates.MonotonicDecomposition

Retain monotone intervals, critical points and source-domain evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `inner` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outer` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `condition` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inverse` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `strict` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `continuous` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `structural-monotonic-decomposition` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.monotonic_certificates.MonotonicInterval

Record one owned interval's direction and derivative evidence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `interval` | `required` | Exact interval supporting this local claim or root selection. |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_limit` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_limit` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `strict` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `continuous` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_attained` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_attained` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.monotonic_certificates.MonotonicPartition

Assemble monotonic cells with endpoint and boundary geometry.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `cells` | `()` | Certified local cells; their union and ownership are separate obligations. |
| `indexed` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `source` | `monotonic-partition` | Route identifier or source-context record; consult this type's docstring. |
| `derivative` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `critical_points` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `property_decomposition` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `critical_points_complete` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `None` | Analysis coordinate and its intrinsic assumptions. |
| `points` | `()` | Every retained owned coordinate/value pair, in the checked order. |
| `seams` | `()` | Owned branch-boundary and one-sided data. |
| `branch_partitions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.monotonic_certificates.NonMonotonicityWitness

Exhibit source points whose values violate the claimed global order.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `points` | `required` | Every retained owned coordinate/value pair, in the checked order. |
| `values` | `required` | Exact values at every retained finite source point. |
| `exact` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `exact-sample-ordering-witness` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.monotonic_certificates.PartitionRange

Assemble component images with exact endpoint attainment data.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `image` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `partition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `monotonic-partition-range` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonic_certificates.py).

### funcprops.real_analysis.oscillation.OscillationCertificate

Bind an oscillation classification to domain and zero-family evidence.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `partition` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `turning_count` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/oscillation.py).

### funcprops.real_analysis.piecewise.PiecewiseBoundary

A finite seam between two effective branch cells.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `point` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_branch` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_branch` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `owner_branch` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/piecewise.py).

### funcprops.real_analysis.piecewise.PiecewiseBoundaryCertificate

Certified local data at one Piecewise seam.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `boundary` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_limit` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_limit` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative_limits` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `continuous` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `differentiability_order` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/piecewise.py).

### funcprops.real_analysis.piecewise.PiecewiseBranch

One connected effective branch cell.

``source_index`` identifies the original Piecewise arm.  ``condition`` is the normalized *effective* condition after excluding all earlier arms. ``domain`` is the corresponding real set/cell when it can be represented.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `condition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `source_index` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_condition` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/piecewise.py).

### funcprops.real_analysis.piecewise.PiecewiseDecomposition

Effective ordered branch cells and their finite boundaries.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `requested_domain` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branches` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `boundaries` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/piecewise.py).

### funcprops.real_analysis.regularity_extensions.HolderRegularityResult

Record a Hölder exponent, constant and sufficient domain premises.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `exponent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `constant` | `None` | The claimed metric constant; optimality requires its own theorem. |
| `optimal` | `TruthValue.UNKNOWN` | Whether the supported optimality claim is proved; separate from replay support. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/regularity_extensions.py).

### funcprops.real_analysis.regularity_extensions.LipschitzResult

Record a Lipschitz classification, constant and source-domain evidence.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `constant` | `None` | The claimed metric constant; optimality requires its own theorem. |
| `optimal` | `TruthValue.UNKNOWN` | Whether the supported optimality claim is proved; separate from replay support. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `proof` | `None` | Underlying proof that must agree with this public summary. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/regularity_extensions.py).

### funcprops.real_analysis.smoothness.SmoothnessResult

Certified regularity information on a requested real domain.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `continuity` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `differentiability_order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `smooth` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `analytic` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exceptional_loci` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/smoothness.py).

### funcprops.real_analysis.special_functions.DLMFFact

Record a sourced special-function theorem and its executable parameter guard.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `property` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `section` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `url` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `status` | `direct` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `note` | `` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/special_functions.py).

### funcprops.real_analysis.structural_properties.HomogeneityResult

Retain scaling classification, inferred/requested degree and guarded cases.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `degree` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `()` | Declared query coordinates. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `weights` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `requested_degree` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/structural_properties.py).

### funcprops.real_analysis.structural_properties.PeriodicityResult

Retain a periodicity classification, period and supporting guarded cases.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `period` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `fundamental` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `None` | Stored completion claim; its theorem premises still require replay. |
| `certified` | `None` | Stored or derived certification status, meaningful under the replay contract. |

Available status/check interfaces: `complete`, `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/structural_properties.py).

### funcprops.real_analysis.structural_properties.SymmetryResult

Retain a symmetry classification, center and identity evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center` | `0` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `centers` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center_period` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `central_value` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `center_families` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `None` | Stored completion claim; its theorem premises still require replay. |
| `certified` | `None` | Stored or derived certification status, meaningful under the replay contract. |
| `query_center` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/structural_properties.py).

### funcprops.real_analysis.variation.VariationResult

Record total variation, including owned Piecewise jumps and endpoint values.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `bounded_variation` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `total_variation` | `required` | Claimed sum of certified motion and all owned excursions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `proof` | `None` | Underlying proof that must agree with this public summary. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/variation.py).

### funcprops.registry.ArgumentPattern

Match one positional argument using native type, sign or literal premises.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `name` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `kind` | `any` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `predicates` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `choices` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry.py).

### funcprops.registry.Family

Group property rules for a supported symbolic function family.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `raw` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry.py).

### funcprops.registry.InstantiatedPropertyRule

A native registry theorem instantiated for one concrete function call.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rule` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `subject` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `result` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `substitutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry.py).

### funcprops.registry.PropertyRule

A localized, typed theorem about positional arguments of a function head.

This type is responsible only for theorem matching and instantiation. Transport through compositions such as ``F(g(x))`` is handled separately by the registry transport layer.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `head` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `property` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `subject` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `result` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `proof_kind` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `verifier` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry.py).

### funcprops.registry.RuleCase

Pair a sufficient property case with native argument matching and a stable identity.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `value_source` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `condition_source` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_property_type` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `rule_id` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `signature` | `RuleSignature(arguments=(), mode=None, coordinate=None, priority=0)` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry.py).

### funcprops.registry.RuleSignature

Bind argument patterns, analysis mode, coordinate ownership and precedence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `arguments` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `mode` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coordinate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `priority` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry.py).

### funcprops.registry_derivatives.ChainRuleCertificate

Formal first-derivative transport under the recorded registry guards.

Source definition and differentiability on a consuming domain remain separate premises. Replay uses the default or explicitly supplied registry.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `terms` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `source` | `native-registry-chain-rule` | Route identifier or source-context record; consult this type's docstring. |
| `gradient_certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.ChainRuleTerm

Record one product contributing to a transported derivative.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `argument_position` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `argument` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `partial_derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inner_derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `product` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.DerivativeRule

Exact partial derivative theorem for one positional function argument.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `head` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `with_respect_to` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `result` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `arity` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.GradientCertificate

Registered outer gradient with one component per requested argument.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `components` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `gradient` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `positions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `missing_positions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `native-registry-gradient` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.GradientComponent

Record one partial derivative and its rule evidence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `argument_position` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `argument` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `partial_derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.HessianCertificate

Registered outer Hessian derived from exact derivative rules.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `positions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `hessian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `source` | `native-registry-hessian` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.IdentityRule

A localized exact identity for a function head.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `head` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `replacement` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `arity` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.InstantiatedDerivativeRule

Bind a registry derivative formula to concrete subjects and guards.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rule` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `argument` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `partial_derivative` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `substitutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.InstantiatedIdentityRule

Bind a registry identity to concrete subjects and parameter conditions.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rule` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `replacement` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `substitutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.JacobianCertificate

Exact Jacobian of a tuple-valued inner map.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `required` | Declared query coordinates. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `True` | Stored completion claim; its theorem premises still require replay. |
| `source` | `symbolic-inner-jacobian` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `complete`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_derivatives.MultivariateChainRuleCertificate

Formal gradient/Hessian transport with recorded order and registry guards.

A consuming domain theorem must also prove source definition and the required regularity of the inner map. Shape alone is not a transport proof.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variables` | `required` | Declared query coordinates. |
| `gradient` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `hessian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `gradient_certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `hessian_certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `native-registry-multivariate-chain-rule` | Route identifier or source-context record; consult this type's docstring. |
| `second_order` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_derivatives.py).

### funcprops.registry_transport.AnalysisSubject

Variables and domain on which a transported property is queried.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `variables` | `required` | Declared query coordinates. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_transport.py).

### funcprops.registry_transport.SubjectMap

Map registry subject slots into one or more analysis variables.

The full Jacobian is stored for multivariable analysis, while ``tangent`` provides the one-variable view used for scalar paths.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `source_slots` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `analysis_variables` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_transport.py).

### funcprops.registry_transport.TransportedPropertyRule

An instantiated registry theorem transported to analysis variables.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `instantiated` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `analysis_variables` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `subject_map` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conditions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `result` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `source` | `native-registry-path-transport` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/registry_transport.py).

### funcprops.results.ConditionalExpression

Pair a mathematical value with the condition under which it applies.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `condition` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/results.py).

### funcprops.results.DetailedPropertyResult

Uniform non-breaking view of detailed property-analysis output.

Public property functions may keep returning their compact enums, sets, or specialized result dataclasses.  ``as_detailed_result`` projects any such value onto this common protocol for downstream orchestration.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `primary` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `None` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `complete` | `None` | Stored completion claim; its theorem premises still require replay. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exceptions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `all_properties` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certified` | `None` | Stored or derived certification status, meaningful under the replay contract. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/results.py).

### funcprops.results.PropertyResult

Retain a property value, guarded cases, domain provenance and evidence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `primary` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `all_properties` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `exceptions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `complete` | `None` | Stored completion claim; its theorem premises still require replay. |
| `certified` | `None` | Stored or derived certification status, meaningful under the replay contract. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/results.py).

### funcprops.results.Singularity

Describe a singular locus, its kind and supporting local data.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `kind` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `condition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `multiplicity` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/results.py).

### funcprops.results.SingularityResult

Classified Boolean singularity loci with their supporting records.

Every locus is a Boolean condition in the analysis variable(s). ``singularities`` is the classified union restricted to the effective function domain. ``unrestricted_singularities`` preserves the ambient singular locus, while ``interior_singularities``, ``boundary_singularities``, and ``exterior_singularities`` classify it relative to the restriction. ``records`` preserves the lower-level :class:`Singularity` objects, including guards, multiplicities, and provenance.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `singularities` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `poles` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `removable` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `essential` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_points` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_cuts` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `definition_cuts` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `discontinuities` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `records` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `Complexes` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `restriction` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unrestricted_singularities` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `interior_singularities` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `boundary_singularities` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exterior_singularities` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_interior` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_boundary` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_exterior` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/results.py).

### funcprops.root_coverage.RootCoverageCertificate

Assemble real root regions, source restrictions and unresolved coverage.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain_record` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `regions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `unresolved` | `EmptySet` | Regions or obligations with no exhaustive conclusion. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `root_count` | `None` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `reason` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/root_coverage.py).

### funcprops.root_coverage.RootRegionProof

Bind a real region's count to a declared theorem and source evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `multiplicity_count` | `None` | Count with multiplicity when established. |
| `roots` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `witness` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/root_coverage.py).

### funcprops.root_coverage.SpecializedRootCoverage

Bind a guarded real root cover to exact parameter substitutions.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `substitutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `coverage` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/root_coverage.py).

### funcprops.seam_regularity.SeamRegularityProof

Bind a continuity assembly or a nonzero limiting gap to its source set.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `conclusion` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cells` | `required` | Certified local cells; their union and ownership are separate obligations. |
| `seams` | `required` | Owned branch-boundary and one-sided data. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/seam_regularity.py).

### funcprops.shared_zeros.ComplexZeroSubsetProof

Transfer complex root exclusion from a checked parent region.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/shared_zeros.py).

### funcprops.shared_zeros.SharedZeroImplication

Prove a lower zero order at an implicitly isolated base root.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `base_region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `minimum_order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `factor` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cofactor` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outer_variable` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `outer` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `jets` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/shared_zeros.py).

### funcprops.shared_zeros.SharedZeroOrderProof

Combine a shared-zero implication with an exhaustive count to prove exact order.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `parent` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `implication` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/shared_zeros.py).

### funcprops.shared_zeros.SharedZeroRegion

Transfer a checked shared-order conclusion to a root or pole region.

Replay contract: `witness-kernel`; mode: `theorem-premise-check`.

| Field | Default | Role |
| --- | --- | --- |
| `order_proof` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `base_region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `schema_version` | `1` | Record schema identifier; a matching number is not a proof. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/shared_zeros.py).

### funcprops.shared_zeros._Replay

See the owning module for this concrete theorem.

Replay contract: `witness-kernel`; mode: `unsupported-unified-replay`.

Constructor data and derived fields are documented by the class and its owning interface.

Available status/check interfaces: `complete`, `certified`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/shared_zeros.py).

### funcprops.singularities.analysis.SingularityAnalysis

Collect singular loci, local records and unresolved coverage obligations.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `branch_cuts` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `definition_cuts` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `poles` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `essential` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `branch_points` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `removable` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `discontinuities` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain_exterior` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `unknown_heads` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `structural-singularity-traversal` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/analysis.py).

### funcprops.special_theorems.GuardedTheorem

Describe an executable sufficient theorem and its parameter guard.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `property` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `theorem_id` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/special_theorems.py).

### funcprops.taylor_models.TaylorModel

Store a polynomial approximation and certified derivative remainder bound.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `center` | `required` | Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root. |
| `order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `polynomial` | `required` | Rational polynomial constraining the auxiliary generator or local source. |
| `remainder_lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `remainder_upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `taylor-lagrange-interval` | Route identifier or source-context record; consult this type's docstring. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/taylor_models.py).

### funcprops.theorem_closure.TheoremFact

Pair a derived property with the theorem and guard establishing it.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `property` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `given` | Route identifier or source-context record; consult this type's docstring. |
| `theorem_id` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/theorem_closure.py).

### funcprops.theorem_registry.TheoremRecord

Describe a sufficient theorem, its hypotheses and adversarial test cases.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `theorem_id` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `premise_property` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `premise_value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `conclusions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `proof_basis` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `completeness` | `complete-on-same-domain` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `mutation_tags` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `verifier` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/theorem_registry.py).

### funcprops.transcendental.algebraize.AlgebraizationResult

Preserve source restrictions in an auxiliary algebraic representation.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `substitutions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `constraints` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `exact` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `none` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source_domain` | `Reals` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `relations` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inverse_substitutions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/algebraize.py).

### funcprops.transcendental.analytic.AnalyticNeighborhoodCertificate

Prove holomorphy on a neighborhood with explicit branch premises.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `holomorphic` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `region` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `unknown` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `obstructions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

Available status/check interfaces: `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/analytic.py).

### funcprops.transcendental.complex_roots.ArgumentPrincipleCertificate

Store a contour count with its route-specific boundary premises.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `winding_number` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_count` | `required` | Local zero count under this concrete contour/root theorem. |
| `pole_count` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `certified` | `False` | Stored or derived certification status, meaningful under the replay contract. |
| `method` | `unknown` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `boundary_segments` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `precision` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `analytic_certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

Available status/check interfaces: `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/complex_roots.py).

### funcprops.transcendental.complex_roots.CertifiedComplexRootRectangle

Store a complex root region with count and accuracy evidence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `rectangle` | `required` | Rational rectangle on which the local claim applies. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `certificate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/complex_roots.py).

### funcprops.transcendental.complex_roots.ComplexRectangle

Closed axis-aligned complex rectangle with exact real bounds.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `re_min` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `re_max` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `im_min` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `im_max` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/complex_roots.py).

### funcprops.transcendental.complex_roots.ComplexRootIsolationResult

Expose route-specific complex root regions, counts and replayable proof data.

Replay contract: `route-dependent`; mode: `bound-native-or-algroots-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `roots` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `rectangles` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `total_count` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `unknown` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `certificates` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `distinct_root_count` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `isolation_complete` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `algebraic_certificate` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `isolation_state` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `coverage_complete`, `isolation_complete`, `accuracy_complete`, `certified`, `scope`, `verify`, `check`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/complex_roots.py).

### funcprops.transcendental.exp_fourier.ExponentialFourierCount

Count roots through a supported exponential-Fourier representation.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `sequence` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `critical_points` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `source` | `normalized-exponential-derivative-sequence` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/exp_fourier.py).

### funcprops.transcendental.extrema.ExtremumFamilyCertificate

Bind indexed extremum values to a supported derivative-root family.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `critical_geometry` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `extrema` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `alternating` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `notes` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `None` | Analysis coordinate and its intrinsic assumptions. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/extrema.py).

### funcprops.transcendental.extrema.ExtremumOrderingTheorem

Exact theorem ordering successive indexed extrema.

``magnitude_direction='decreasing'`` means ``|E_{k+1}| < |E_k|`` on ``index_guard``.  ``global_max_index``/``global_min_index`` identify a member when the alternating sign pattern plus magnitude ordering proves first-member dominance.  The proof field records the exact Lyapunov/Sonin quantity used by funcprops; it is not numerical evidence.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `magnitude_direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `index_guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `global_max_index` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `global_min_index` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `proof` | `None` | Underlying proof that must agree with this public summary. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `notes` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parameter` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/extrema.py).

### funcprops.transcendental.extrema.ExtremumRange

Certified symbolic interval image from endpoint and critical-point data.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `lower_attained` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper_attained` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `candidates` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `None` | Analysis coordinate and its intrinsic assumptions. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/extrema.py).

### funcprops.transcendental.periodic.PeriodicCondition

Describe a Boolean condition repeated over an exact period.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `set` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/periodic.py).

### funcprops.transcendental.periodic.PeriodicSet

Set obtained by translating a base set by integer multiples of a period.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `base` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `period` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variable` | `None` | Analysis coordinate and its intrinsic assumptions. |
| `origin` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/periodic.py).

### funcprops.transcendental.reduce.UnivariateReductionResult

Retain a reduced univariate condition and its exactness obligations.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `condition` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `cells` | `()` | Certified local cells; their union and ownership are separate obligations. |
| `roots` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `method` | `univariate_cells` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |

Available status/check interfaces: `certified`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/reduce.py).

### funcprops.transcendental.root_geometry.MonotoneRootCount

Count roots using monotone cells, limits and endpoint ownership.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `required` | Stored completion claim; its theorem premises still require replay. |
| `critical_points` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `derivative-sign-cells` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/root_geometry.py).

### funcprops.transcendental.roots.CertifiedRootInterval

Record an owned real root interval with multiplicity and evidence.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `interval` | `required` | Exact interval supporting this local claim or root selection. |
| `certificate` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/roots.py).

### funcprops.transcendental.roots.ParametricZeroFamily

Represent a guarded symbolic root family and its index domain.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `support` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `simple` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `interlaces_prev_degree` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `interlacing` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/roots.py).

### funcprops.transcendental.roots.RootCertificate

Bind a real root count or location to a declared sufficient theorem.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `method` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `proof` | `()` | Underlying proof that must agree with this public summary. |
| `complete` | `True` | Stored completion claim; its theorem premises still require replay. |
| `multiplicity` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `None` | Analysis coordinate and its intrinsic assumptions. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/roots.py).

### funcprops.transcendental.roots.RootIsolationResult

Expose real root locations, indexed families and unresolved coverage.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `roots` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_intervals` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `isolated_intervals` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `periodic` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `method` | `unknown` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `certificates` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `parametric_families` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `geometry` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expression` | `None` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `None` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/roots.py).

### funcprops.transcendental.unified_real.UnifiedRealAnalysis

Collect compatible domain, zero, sign and image facts for one expression.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `zero_geometry` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `left_tail` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right_tail` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `image` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/unified_real.py).

### funcprops.transcendental.zero_geometry.CertifiedIntegerBracket

Rigorous integer enclosure for an exact indexed-tail selector.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `lower` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `upper` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `proof` | `()` | Underlying proof that must agree with this public summary. |
| `zero_template` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cutoff` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `direction` | `right` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inclusive` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transcendental.zero_geometry.IndexedTailInversionCertificate

Bind a tail cutoff to an exact index comparison in a zero family.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cutoff` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `direction` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `inclusive` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `first_index` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `zero_template` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `True` | Stored completion claim; its theorem premises still require replay. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `proof` | `()` | Underlying proof that must agree with this public summary. |
| `integer_bracket` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transcendental.zero_geometry.IntervalPropertyCell

Record a property on an interval between distinguished source points.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `interval` | `required` | Exact interval supporting this local claim or root selection. |
| `value` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `proof` | `()` | Underlying proof that must agree with this public summary. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transcendental.zero_geometry.PropertyIntervalDecomposition

Partition a source domain into interval property cells and boundary loci.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `derivative_order` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `cells` | `()` | Certified local cells; their union and ownership are separate obligations. |
| `boundary_geometry` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `alternating` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `first_value` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transcendental.zero_geometry.ZeroGeometryCertificate

Bind ordered zero-family data to source and parameter premises.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `support` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `count` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `simple` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `indexed_family` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `orderings` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `interlacings` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `derivative_order` | `0` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `complete_on_support` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `notes` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `real_exhaustive` | `False` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transcendental.zero_geometry.ZeroInterlacing

Record proved interlacing between supported zero families.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `first_family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `second_family` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `pattern` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |
| `complete` | `True` | Stored completion claim; its theorem premises still require replay. |

Available status/check interfaces: `complete`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transcendental.zero_geometry.ZeroOrdering

Record proved order relations within a supported zero family.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `left` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `right` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `relation` | `<` | Entire implicit equation defining the local branch family. |
| `guard` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `` | Route identifier or source-context record; consult this type's docstring. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transcendental/zero_geometry.py).

### funcprops.transformation.ChangeOfVariablesCertificate

Record a substitution's Jacobian, orientation and absolute determinant.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `required` | Declared query coordinates. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `determinant` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `absolute_determinant` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `local_invertibility` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `orientation` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `domain` | `Reals` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `source` | `local-change-of-variables` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transformation.py).

### funcprops.transformation.DeterminantNonvanishingCertificate

Bind a real C1 map and its domain to a Jacobian nonvanishing decision.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `determinant` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `required` | Declared query coordinates. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `witness` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `assumptions` | `True` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `expressions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transformation.py).

### funcprops.transformation.LocalInvertibilityCertificate

Record applicability of the real C1 inverse function theorem.

FALSE means a theorem hypothesis fails. It does not rule out a continuous or nondifferentiable inverse, as illustrated by the cube map at zero.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `required` | Declared query coordinates. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `determinant` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `nonvanishing` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `classification` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `inverse-function-theorem` | Route identifier or source-context record; consult this type's docstring. |

Available status/check interfaces: `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transformation.py).

### funcprops.transformation.TransformationGeometry

Combine Jacobian, invertibility and change-of-variables conclusions.

Replay contract: `nested-or-summary-data`; mode: `no-registered-standalone-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expressions` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `variables` | `required` | Declared query coordinates. |
| `domain` | `required` | Domain of this concrete claim; consult the route for requested/effective semantics. |
| `jacobian` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `determinant` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `determinant_nonvanishing` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `local_invertibility` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `change_of_variables` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

No status or check methods are defined on this data record; use its owning or registered checker.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/transformation.py).

### funcprops.verified_roots.RealRootInterval

Bind a zero or unique-root interval to its source domain and count method.

Replay contract: `factory-certificate`; mode: `declared-backend-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `expression` | `required` | Original expression bound to this theorem; source holes remain relevant. |
| `variable` | `required` | Analysis coordinate and its intrinsic assumptions. |
| `interval` | `required` | Exact interval supporting this local claim or root selection. |
| `root_count` | `required` | Distinct-root count when established, separate from multiplicity. |
| `unique` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `required` | Route identifier or source-context record; consult this type's docstring. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `scope`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/verified_roots.py).

### funcprops.work_budget.BudgetedResult

Retain an unfinished query and explicit resource-exhaustion status.

Replay contract: `factory-certificate`; mode: `unsupported-unified-replay`.

| Field | Default | Role |
| --- | --- | --- |
| `primary` | `required` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `cases` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `all_properties` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `source` | `None` | Route identifier or source-context record; consult this type's docstring. |
| `exceptions` | `()` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `evidence` | `()` | Route-specific witnesses; their presence alone is not successful replay. |
| `complete` | `False` | Stored completion claim; its theorem premises still require replay. |
| `certified` | `False` | Stored or derived certification status, meaningful under the replay contract. |
| `domain_record` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `operation` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |
| `query` | `None` | Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it. |

Available status/check interfaces: `complete`, `certified`, `verify`.

[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/work_budget.py).
