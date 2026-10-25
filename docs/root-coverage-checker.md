# Root coverage checker

Python blocks on this page form one ordered session, executed from a fresh namespace.

The checker separates a proposed search result from a coverage proof. The real checker does not re-run the adaptive search: it replays each leaf's local count, checks source binding, checks pairwise disjoint sets (including endpoint ownership), and checks that proved plus explicitly unresolved sets exactly cover the effective domain. A dropped endpoint is a gap. Duplicated root ownership is invalid even when the claimed total was adjusted.

```python
import sympy as sp
from funcprops import root_coverage, replay_status
x = sp.Symbol('x', real=True)

r = root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 2))
assert r.complete and r.root_count == 1 and r.verify()

p = root_coverage(sp.sin(x), x, sp.Interval(-4, 4), max_cells=0)
assert p.root_count is None and not p.complete
assert p.unresolved == sp.Interval(-4, 4)
assert replay_status(p).certified  # valid bookkeeping for an explicitly partial result
assert replay_status(p).complete is False
```

## Records and scope

RootCoverageCertificate contains the original expression/variable, DomainRecord, RootRegionProof leaves, unresolved set, scoped completeness, distinct root count and optional multiplicity count. known_root_count is the sum of verified leaf counts, not a whole-domain count when unresolved is nonempty. A certified partial record does not establish existence in unresolved cells. Unknown definition domains cannot acquire certified coverage merely by marking everything missing.

The target is the requested *effective* definition domain. Excluded source poles are retained in DomainRecord, not restored. The original source syntax must reach tracking; a quotient already simplified by the caller cannot have its lost syntax recovered. Inherited tracking currently declines logs, noninteger powers, Piecewise/discrete and some symbolic parameter domains.

Every region must be a certified counted/excluded region or explicitly unresolved. The final count exists only when the unresolved set is empty. Type-invalid flags/counts, changed sources, forged counts, deleted gaps and wrong parameter substitutions fail replay. verify_certificate and replay_status accept the real, parameter-specialized and complex records.

## Implemented proof leaves

- **Compact simple roots:** outward interval function/derivative enclosures, strict monotonicity and endpoint signs; adaptive bisection partitions cells with explicit endpoint ownership. A monotone endpoint-exclusion lemma proves an open cell root-free when its only possible root is at its unowned endpoint.
- **Exact rational functions:** rational-coefficient numerator root enumeration, filtered by the exact source domain. Roots include exact algebraic RootOf values. Distinct roots and multiplicities are counted separately. This gives complete multiple-root support for this class, including tangent roots. Identically-zero intervals have infinitely many roots; a finite zero set has only its finite cardinality, and no finite multiplicity is claimed for the identically-zero function.
- **Infinite periodic families:** an existing exhaustive, source-bound verified periodic root family can cover the full real line. A numerical sample of periods cannot. This root-family route requires a nonempty finite fundamental root set and a full-real effective source domain.
- **Strict tail exclusion:** existing exact coefficient/dominance tail proofs can prove supported half-infinite regions root-free. Their source, sign, direction and actual threshold support are checked. A proved tail does not establish a missing core or opposite tail. Exact global rational enumeration can alternatively cover an unbounded rational problem without truncation.
- **Parameter specialization:** specialize_root_coverage retains the original expression, exact independent parameter equalities and specialized domain. Coverage is conditional on its explicit guard. This implements concrete exact parameter cases, not automatic stratification of the whole parameter space. Contradictory Symbol-assumption guards and substitutions hiding undefined source expressions cannot certify.
- **Complex rectangles:** complex_root_coverage counts rational-coefficient polynomial roots inside a closed rectangle with Gaussian-rational corners. Each certified rectangle proves its full boundary root-free. The independent tiling checker permits shared edges, rejects overlapping interiors and gaps, and adds distinct-root and multiplicity counts separately. A zero on a contour makes that region unresolved. General transcendental/meromorphic contour coverage, nonrational coefficients and arbitrary contour topology are outside this polynomial rectangle adapter; use [native isolation](native-complex-isolation.md) for the supported entire-function grammar.

```python
from funcprops import specialize_root_coverage, complex_root_coverage

a = sp.Symbol('a', real=True)
s = specialize_root_coverage(x**2 - a, x, {a: 1}, sp.Interval(-2, 2))
assert s.guard == sp.Eq(a, 1) and s.complete
assert s.coverage.root_count == 2

z = sp.Symbol('z')
c = complex_root_coverage((z - 1)**2, z, -2-2*sp.I, 2+2*sp.I)
assert c.complete and c.root_count == 1 and c.multiplicity_count == 2
```

## Budgets and remaining limits

max_depth and max_cells bound adaptive subdivision. They are not wall-clock limits on a single underlying symbolic call or family solver. Exhausted budgets retain all unprocessed cells. Multiple roots without a supported order witness, unresolved coefficient comparisons, unproved tails and unsupported domain geometry remain partial.

The local lemmas still trust audited symbolic/interval backends; this is not a formal proof kernel. The global checker is independent of its adaptive partition producer, but a bad local theorem can still invalidate a result. Internal coordinates use fresh Dummy symbols to prevent capture of user parameters.

General transcendental completeness remains a family-by-family contract. The coverage infrastructure provides a safe place to add stronger interval Newton, multiple-root, ODE/phase, rigorous remainder/tail and complex-contour leaves without converting unsupported regions into global completeness.
