# funcprops

`funcprops` is a SymPy-backed package for global function properties.
It combines a conditional function property registry, exact semialgebraic reasoning from the semialgebraic geometry package `semialg`, transcendental interval analysis, special-function zero geometry, and branch-cut/singularity analysis.

The package is careful: parameter conditions are retained instead of guessed, piecewise branches are analyzed on their effective domains, incomplete numerical searches are never promoted to exact proofs, and undecidable comparisons remain unknown.

## Installation

```bash
pip install funcprops
```

The core runtime requires SymPy, mpmath, and semialg 1.0.0 or newer.

## Quick start

```python
import sympy as sp
from funcprops import (
    function_analytic,
    function_branchcuts,
    function_continuous,
    function_convexity,
    function_domain,
    function_homogeneity,
    function_meromorphic,
    function_monotonicity,
    function_periodicity,
    function_poles,
    function_range,
    function_symmetry,
)

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")

function_domain(sp.sqrt(x - 1), x)
# x >= 1

function_range(x**2, x, y)
# y >= 0

function_monotonicity(sp.exp(x), x)
# Monotonicity.STRICTLY_INCREASING

function_convexity(x**2, x)
# Convexity.STRONGLY_CONVEX

function_periodicity(sp.sin(2 * x) + sp.cos(3 * x), x, details=True).period
# 2*pi

function_symmetry((x - 2) ** 2, x, center=None, details=True).center
# 2

function_homogeneity(x**2 + y**4, (x, y), weights=(2, 1), details=True).degree
# 4

function_branchcuts(sp.log(1 - z), z)
# structural pullback of the principal logarithm cut

function_poles(sp.sin(z) / z**3, z)[0].multiplicity
# 2

function_analytic(sp.log(z), z, domain=sp.S.Complexes)
# Analyticity.ANALYTIC on the principal branch's natural domain

function_meromorphic(sp.log(z), z)
# Meromorphicity.NOT_MEROMORPHIC

function_continuous(sp.Abs(x), x)
# Continuity.CONTINUOUS
```

## Property model

API functions return exact classifications when the available proof machinery is sufficient. `PropertyResult` and `ConditionalValue` are the common representation for parameter strata across real and complex properties, so unresolved guards are preserved instead of being collapsed into a single answer. `PropertyResult.as_piecewise()` provides a Piecewise-style view when useful.

Three-valued reasoning is used throughout proof-oriented code. An undecidable set relation, domain implication, branch-locus intersection, or symbolic comparison is not treated as false merely because Python cannot decide it.

## Real-domain analysis

`funcprops` owns the property vocabulary. For semialgebraic functions on semialgebraic real domains `funcprops` delegates exact domain, range, sign, monotonicity, convexity, smoothness, and mapping-property problems to `semialg`, while retaining stronger exact `funcprops` results when they are already certified. A shared sign engine is the main inequality proof primitive: derivative signs feed monotonicity and convexity, while relation queries reduce comparisons to the sign of a difference. Transcendental expressions are handled compositionally using primitive facts, exact domain restrictions, periodic reductions, derivative geometry, and certified interval reasoning.

Mixed variable/parameter domains are split once by the shared stratification layer and each variable-domain branch is analyzed independently. Finite `Piecewise` expressions likewise use one effective-branch representation. Consumers add only the interface conditions their property requires: monotonicity checks jump direction, convexity checks continuity and derivative ordering, and sign and boundedness combine exact branch classifications.

The main real-analysis APIs include:

- `function_domain()` and `function_range()`;
- `function_sign()`;
- `function_boundedness()`;
- `function_monotonicity()`;
- `function_oscillation()`;
- `function_convexity()` with normalized `ConvexityCertificate` evidence;
- `function_injective()`, `function_surjective()`, and `function_bijective()`;
- `function_continuous()`, `function_differentiability()`, `function_smoothness()`, and `function_analytic()`;
- `function_periodicity()`, `function_symmetry()`, and `function_homogeneity()`.

Multivariate APIs normalize variable collections explicitly rather than treating a tuple as one symbolic atom. Constant-Hessian convexity and affine mapping cases are handled exactly; unsupported nonlinear multivariate mapping questions give unknown.

## Monotonic partitions and exact inverse solving

`MonotonicPartition` is the shared exact interval representation used by monotonicity, range, injectivity, inverse solving, oscillation, and extrema. Finite partitions retain exact critical points, endpoint limits, and endpoint attainment. Infinite oscillatory partitions retain indexed zero geometry without guessing an unsupported increasing/decreasing phase.

`solve_monotonic_inverse()` first attempts a whole-domain exact solve. If that is insufficient, it uses monotonic cells and exact image pruning. On a strict finite cell, an unresolved symbolic inverse can still be completed by certified endpoint signs and a rational isolating interval. `certified_monotonic_inverse()` is the explicit certification-oriented spelling of the same reusable primitive. The same partition can be passed explicitly to consumers or reused through the bounded proof cache.

## Certified real-root backends

Real root isolation is domain-cell aware: denominator zeros, logarithm boundaries, noninteger-power branch boundaries, Piecewise switch points, and other exact domain boundaries split the problem before any interval certificate is constructed. Identically-zero interval cells are retained as ordinary parts of the mathematical zero set.

For finite elementary cells, an outward-rounded interval evaluator can prove that zero is excluded from the function image, or from the derivative image. The latter certifies strict monotonicity even when symbolic monotonicity is unresolved. Point signs use `robust_real_sign()`, which combines exact SymPy sign reasoning with an audited exp/log interval fallback to avoid overflow and underflow.

`exponential_fourier_count()` provides a restricted derivative-sequence root counter for real exponential polynomials. After multiplication by a positive exponential factor, each derivative step removes the lowest exponential term. When every derivative root and endpoint/critical sign is exact, recursive Rolle/monotonicity reasoning certifies the number of distinct roots on the requested interval.

## Certified complex root isolation

`function_complex_zeros` isolates zeros in finite complex rectangles. It uses exact complex solving when available and otherwise a validated argument-principle contour: structural holomorphy certification, adaptive complex-interval boundary enclosures that exclude zero, winding-number counting, and count-preserving rational rectangle subdivision. Uncertified numerical winding estimates remain diagnostic only.

## Zero geometry and oscillatory extrema

Special-function zeros are represented symbolically when closed forms are not available. `IndexedZero`, `ZeroOrdering`, `ZeroInterlacing`, and `ZeroGeometryCertificate` describe exact support, simplicity, ordering, interlacing, and completeness information.

Derivative-zero geometry feeds interval decomposition. A finite exact root set produces concrete cells; a complete infinite family can produce an indexed alternating-cell structure. This allows exact reasoning about Airy, Bessel, and classical orthogonal-polynomial behavior without truncating an infinite zero sequence numerically.

`IndexedExtremumValue` and `ExtremumEnvelope` represent exact critical values and infinite extremum families. `symbolic_extremum_range()` combines them with exact endpoint values or limits. For supported Airy and Bessel families, analytic ordering theorems reduce infinite extremum envelopes to finite exact candidates.

`IndexedTailIndex` and indexed-tail inversion represent the least zero/extremum index entering a semi-infinite domain. Same-family cutoffs and certified interlacing can reduce the symbolic selector to an ordinary integer; otherwise it remains exact as a symbolic set-theoretic minimum.

## Periodicity, symmetry, and homogeneity

Periodicity propagates exact common periods through commensurate sums, products, and compositions. Parameter-dependent affine frequencies retain their nonzero frequency condition, and a returned period is not called fundamental unless minimality is established.

Symmetry supports a specified reflection center as well as exact center discovery for supported polynomial and affine-trigonometric forms. Detail results can retain families of equivalent even/odd centers and central point symmetry.

Homogeneity supports ordinary and weighted multivariate scaling. Polynomial analysis preserves exact parameter strata when coefficients determine which weighted-degree blocks survive, including the identically zero case.

## Singularities and branch cuts

`function_singularity_analysis()` performs condition-aware structural traversal of poles, removable singularities, essential singularities, branch points, branch cuts, definition cuts, and discontinuities. Piecewise guards and parameter guards are retained. Unknown primitive heads are recorded instead of silently treated as regular.

`function_branchcuts()` provides inexpensive structural pullback of principal cuts. Boundary-value and jump computations are available under `funcprops.branchcuts`.

Real analyticity and complex holomorphy are kept distinct from meromorphicity. For example, the principal logarithm is locally holomorphic on its natural complex domain but is not meromorphic on the complex plane because of its branch structure.

## Special-function property registry

The conditional registry contains SymPy/mpmath family metadata from an audited property catalogue. Catalogue values and guards are stored in deterministic SymPy constructor syntax, so rule loading does not depend on a second expression grammar. Concrete SymPy overloads are matched before guards are instantiated, and more-specific rules take precedence over generic ones. Literal pattern failures do not count as matches.

Selected special-function facts are cross-checked against the NIST Digital Library of Mathematical Functions (DLMF). The audit distinguishes direct formula-backed facts from derived wrapper/helper facts and from merely related DLMF material. The machine-readable manifest is `src/funcprops/data/dlmf_audit.json`.

## Proof cache and certificate replay

Reusable proof primitives are coordinated through a lazy `PropertyProofContext`. Constructing a context does no mathematical work. Independent bounded LRU caches hold raw and factored derivatives, natural domains, sign results, endpoint limits, zero geometry, singularity analyses, and monotonic partitions.

Cache-key normalization is intentionally inexpensive and syntactic; it does not run quantifier elimination or expensive logical simplification simply to form a key. Raw and factored derivatives use separate cache slots so callers that need only a derivative do not pay for factorization.

Certificates can be replayed with `verify_certificate()` and specialized verifiers. Convexity uses one `ConvexityCertificate` shape for ordinary, strict, and strong classifications; strong certificates additionally carry the certified modulus. Replay is conservative: an undecidable comparison never counts as a successful verification.

## Documentation

- [Function property reference](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/properties/index.md) — comprehensive definitions, API contracts, examples, applications, proof strategies, and limitations for every public `function_*` query.
- [Function properties tutorial notebook](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/notebooks/function-properties-tour.ipynb) — an executable tour built from the same tested examples as the reference documentation.
- [Architecture](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/architecture.md)
- [DLMF audit methodology](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/dlmf_audit.md)
- [Source repository](https://github.com/BhuvaneshBhatt/funcprops)

## Development

Run the test suite against the source tree with:

```bash
PYTHONPATH=src pytest
```

The package intentionally keeps exact fast paths ahead of heavier partition, root-isolation, or semialgebraic machinery. Refactors should preserve that order unless a benchmark and correctness argument justify changing it.

## License

funcprops is licensed under the GNU General Public License version 3 only
(`GPL-3.0-only`). See [LICENSE](https://github.com/BhuvaneshBhatt/funcprops/blob/main/LICENSE).