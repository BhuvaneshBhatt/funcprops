# Result contracts and glossary

These are route-specific contracts, not a universal schema for every returned object. Read the result's concrete type and proof route. Compact property values, factory-based certificates, backend adapters and native witness kernels differ.

Source-bound proofs retain the definitions of raw operands before a computational formula cancels or evaluates them. This includes constant subexpressions and power exponents. Held logarithms with an explicit base use the principal-logarithm ratio for calculation and differentiation; both logarithms and the nonzero denominator remain source obligations. Equality and nonzero conditions can have complex operands even when the analysis coordinate is real. Their real-axis sets must retain valid negative-axis points, such as `log(-1)**2 + pi**2 == 0`.

## Property and operation outcomes

| Interface | Established result | Undecided result | Completion meaning |
| --- | --- | --- | --- |
| Compact property query | Enum, set/condition, or guarded Piecewise | UNKNOWN member or explicit unknown fallback | No universal completion field; request details |
| PropertyResult / detailed view | Classification plus supported evidence/cases | Unresolved obligations/cases remain visible | Per-property coverage, not automatically a root theorem |
| Certified operation | Its documented value/certificate | Often None, or an incomplete structured record | Consult the operation; a missing certificate is not a counterexample |
| ReplayStatus | certified=True after successful replay | certified=None for unsupported replay; False for rejected/exhausted evidence | Exposed only after successful replay; may be None for factory-based records |
| CheckResult | certified=True for accepted local/coverage evidence | rejected/unsupported/exhausted outcomes | complete=True only for the checked theorem's exhaustive claim |

`verify_certificate` normalizes Python True and SymPy S.true to Python True, and returns False for other checker results; unresolved symbolic predicates and truthy non-Boolean payloads never become successful proofs. Replay status also normalizes literal Boolean completion flags after successful replay. `verify_certificate(...) == False` means evidence failed or is unsupported. It never proves the mathematical negation. A Boolean property answer False/FALSE establishes negation only under that property's contract. Do not apply that interpretation to a failed verifier or a completion flag.

`replay_status` reports supported, certified, complete, scope, reason, outcome, schema_version and factory_replay. A schema number or a claimed status is not a proof. Unregistered subclasses cannot override check()/verify() to select or satisfy a replay checker. `CheckOutcome` distinguishes valid-local-proof, complete-coverage, proved-inadmissible-stratum, rejected-evidence, unsupported-replay and resource-exhaustion. Inadmissibility certifies a forbidden parameter case; it cannot supply a root count for that case.

## Real root coverage

Native CoverageProof/AdaptiveRootResult records bind source syntax, coordinate, requested/effective domain and parameter/branch context. `complete` requires an exact cover by root witnesses or exclusion proofs. Unresolved regions prevent a global total. Infinite domains also need rigorous tails or exhaustive indexed families. Distinct root counts and multiplicity counts are different quantities. A partial record may verify while `complete=False`. Property-coverage consumers also expose per-conclusion completion fields; inspect the conclusion you need.

## Complex root routes

| Route / evidence | Coverage | Individual isolation | Accuracy and complete |
| --- | --- | --- | --- |
| Native entire ComplexIsolationProof/state/result | Every region certified; no unresolved region; exact cover and counts checked | Every positive region is count-one or has a supported location/multiplicity witness; clusters can keep this False | accuracy_complete checks requested width/diameter; complete is the conjunction of all three flags |
| Native QuotientIsolationProof/state/result | Joint numerator/denominator/original-guard cover and classifications established | Distinct source zeros and poles resolved with required order relations | Same three-way conjunction; accuracy applies to relevant source-root/pole regions |
| AlgebraicComplexRootProof / algebraic result | Exhaustive algebraic candidates filtered against source, branch, rectangle and domain restrictions | Finite accepted locations are known | complete/coverage_complete concern candidate coverage; exact locations may have unknown source order, especially radicals; native width/diameter semantics do not transfer automatically |
| Factory-based exact root result | Route-specific exact root-set coverage | Exact locations may be known | Multiplicity may remain unknown; inspect total_count and evidence instead of inferring it from complete |

For native results:

- `coverage_complete` proves exhaustive coverage even when positive clusters remain.
- `isolation_complete` requires individually resolved roots/poles.
- `accuracy_complete` checks requested box accuracy after isolation.
- `complete = coverage_complete and isolation_complete and accuracy_complete`.
- `root_count` / `distinct_root_count` are distinct-root counts when proved.
- `total_count` / `multiplicity_count` count zeros with multiplicity when proved.

A small count-one box is not automatically a width/diameter target certificate. A count-two box does not establish two distinct roots. Boundary zeros or an unproved boundary cannot be discarded to claim completion. Native coordinates are unconstrained commutative Symbols, rational rectangle corners and no free parameters in the declared entire/quotient grammar. See [isolation](../tutorials/complex-isolation.md) and [the algebraic adapter](../algroots-complex-backend.md).

## Quotient ledger and source holes

Let g=exp(z)-2 in a rectangle containing only its zero log(2).

| Original source | Source zero multiplicity | Extension zero multiplicity | Pole multiplicity |
| --- | --- | --- | --- |
| held g**2*g/g | 0 | 2 | 0 |
| g/sin(g) | 0 | 0 | 0 |
| g/sin(g)**2 | 0 | 0 | 1 |

Original denominator exclusions remain source holes. Positive local order at an excluded point is an extension zero, not an attained source zero. `excluded_zero_multiplicity` records those excluded extension zeros. `winding_count` is numerator order minus denominator order; it is not a distinct root count or a source-zero count. Counts of poles use meromorphic extension semantics, with the source restrictions retained separately. See the executable [quotient tutorial](../tutorials/quotients-and-holes.md).

A SharedZeroImplication supplies a minimum order at one implicitly located base zero. Its successful replay has outcome valid-local-proof and complete=False; additional cofactor zeros and a larger actual order remain possible. A separate SharedZeroOrderProof needs the exhaustive count that makes the order exact.

## Conditional guarantees, budgets and replay

ComplexIsolationGuarantee and QuotientIsolationGuarantee always have `complete=False`: their verification validates a conditional search theorem. `applicable=None/False/True` distinguishes unresolved, disproved and discharged finite premises. Unbounded completed cofinal stages remain a hypothesis; no finite wall-time bound or universal termination follows. Particular multiple-root problems can complete outside the narrower simple-root guarantee.

Work exhaustion is not root exclusion. Completed local proofs remain useful; where supported, resume from the returned checked state. Checkpoints are in-memory records, not a durable storage format. See [budgets](../guides/budgets-and-resume.md).

Native kernel replay checks stored witnesses without the proposing search. The algebraic adapter redoes declared exact backend obligations. Some factory-based families recompute through their theorem factories. These are different trust boundaries; none is an external proof-assistant validation. See [certification](../certification.md) and [architecture](../architecture.md).

## Extrema bounds, branch atlases and implicit local orders

[Extrema bounds](../certified-extrema-bounds.md) certify infimum/supremum brackets. Their value coverage can be exhaustive while derivative-zero coverage is still partial: unresolved critical regions are enclosed instead of discarded. Requested value accuracy is a separate flag; attainment is not asserted.

[Branch atlases](../branch-atlas.md) distinguish chart coverage from global branch compatibility. A valid transition obstruction is certified partial evidence. A selected power can glue when its multipliers are trivial even if a global logarithm cannot. These results do not redefine principal expressions.

[Implicit local orders](../implicit-orders.md) distinguish local equality/order from global zero coverage. `common_zero_status` separates proved equality, proved exclusion, and unknown. Full rectangle order/count claims still require independent exhaustive counts. The records use concrete-type, schema-bound native replay; unknown discovery is never a positive coincidence proof.

## Finite metrics, polynomial parameters and branch recipes

`FiniteLipschitzProof` checks every defined real point of the requested finite set and every pairwise slope. Its constant is optimal on the effective finite domain, with zero for at most one point. `JumpVariationProof` covers a bounded interval by certified monotone motions and all owned boundary values; its total includes motion, jumps and isolated point excursions. Their checkers do not call the metric or partition proposers. The corresponding `LipschitzResult` and `VariationResult` summaries replay only when they carry the matching proof; older derivative-bound and other routes may return useful values without such a replay proof.

`ParameterGeometryProof` stores an exact prefix-tree partition of polynomial parameter space. It supports rational polynomials of degree at most four in one real root coordinate, up to four real parameters, and rational interval endpoints. Counts are distinct real roots, including degree loss and the identically-zero stratum. The checker recomputes Hermite trace-form signatures and endpoint ownership, checks the stored polynomial/event data and exact partition coverage, and rejects omitted or overlapping leaves. Unresolved sign prefixes keep `complete=False`; `specialize` returns no count there. This is not a general transcendental parameter decomposition. The cell budget and optional wall budget bound proposal effort; a wall timeout returns an uncertified budget result.

`AlgebraicCoefficientEncoding` binds original inputs to a rational generator selected by an irreducible polynomial and a unique rational isolating interval. Its checker verifies each exact coefficient representation without rerunning number-field discovery. Adapter queries retain original source-definition guards and restrictions. The supported compositum has degree at most four and at most four nonrational constants, with no additional symbolic coefficient parameters in these adapter routes.

`HolomorphicBranchChart` checks a supplied local formula for an entire implicit relation. Formulas combine selected logarithms, supported entire primitives and arithmetic; denominators require supported nonzero witnesses. `BranchGluingProof` checks exact rational rectangle coverage and every touching overlap using log-sheet transfers or an exact derivative identity plus an anchor value. `coverage_complete` concerns the chart cover; `gluing_complete` additionally requires equality on every overlap. A certified disagreement is valid partial evidence with `complete=False`. This framework assembles given recipes; it does not discover arbitrary implicit branches or identify them with a global principal branch.
