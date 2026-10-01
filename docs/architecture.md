# Architecture

`funcprops` separates declarative property facts, symbolic proof machinery, and
public query routing so exact reasoning can be reused without forcing every API
through the same expensive path.

## Main modules

- `api.py` defines the public `function_*` surface and routes property queries.
- `engine.py` evaluates conditional catalogue rules, overload precedence, and
  assumptions.
- `registry.py` and `data/catalogue.json` store conditional function-family
  metadata and source-pattern information.
- `conditions.py` parses deterministic SymPy-constructor catalogue expressions
  and preserves custom semantic predicates explicitly.
- `singularities.py` handles poles, removable and essential singularities,
  branch/definition loci, analyticity, meromorphicity, and continuity.
- `stratification.py` normalizes guarded alternatives and splits mixed
  variable/parameter domains for all property engines.
- `_semialg.py` is the narrow adapter to semialg 1.0.0+ public root exports for
  exact semialgebraic domain, range, sign, monotonicity, convexity, smoothness, and mapping operations.
- `real_analysis/` contains domain, sign/inequality, monotonicity, range, mapping,
  convexity, boundedness, smoothness, and structural-property reasoning.
- `real_analysis/piecewise.py` supplies effective branch domains and shared
  interface data for property-specific piecewise combination.
- `transcendental/` contains certified root isolation, algebraization,
  periodic reduction, zero geometry, extrema, and supporting proof objects.
- `branchcuts/` contains structural cut pullback and boundary-value/jump
  machinery.
- `proof_cache.py` coordinates reusable lazy proof primitives.
- `verification.py` replays certificate invariants.

## Conditional results

Property queries preserve unresolved parameter conditions. A singularity record,
for example, keeps its variable-dependent locus separate from the parameter-only
guard under which that locus applies. This distinction is necessary for families
whose branch or pole structure changes with an order or shape parameter.

`PropertyResult` is the shared representation for guarded alternatives. Mixed
variable/parameter conditions are stratified before a property engine runs, and
nested guarded results are flattened back into the same representation. Internal
transformations preserve cases
classification.

Three-valued logic is a correctness requirement. An undecidable set relation,
branch-locus intersection, singularity search, or domain conversion must remain
unknown.

## Real-property proof flow

The real-analysis layer uses inexpensive exact information before invoking heavier
machinery:

```text
property query
  -> parameter-domain stratification
  -> primitive and structural closure facts
  -> shared sign/inequality proof when applicable
  -> effective Piecewise branch analysis when applicable
  -> direct symbolic simplification
  -> transcendental algebraization when applicable
  -> semialgebraic solver for the algebraized problem
  -> periodic fundamental-domain reduction
  -> certified root or zero geometry
  -> monotonic/convex interval decomposition
```

Not every query traverses this entire pipeline. Fast paths return immediately when
they already prove the requested property.

Completeness is explicit. An incomplete root search can be useful evidence but is
never consumed as an exhaustive zero set.

## Shared inequality and piecewise reasoning

The sign engine is the common exact inequality oracle. Relations such as `f >= g`
are reduced to the sign of `f - g`; derivative-based consumers therefore reuse the
same proof ladder.

Finite `Piecewise` expressions are first converted to a `PiecewiseDecomposition`
of effective, non-overlapping connected branch cells. Every finite seam records
left/right approach branches separately from the branch that owns the point.
`PiecewiseBoundaryCertificate` computes one-sided values and derivatives on the
selected branch expressions themselves, avoiding whole-Piecewise limit heuristics.
Sign and boundedness combine branch classifications directly; zeros and ranges
merge branch-local sets/images. Continuity, differentiability, smoothness,
monotonicity, and convexity additionally require the appropriate certified seam
conditions. Unknown interface facts remain unknown
from compatible branch labels alone. See [`docs/piecewise.md`](piecewise.md).

## Singularity loci and restricted domains

Singularity analysis uses Boolean loci
isolated points. In several variables, rational denominators and elementary
branch structures therefore remain as exact hypersurface or preimage conditions,
such as `Eq(x + y, 0)` or the preimage of the principal logarithm cut. Complex
ambient results expose these conditions explicitly through `re(...)` and
`im(...)`.

`ConditionalExpression` supplies a function-specific restriction independently of
the ambient real/complex mode. The aggregate singularity query intersects the
known locus with that restriction, using semialgebraic feasibility when available
to certify empty intersections. Detailed singularity results retain the
unrestricted locus and classify it against the restriction's ambient interior,
boundary, and exterior. Thus an excluded support boundary remains available as
geometry/evidence without being reported as a singularity of the restricted
function itself.

## Zero geometry and interval decomposition

The root layer separates root representation from geometric proof. Closed-form and
isolated roots coexist with `IndexedZero` families. Certificates describe support,
parameter guards, counts, simplicity, ordering, and interlacing.

First-derivative zero geometry feeds monotonic decomposition; second-derivative
geometry feeds convexity decomposition. Finite exact roots create concrete cells.
Complete infinite families create symbolic indexed cells
numerical truncation.

Indexed-tail inversion adds exact inverse-index objects for semi-infinite domains:

```text
IndexedZero family
  -> IndexedTailIndex / inversion certificate
  -> first admissible extremum indices
  -> extremum ordering theorem
  -> finite exact candidate set
  -> function range
```

A general parameter cutoff can remain symbolic. When same-family ordering or
interlacing identifies the first admissible index exactly, the selector is reduced
to an integer.

## Shared proof context

`PropertyProofContext(expr, var, domain, assumptions)` is a lazy container for
cross-property proof primitives. It does not compute a domain, derivative, sign,
or singularity analysis when constructed.

Bounded LRU caches independently retain:

- raw derivatives;
- factored derivatives;
- natural domains;
- sign classifications;
- one-sided endpoint limits;
- zero geometry;
- singularity analyses; and
- monotonic partitions.

Raw and factored derivatives are separate because factorization can dominate the
cost of an otherwise cheap derivative query. Recursive traversal can bypass the
global cache boundary when transient subexpressions are unlikely to be reused.

Cache-key normalization is deliberately syntactic: Boolean conjunctions and
disjunctions are flattened, duplicates removed, operands sorted canonically, and
simple relations oriented deterministically. Quantifier elimination and expensive
logical simplification are never performed merely to build a cache key.

## Certificate replay

Verification lives above the proof context. Convexity classifications use one
`ConvexityCertificate` representation; strong classifications add a certified
modulus while ordinary classifications retain their method and proof payload in
the same shape. A verifier reconstructs the invariant claimed by a certificate
from its payload and current exact primitives. Failed or undecidable checks return
failure; replay does not treat inability to disprove a claim as proof of that
claim.

## Error handling

Symbolic fallbacks catch only documented computational failures through
`SYMBOLIC_QUERY_ERRORS`. Programming errors such as `NameError`, `KeyError`, and
unexpected `AttributeError` are allowed to surface. Individual interoperability
boundaries may catch a more specific exception when an external SymPy protocol is
known to use it, such as `Boolean.as_set()` on custom Boolean predicates.

## Executable documentation and invariant tests

The property reference, tutorial notebook, and specification tests share one canonical example corpus in `examples/property_examples.py`. Every public `function_*` query has a page under `docs/properties/` with a common structure: mathematical definition, public API and parameters, domain/assumption semantics, executable examples, applications, proof strategy, limitations, and related properties. The tutorial notebook is built from those same examples.

Tests are separated by purpose. `tests/specification/` checks documented behavior and executes the tutorial, while `tests/invariants/` checks mathematical laws that must hold across proof routes: implication chains, parameter specialization, piecewise interface compatibility, expression-rewrite invariance, certificate replay, and cross-property consistency. Regression tests remain focused on particular algorithms and previously discovered edge cases. This separation makes a failure identify whether the public contract, a mathematical invariant, or an implementation-specific regression was violated.


## Detailed-result protocol

Compact property APIs return their direct mathematical value when unconditional.
A parameter-stratified `PropertyResult` is projected to a SymPy `Piecewise` at the
root public boundary; `return_result=True` preserves the rich result. Downstream
code that already has a compact value can call `funcprops.as_detailed_result(value)`.
The resulting `DetailedPropertyResult` exposes `primary`, `cases`, `domain`,
`complete`, `source`, `evidence`, `certificate`, `exceptions`, and
`all_properties` without forcing every property family into one public scalar
type.  This keeps simple calls lightweight while giving orchestration and
certificate tooling a stable structural contract.

## Native registry theorem layers

The native registry uses `FunctionSlot` placeholders, which are local positional
arguments. `PropertyRule` stores direct property
facts. `IdentityRule` stores exact rewrites and `DerivativeRule` stores an exact
partial derivative with respect to one function slot.

First-derivative transport is replayable through `ChainRuleCertificate`. For a
call `F(g1(x), ..., gn(x))`, `registry_derivative` requires a derivative theorem
for every varying argument and constructs

`sum_i (partial F / partial slot_i)(g1(x), ..., gn(x)) * diff(gi(x), x)`.

Rule conditions are instantiated and retained on the certificate. A consumer
must prove those conditions on its analysis domain before treating the
certificate as applicable. The shared derivative cache consumes unconditional
complete certificates; monotonicity can additionally consume a conditional
certificate when its current assumptions imply the certificate condition.

Registry coverage is tracked in `.github/registry/coverage-matrix.md`. The
checked baseline is monotone: CI permits registry growth but rejects silent
loss of an existing category/property coverage cell.

## Native registry composition

The native registry separates theorem localization from transport into a user
query. `FunctionSlot` binds theorem-local argument positions without creating
global-symbol dependencies. `SubjectMap` records how one or more theorem subjects
map to the expressions in a concrete call.

For a scalar composition

\[
x \longmapsto F(g_1(x),\ldots,g_n(x)),
\]

`registry_derivative` certifies the derivative as the registered outer gradient
dotted with the path tangent `(g_1'(x), ..., g_n'(x))`. Missing or ambiguous
partial-derivative rules leave the certificate incomplete; they are never guessed.
Pointwise, regularity, finite joint-zero, and monotonicity-via-gradient transports
use the same subject-map abstraction.

For multiple independent analysis variables, the subject map stores the full
Jacobian. First-order transport uses `JacobianCertificate`; second-order transport
uses `HessianCertificate` and the multivariate chain rule. Convexity is certified
from the composite Hessian.

The same separation is used by `ConditionalExpression` and Piecewise analysis:
conditions restrict the effective analysis domain, branch expressions are analyzed
through the ordinary property engines, and boundary certificates determine whether
branch-local conclusions merge into a global result.
