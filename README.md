# funcprops

`funcprops` is a SymPy-backed package for global mathematical properties of real, complex, and multivariate functions — including domains, ranges, zeros, monotonicity, convexity, regularity, singularities, extrema, mapping properties, and transformation geometry —while supporting assumptions, parameter-dependent answers, and replayable proof certificates. It combines a conditional function property registry, exact semialgebraic reasoning from the semialgebraic geometry package `semialg`, exact algebraic geometry from `algroots`, transcendental interval analysis, special-function zero geometry, and branch-cut/singularity analysis.

When a result cannot be established by the available symbolic, semialgebraic, theorem-based, or validated numerical methods, `funcprops` preserves unresolved conditions or returns "unknown" for the result.

## Installation

```bash
pip install funcprops
```

The runtime requires Python 3.11+, SymPy 1.14+, mpmath 1.3+, semialg 1.3.2+, algroots 0.3.0+ and exprtest 0.1.0+.

## Quick start

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")

fp.domain(sp.sqrt(x - 1), x)
# x >= 1

fp.range(x**2, x, y)
# y >= 0

fp.monotonicity(sp.exp(x), x)
# Monotonicity.STRICTLY_INCREASING

fp.convexity(x**2, x)
# Convexity.STRONGLY_CONVEX

fp.complete_monotonicity(sp.exp(-x), x, domain=sp.Interval(0, sp.oo))
# TruthValue.TRUE

fp.periodicity(sp.sin(2*x) + sp.cos(3*x), x, return_result=True).period
# 2*pi

fp.branch_cuts(sp.log(1 - z), z)
# (z > 1,)

fp.geometry(x**2, x).minimum_exists.exists
# True

fp.jacobian((2*x + y, x - y), (x, y))
# Matrix([[2, 1], [1, -1]])

fp.change_of_variables((2*x + y, x - y), (x, y)).volume_factor
# 3
```

All root-level property queries use the same public conventions: scalar analysis variables are named `variable`, multivariate variables are named `variables`, `assumptions=` carries symbolic assumptions, and `return_result=True` requests the detailed result/proof view (without changing the default mathematical answer).

```python
a = sp.symbols("a", real=True)

fp.injective(a*x, x)
# parameter-stratified answer: a != 0 -> true; a = 0 -> false

detail = fp.convexity(x**2, x, return_result=True)
print(fp.explain_result(detail))
```

To discover supported high-level properties interactively:

```python
fp.properties()
fp.properties(category="mapping")
fp.properties(category="regularity")
```

## Property model

Root-level property queries return exact classifications when the available proof machinery is sufficient. `PropertyResult` and `ConditionalExpression` retain parameter strata instead of collapsing unresolved guards into one answer, and `PropertyResult.as_piecewise()` provides a Piecewise-style view when useful.

## Result conventions

Mathematical values are the default.  Boolean-style properties use `TruthValue.TRUE`, `TruthValue.FALSE`, and `TruthValue.UNKNOWN`; categorical properties use their corresponding enum with an `UNKNOWN` member. Parameter dependence is represented by `PropertyResult`.

Detailed results are opt-in (via the option return_result=True) and consistent across the root API:

```python
result = fp.monotonicity(a*x, x, return_result=True)
print(result)
print(fp.explain_result(result))
```

In notebooks, conditional and detailed results render as compact tables so the mathematical answer is prominent and proof metadata remains secondary.

## Real-domain analysis

`funcprops` owns the public property vocabulary. For semialgebraic functions on semalgebraic real domains it delegates exact domain, range, sign, monotonicity, convexity, smoothness, and mapping problems to `semialg`, while retaining stronger `funcprops` certificates when they are already available.

The main real-analysis queries are:

- `domain()` and `range()`;
- `sign()` and `boundedness()`;
- `monotonicity()` and `oscillation()`;
- `convexity()` and `complete_monotonicity()`;
- `injective()`, `surjective()`, and `bijective()`;
- `continuous()`, `differentiability()`,
  `smoothness()`, and `analytic()`;
- `periodicity()`, `symmetry()`, and
  `homogeneity()`.

Mixed variable/parameter domains are split by shared stratification layer and analyzed branch by branch. Finite `Piecewise` expressions use the same effective branch representation, with each property adding only the interface conditions it requires.

## Monotonic partitions, inverse solving, and real roots

`MonotonicPartition` is the shared exact interval representation used by monotonicity, range, injectivity, inverse solving, oscillation, and extrema. Finite partitions retain exact critical points and endpoint behavior; infinite oscillatory partitions retain indexed zero geometry without truncating an infinite sequence.

`solve_monotonic_inverse()` and `certified_monotonic_inverse()` reuse those cells to isolate inverse solutions. Real-root isolation is domain-cell aware: poles, logarithmic boundaries, radical boundaries, Piecewise switch points, and other exact exclusions split the problem before interval certificates are constructed. Identically-zero interval cells remain part of the mathematical zero set.

For supported exponential polynomials, `exponential_fourier_count()` provides a restricted derivative-sequence root counter. Exact endpoint and critical-point signs then certify the number of distinct roots on an interval.

## Zero geometry and oscillatory extrema

Special-function zeros are represented symbolically when closed forms are not available. `IndexedZero`, `ZeroOrdering`, `ZeroInterlacing`, and `ZeroGeometryCertificate` encode support, simplicity, ordering, interlacing, and completeness.

`IndexedExtremumValue`, `ExtremumEnvelope`, and indexed-tail inversion extend the same exact representation to infinite extremum families. Supported Airy, Bessel, and classical orthogonal-polynomial families can therefore participate in range, boundedness, and inverse reasoning without numerical truncation.

## Singularities, branch cuts, and complex zeros

`singularity_analysis()` performs condition-aware structural traversal of poles, removable and essential singularities, branch points, branch cuts, definition cuts, and discontinuities. Multivariate loci retain their joint conditions instead of being projected onto an artificial scalar coordinate.

`branch_cuts()` provides inexpensive structural pullback of principal cuts; boundary-value and jump computations are available under `funcprops.branchcuts`.

`complex_zeros()` isolates zeros in finite complex rectangles. It uses exact complex solving when available, otherwise a validated argument-principle contour with structural holomorphy checks, complex-interval boundary enclosures, winding-number counting, and count-preserving rational subdivision. Uncertified numerical winding estimates remain only diagnostic.

## Function geometry and attainment

`geometry()` combines regularity, singularity, convexity, boundary escape, level-boundedness, and structural mode-existence information in one summary. Related focussed queries are:

- `boundary_behavior()` for certified limits at unbounded boundaries;
- `level_boundedness()` for a compact coercivity classification, with certificates via `return_result=True`;
- `mode_existence()` for compact structural minimum/maximum attainment, with proof metadata via `return_result=True`.

The attainment machinery is implication-based. Failure to establish continuity, closedness, or level-boundedness yields an unresolved result.

## Transformation geometry

For an explicit coordinate map, `funcprops` can compute and certify:

- `jacobian()` — exact Jacobian matrices by default, with derivative certificates via `return_result=True`;
- `determinant_nonvanishing()` — domain-wide nonvanishing of `det J`;
- `local_invertibility()` — inverse-function-theorem certificates;
- `change_of_variables()` — the local volume factor `Abs(det J)`;
- `transformation_geometry()` — combined transformation summary.

A nonzero Jacobian determinant proves local invertibility, not global injectivity. The API keeps those claims separate so change-of-variables reasoning does not silently overstate a local theorem.

## Special-function registry and provenance

The conditional registry stores audited special-function metadata and exact parameter guards in deterministic SymPy constructor syntax. Concrete overloads are matched before guards are instantiated, and more-specific rules take precedence over generic ones.

Selected identities and real-variable facts are cross-checked against the NIST Digital Library of Mathematical Functions (DLMF). The machine-readable audit manifest is `src/funcprops/data/dlmf_audit.json`; see [the DLMF audit methodology](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/dlmf-coverage.md).

## Statistical special functions

The theorem registry includes probability- and statistics-oriented facts for `loggamma`, digamma/polygamma, incomplete and regularized Gamma/Beta functions, `erf`/`erfc`, modified Bessel families, and generalized Marcum Q.

For statistical functions not represented by the supported SymPy release, `funcprops` provides lightweight symbolic heads:

- `OwenT(h, a)`;
- `MittagLefflerE(alpha, z)` and `MittagLefflerE(alpha, beta, z)`;
- `RegularizedGammaP(a, x)` and `RegularizedGammaQ(a, x)`.

These heads are simply symbolic theorem carriers, not replacements for numerical libraries. Parameter-sensitive statements are guarded: outside a certified parameter/domain stratum the property engine returns a conditional or unknown result. Complete-monotonicity support includes elementary exponential kernels, Pollard-type Mittag-Leffler results, and supported Bessel-K regimes.

See [Statistical special functions](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/statistical-special-functions.md) for the current theorem coverage and provenance notes.

## Proof cache and certificate replay

Reusable proof primitives are coordinated through lazy `PropertyProofContext` objects. Independent bounded caches hold derivatives, natural domains, sign results, endpoint limits, zero geometry, singularity analyses, and monotonic partitions. Cache-key normalization is syntactic and avoids expensive proof work to construct a key.

Proof objects can be "replayed" with `verify_certificate()` and specialized verifiers. For replay, an undecidable comparison never counts as a successful verification.

## Capabilities and limits

| Task | Supported scope | Completion boundary |
| --- | --- | --- |
| Domains, range and sign | Structural rules, exact restriction transfer, selected semialgebraic and elementary families | Source definition and every requested restriction remain premises |
| Shape and regularity | Monotonicity, convexity, symmetry, periodicity, finite metric constants, variation and supported Piecewise seams | Cell coverage, global order and replay support are separate |
| Exact coefficients | Up to four real algebraic constants in a field of degree at most four | Larger fields and coefficient parameters can decline the lift |
| Parameter roots | Selected uniform families and rational polynomial geometry of degree at most four with up to four real parameters | Every parameter region needs a count or an explicit unresolved status |
| Real roots and extrema | Compact covers, selected multiple roots, periodic families, tails and outward extrema bounds | Every source region needs a root or exclusion proof |
| Complex roots and poles | Algebraic enumeration, supported entire/quotient contours, subdivision and Newton refinement | Declared grammar, rational rectangles, source guards and clear boundaries |
| Branches and local analysis | Finite atlases, supplied holomorphic recipes, implicit orders, residues, selected essential-series/classification rules and continuation | Selected local values do not redefine global principal expressions; essential-singularity isolation is unsupported |
| Certified operations | Supported equations, inverses, integration, winding and homotopy | Each operation has its own premises and replay contract |

General transcendental parameter geometry, automatic discovery of arbitrary implicit branches, unrestricted branch-surface gluing, arbitrary analytic common-factor discovery and essential-singularity isolation remain capability gaps. Bounded work can leave supported problems partial. See the [full matrix](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/capabilities.md), [result contracts](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/reference/result-contracts.md) and [troubleshooting](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/troubleshooting.md).

## Documentation and examples

- [Documentation index](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/index.md)
- [Function property reference](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/properties/index.md) — canonical reference pages for every public function property
- [Working with results, assumptions, certificates, and caches](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/using-results.md)
- [Executable tutorial notebook](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/notebooks/function-properties-tour.ipynb) — generated from the same canonical example corpus used by the reference pages
- [Task tutorials by level](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/tutorials/index.md)
- [Runnable examples](https://github.com/BhuvaneshBhatt/funcprops/blob/main/examples/README.md)
- [Workflow notebook](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/notebooks/certified-workflows.ipynb)
- [Statistical special functions](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/statistical-special-functions.md)
- [Mathematical conventions](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/mathematical-conventions.md)
- [Complex analysis](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/complex-analysis.md)
- [Homotopy and contour deformation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/homotopy.md)
- [Capability matrix and limitations](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/capabilities.md)
- [Architecture](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/architecture.md)
- [Proof design](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/design/index.md)
- [Testing](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/guides/testing.md)
- [DLMF property-table audit](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/dlmf-coverage.md)
- [Source semantics](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/source-semantics.md)
- [Domains and branches](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/guides/domains-and-branches.md)
- [Budgets](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/guides/budgets-and-resume.md)
- [Certification model](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/certification.md)

The canonical examples live in `examples/property_examples.py`. Documentation specification tests execute those examples and verify that the reference and notebook stay synchronized with the public API.

## Development

Contributions – whether they are bug reports, suggestions, or code – are welcome!

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

The package keeps exact fast paths ahead of heavier partition, root-isolation, or semialgebraic machinery. Structural refactors should preserve that ordering unless a benchmark and correctness argument justify changing it.

## License

`funcprops` is licensed under the GNU General Public License version 3 only
(GPL-3.0-only). See [LICENSE](https://github.com/BhuvaneshBhatt/funcprops/blob/main/LICENSE).
