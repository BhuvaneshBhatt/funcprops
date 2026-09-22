# funcprops

`funcprops` is a SymPy-backed package for global mathematical properties of real, complex, and multivariate functions — including domains, ranges, zeros, monotonicity, convexity, regularity, singularities, extrema, mapping properties, and transformation geometry —while supporting assumptions, parameter-dependent answers, and replayable proof certificates. It combines a conditional function property registry, exact semialgebraic reasoning from the semialgebraic geometry package `semialg`, transcendental interval analysis, special-function zero geometry, and branch-cut/singularity analysis.

## Installation

```bash
pip install funcprops
```

The runtime requires Python 3.11+, SymPy 1.14+, mpmath 1.3+, semialg 1.2.0+ and exprtest 0.1.0+.

## Quick start

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")

fp.function_domain(sp.sqrt(x - 1), x)
# x >= 1

fp.function_range(x**2, x, y)
# y >= 0

fp.function_monotonicity(sp.exp(x), x)
# Monotonicity.STRICTLY_INCREASING

fp.function_convexity(x**2, x)
# Convexity.STRONGLY_CONVEX

fp.function_complete_monotonicity(sp.exp(-x), x, domain=sp.Interval(0, sp.oo))
# TruthValue.TRUE

fp.function_periodicity(sp.sin(2*x) + sp.cos(3*x), x, return_result=True).period
# 2*pi

fp.function_branchcuts(sp.log(1 - z), z)
# structural pullback of the principal logarithm cut

fp.function_geometry(x**2, x).minimum_exists.exists
# True

fp.function_jacobian((2*x + y, x - y), (x, y))
# Matrix([[2, 1], [1, -1]])

fp.function_change_of_variables((2*x + y, x - y), (x, y)).volume_factor
# 3
```

## Property model

The package preserves parameter conditions, analyzes piecewise branches on their effective domains, never upgrades incomplete numerical searches into exact proofs, and represents undecidable symbolic questions as unknown or conditional results.

API functions `function_*` return exact classifications when the available proof machinery is sufficient. `PropertyResult` and `ConditionalExpression` retain parameter strata instead of collapsing unresolved guards into one answer, and `PropertyResult.as_piecewise()` provides a Piecewise-style view when that's useful.

Proof-oriented code uses three-valued reasoning. An undecidable set relation, domain implication, branch-locus intersection, or symbolic comparison is not silently treated as false.

## Real-domain analysis

`funcprops` owns the public property vocabulary. For semialgebraic functions on semialgebraic real domains it delegates exact domain, range, sign, monotonicity, convexity, smoothness, and mapping problems to `semialg`, while retaining stronger `funcprops` certificates when they are already available.

The main real-analysis queries are:

- `function_domain()` and `function_range()`;
- `function_sign()` and `function_boundedness()`;
- `function_monotonicity()` and `function_oscillation()`;
- `function_convexity()` and `function_complete_monotonicity()`;
- `function_injective()`, `function_surjective()`, and `function_bijective()`;
- `function_continuous()`, `function_differentiability()`,
  `function_smoothness()`, and `function_analytic()`;
- `function_periodicity()`, `function_symmetry()`, and
  `function_homogeneity()`.

Mixed variable/parameter domains are split by the shared stratification layer and analyzed branch by branch. Finite `Piecewise` expressions use the same effective branch representation, with each property adding only the interface conditions it requires.

## Monotonic partitions, inverse solving, and real roots

`MonotonicPartition` is the shared exact interval representation used by monotonicity, range, injectivity, inverse solving, oscillation, and extrema. Finite partitions retain exact critical points and endpoint behavior; infinite oscillatory partitions retain indexed zero geometry without truncating an infinite sequence.

`solve_monotonic_inverse()` and `certified_monotonic_inverse()` reuse those cells to isolate inverse solutions. Real-root isolation is domain-cell aware: poles, logarithmic boundaries, radical boundaries, Piecewise switch points, and other exact exclusions split the problem before interval certificates are constructed. Identically-zero interval cells remain part of the mathematical zero set.

For supported exponential polynomials, `exponential_fourier_count()` provides a restricted derivative-sequence root counter. Exact endpoint and critical-point signs then certify the number of distinct roots on an interval.

## Zero geometry and oscillatory extrema

Special-function zeros are represented symbolically when closed forms are not available:`IndexedZero`, `ZeroOrdering`, `ZeroInterlacing`, and `ZeroGeometryCertificate` encode support, simplicity, ordering, interlacing, and completeness.

`IndexedExtremumValue`, `ExtremumEnvelope`, and indexed-tail inversion extend the same representation to infinite extremum families. Supported Airy, Bessel, and classical orthogonal-polynomial families can therefore participate in range, boundedness, and inverse reasoning without numerical truncation.

## Singularities, branch cuts, and complex zeros

`function_singularity_analysis()` performs condition-aware structural traversal of poles, removable and essential singularities, branch points, branch cuts, definition cuts, and discontinuities. Multivariate loci retain their joint conditions instead of being projected onto an artificial scalar coordinate.

`function_branchcuts()` provides inexpensive structural pullback of principal cuts; boundary-value and jump computations are available under `funcprops.branchcuts`. Real analyticity, complex holomorphy, and meromorphicity remain distinct concepts.

`function_complex_zeros()` isolates zeros in finite complex rectangles. It uses exact complex solving when available and otherwise a validated argument-principle contour with structural holomorphy checks, complex-interval boundary enclosures, winding-number counting, and count-preserving rational subdivision. Uncertified numerical winding estimates remain diagnostic only.

## Function geometry and attainment

`function_geometry()` combines regularity, singularity, convexity, boundary escape, level-boundedness, and structural mode-existence information in one summary. Related focused queries are:

- `function_boundary_behavior()` for certified limits at unbounded boundaries;
- `function_level_boundedness()` for a compact coercivity classification, with certificates via `return_result=True`;
- `function_mode_existence()` for compact structural minimum/maximum attainment, with proof metadata via `return_result=True`.

The attainment machinery is implication-based. Failure to establish continuity, closedness, or level-boundedness will yield an unresolved result.

## Transformation geometry

For an explicit coordinate map, `funcprops` can compute and certify:

- `function_jacobian()` — exact Jacobian matrices by default, with derivative certificates via `return_result=True`;
- `function_determinant_nonvanishing()` — domain-wide nonvanishing of `det J`;
- `function_local_invertibility()` — inverse-function-theorem certificates;
- `function_change_of_variables()` — the local volume factor `Abs(det J)`;
- `function_transformation_geometry()` — a combined transformation summary.

A nonzero Jacobian determinant proves local invertibility, not global injectivity. The API keeps those claims separate so change-of-variables reasoning does not silently overstate a local theorem.

## Statistical special functions

The theorem registry includes probability- and statistics-oriented facts for `loggamma`, digamma/polygamma, incomplete and regularized Gamma/Beta functions, `erf`/`erfc`, modified Bessel families, and generalized Marcum Q.

For statistical functions not represented by the supported SymPy release,
`funcprops` provides lightweight symbolic heads:

- `OwenT(h, a)`;
- `MittagLefflerE(alpha, z)` and `MittagLefflerE(alpha, beta, z)`;
- `RegularizedGammaP(a, x)` and `RegularizedGammaQ(a, x)`.

These heads are simply symbolic theorem carriers, not replacements for numerical special-function libraries. Parameter-sensitive statements are guarded: outside a certified parameter/domain stratum the property engine returns a conditional or unknown result. Complete-monotonicity support includes elementary exponential kernels, Pollard-type Mittag-Leffler results, and supported Bessel-K regimes.

See [Statistical special functions](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/statistical_special_functions.md) for the
current theorem coverage and provenance notes.

## Special-function registry and provenance

The conditional registry (which needs to be expanded) stores audited special-function metadata and exact parameter guards in deterministic SymPy constructor syntax. Concrete overloads are matched before guards are instantiated, and more-specific rules take precedence over generic ones.

Selected identities and real-variable facts are cross-checked against the NIST Digital Library of Mathematical Functions (DLMF). The machine-readable audit manifest is `src/funcprops/data/dlmf_audit.json`; see [the DLMF audit methodology](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/dlmf_audit.md).

## Proof cache and certificate replay

Reusable proof primitives are coordinated through lazy `PropertyProofContext` objects. Independent bounded caches hold derivatives, natural domains, sign results, endpoint limits, zero geometry, singularity analyses, and monotonic partitions. Cache-key normalization is syntactic and avoids expensive proof work merely to construct a key.

Proof objects can be replayed with `verify_certificate()` and specialized verifiers. Replay is conservative: an undecidable comparison never counts as a successful verification.

## Documentation and examples

- [Function property reference](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/properties/index.md) — one canonical page for every public `function_*` query.
- [Working with results, assumptions, certificates, and caches](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/using-results.md).
- [Executable tutorial notebook](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/notebooks/function-properties-tour.ipynb) — generated from the same canonical example corpus used by the reference pages.
- [Statistical special functions](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/statistical_special_functions.md).
- [Architecture](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/architecture.md).
- [DLMF audit methodology](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/dlmf_audit.md).

The canonical examples live in `examples/property_examples.py`. Documentation specification tests execute those examples and verify that the reference and notebook stay synchronized with the public API.

## Development

Run the source-tree tests with:

```bash
PYTHONPATH=src:. pytest
```

Run the static gates with:

```bash
ruff format --check src tests examples tools
ruff check src tests examples tools
python -m compileall -q src tests examples tools
```

The package keeps exact fast paths ahead of heavier partition, root-isolation, or semalgebraic machinery. Structural refactors should preserve that ordering unless a benchmark and correctness argument justify changing it.

## License

funcprops is licensed under the GNU General Public License version 3 only
(`GPL-3.0-only`). See [LICENSE](https://github.com/BhuvaneshBhatt/funcprops/blob/main/LICENSE).
