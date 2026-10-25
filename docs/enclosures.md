# Real enclosures and proof records

An enclosure bounds every value of the original expression on a stated real cell. It is useful for excluding roots, proving a derivative sign or bounding a function without solving it symbolically.

`enclose_expression` and `enclose_derivative` return outward rational bounds with stored precision and series limits. `EnclosurePolicy` bounds refinement, cell count, depth, series terms and elapsed time. A failed refinement retains valid earlier bounds. A zero-cell budget cannot certify an enclosure.

## Bound premises

`CoverageContext` binds the expression, coordinate assumptions, requested and effective sets, domain evidence, parameter guard, substitutions and branch context. `source_syntax` retains held SymPy syntax. Construct `Mul(x, Pow(x, -1, evaluate=False), evaluate=False)` to preserve the hole of x/x before analysis; an already simplified constant cannot recover it.

The real grammar includes exact rational arithmetic, pi, E, supported elementary functions, erf/erfc, Abs and constant real powers where their domain premises can be proved. Floating coefficients, unsupported heads, unresolved parameters and incompatible coordinate assumptions produce obligations. Real proofs use principal real branches. A `CellDomainWitness` can prove definition on the requested cells even when a global natural-domain formula is unavailable.

## Checkable leaves

| Theorem | Evidence | Obligation |
| --- | --- | --- |
| `interval-exclusion` | Value bounds | Zero lies outside the source image |
| `monotone-crossing` | Derivative and endpoint bounds | C1 extension, strict derivative sign and owned crossing |
| `interval-newton` | Midpoint, value and derivative bounds | Checked Newton image inclusion or exclusion |
| `taylor-exclusion` | Coefficients and derivative remainder | Actual jets and a strict nonzero remainder enclosure |
| `rational-sturm` | Numerator and denominator coefficients | Source binding, Sturm counts and multiplicities |
| `point-zero`, `point-exclusion` | Exact value or outward bound | Owned singleton and checked substitution |

`CoverageLeaf` supplies a local count. `CoverageProof` also checks disjoint ownership, exact union, unresolved cells and totals. `CheckOutcome` separates valid local proof, complete coverage, inadmissible strata, rejected evidence, unsupported replay and resource exhaustion.

## Trust and replay

The real checker reconstructs the stated inequalities without calling search or root isolation. It trusts SymPy exact arithmetic, differentiation, domain/set reasoning and Sturm routines, plus mpmath outward interval primitives. This is a computer algebra certificate system, not a proof-assistant formalization. `replay_status` and `proof_api_manifest()` distinguish independent witnesses, backend adapters and factory-based checks.

See the [real coverage tutorial](tutorials/real-root-coverage.md) and [contracts](reference/result-contracts.md).
