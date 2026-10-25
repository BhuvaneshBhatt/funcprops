# Implicit shared zeros, cofinal quotient search and joint refinement

Python blocks on this page form one ordered session, executed from a fresh namespace.

## Exact implications at an implicitly isolated root

```python
import sympy as s
import funcprops as fp
z = s.Symbol('z')
g = s.exp(z)-2
rect = (-1-s.I, 1+s.I)
policy = fp.EnclosurePolicy(max_cells=8192, max_depth=24, max_taylor_order=5)
held = s.Mul(g**2, g, s.Pow(g, -1, evaluate=False), evaluate=False)
q = fp.certify_quotient_isolation(held, z, *rect, policy=policy)
assert q.complete and q.verify() and q.total_count == 0
assert q.proof.extension_zero_count == q.proof.excluded_zero_multiplicity == 2
assert q.proof.source.guards == (g,)
assert any(c.guard_zero is not None for c in q.proof.cells)
```

`SharedZeroImplication` binds an entire expression F to a checked count-one base G on the same rectangle. In factor mode, replay checks F=G**m*H by exact expansion, with positive integer m and entire H. Thus F vanishes to order at least m at the unique simple zero of G, without computing that zero's coordinate. H may have other zeros: the implication alone makes no exhaustive or exact-order claim. Its completion flag is False and replay reports valid-local-proof, even when the implication itself is valid.

`SharedZeroOrderProof` combines that implication with an independently replayed F count equal to m on the same rectangle. The base zero already contributes at least m, so the finite total proves exact order m and excludes every other F zero. This count discharges the need for a separate nonvanishing-cofactor premise. Power/unit records provide exact multiplicities and retain their unit witnesses.

A cell's `guard_zero` is an implication for one unchanged original source guard at this same base zero. Together with the exhaustive numerator-order proof it excludes every numerator multiplicity there from the original source. It does not restore canceled points to the source, even if the meromorphic extension has a zero there. The guard's exact order is unnecessary for this exclusion.

## Exact outer jets and exhaustive composition orders

```python
for denominator, poles in ((s.sin(g), 0), (s.sin(g)**2, 1)):
    q = fp.certify_quotient_isolation(g/denominator, z, *rect, policy=policy)
    assert q.complete and q.verify() and q.total_count == 0
    assert q.pole_multiplicity_count == poles
    assert q.proof.extension_zero_count == 0
    assert all(r.verify() for r in q.proof.pole_regions)
```

Composition mode checks F=H(G), with an exact entire outer expression H in its own unconstrained coordinate, and exact zero derivatives H^(k)(0)=0 for 0<=k<m. A simple G zero then contributes order at least m. The independent F count m again proves exactness and exhaustiveness. No small numerical value or overlap of isolating boxes proves equality of roots. If sin(G) has additional zeros in the rectangle, its larger total cannot certify order one at G's zero.

```python
base = s.exp(z)+1
q = fp.certify_quotient_isolation(base/s.sin(base)**2, z,
    -1+2*s.I, 1+4*s.I, policy=policy)
assert q.complete and q.verify() and q.total_count == 0
assert q.pole_multiplicity_count == q.distinct_pole_count == 1
```

The reasoning also applies to nonreal implicit roots, here at i*pi. The proposer tries existing count-one/bases, original guards and entire primitive arguments. It can recover affine inner formulas after normalization expands expressions such as exp(a+b), using exact polynomial substitution with a nonzero Gaussian- rational slope. Replay checks the submitted final identity, not this heuristic.

Automatic identity proposals use at most 512 source operations and eight affine generator candidates. Composition jet proposals respect `max_taylor_order+1`; cofinal stages increase that cap. Direct factor identities can prove larger orders without differentiated jets. General analytic gcds, root equivalence and arbitrary composition discovery remain unsupported. Failure is explicit.

## Bounded cofinal stages and a conditional completion argument

```python
run = fp.adaptive_quotient_isolation(g/(s.exp(z)-1), z, *rect, stages=0,
    policy=fp.EnclosurePolicy(max_cells=128, max_depth=0), use_newton=False)
assert run.verify() and not run.complete
run = fp.resume_adaptive_quotient_isolation(run, stages=8)
assert run.verify() and run.complete
assert run.root_count == run.distinct_pole_count == 1
contract = run.termination_contract
assert contract.verify() and contract.conditional and not contract.complete
assert contract.applicable is True
```

`adaptive_complex_isolation` and its resume function dispatch supported quotients to these same entrypoints. `QuotientIsolationRun` retains its state, base policy, next stage, boundary-depth base, mode flags and protocol identifier. Counts and all three completion flags come exclusively from the checked joint ledger. `stages=0` returns a valid unresolved seed. No finite stage is a completeness oracle.

Stages reuse `complex_isolation_policy_stage`: the starting precision stays fixed while maximum precision, refinement portfolio, series allowance, depth, Taylor order and query work allowance grow. Every earlier precision remains available. A pending attempt diagonally enumerates `(cut candidate, effort)` in N². Effort j allows q=64(j+1)^2 work per contour, at most j+1 retained precision trials, and boundary depth at most 14+j (also bounded by the stage caps).

Before a task the scheduler reserves 8q+1 units: one scheduling unit, up to two initial component counts, one bounded enrichment allowance, one optional joint Newton allowance and four child counts. Insufficient space retains the unchanged attempt at the queue head. Failed counts retain the parent. Failed cut candidates are revisited with increasing effort; a stream of fresh cuts alone would not provide this guarantee. Work counters charge proposals/evaluations and scheduling; independent replay and Python/process overhead are outside that counter.

The following is a sufficient conditional termination class, not a theorem for all supported expressions:

1. N, D and every original guard are nontrivial members of the finite entire grammar, with no free parameters and a zero-free rational outer boundary.
2. Every N and D zero is simple. Distinct unaccounted numerator/denominator zeros are separated. Any numerator collision with D or an original guard is either absent or **already covered by a checked finished cell**, using the exact-point or shared-zero certificates above. Unproved coincidences do not satisfy this premise. Already classified simple removable holes require no further box accuracy and remain in the accepted cover.
3. The existing recognized outward interval forms converge on compact sets as rectangles shrink and sufficient precision/series effort is supplied.
4. Completed cofinal stages continue without an eventual fixed resource cap; each finite primitive and replay operation can finish. Requested accuracy is a positive exact rational. Infinite wall-timeout retries that never finish stages do not meet this condition.

A fixed zero-free contour has a positive image distance from zero. Convergent forms succeed at finite boundary depth B, precision index P and series cap T, using a finite panel tree of N nodes. Its charged effort grows at most linearly in j for that fixed successful portfolio prefix; quadratic q eventually suffices. Stage growth eventually includes B, P and T. Outer counts have a fixed finite successful effort too, and their ordinary stage allowance grows without bound.

Each task has finitely many FIFO predecessors. Finite attempts and reservations therefore either advance it or defer it to a later larger stage. Fixed candidates receive arbitrarily large effort. Only finitely many N/D root projections forbid a seam; the dense central rational portfolio contains a usable cut. Both child counts eventually certify that fixed cut, and their totals are checked before an atomic replacement. Zero-free parents and shared-order records transfer by independent checked subset/base counts instead of repeating the powered count.

Two longest-side central cuts contract the maximum side by at least 2/3; a checked Newton step contracts both sides by at least 3/4 and keeps every complement. Finitely many accepted positive-path operations therefore separate the remaining finite simple zeros, avoid noncoincident guards and meet positive requested accuracy. Only a finite task tree is needed, and all its nodes eventually finish. Finished collision cells are retained unchanged. Under the stated hypotheses, the assembly eventually reports complete individual source-root/pole isolation.

`QuotientIsolationGuarantee` always has `complete=False`. Its `verify()` validates this conditional contract instance and protocol, **not** unknown hypotheses or a root count. `unproved_hypotheses` retains unknown boundary, simplicity/collision premises and unbounded completed stages. `applicable` is None until finite premises are discharged, False for a proved multiple N/D zero (or structural zero numerator), and True for an exhaustive simple checked cover, including certified simple holes. Selected multiple-root cases can complete even when this narrower guarantee is inapplicable. There is no a priori computable stage/time bound here.

Initial and resumed calls accept wall budgets, serialize only atomic checked covers and preserve attempts and the stage on interruption. The checkpoint can resume at that stage. Wall limits include child-process search/replay, with serialization/startup and recovery overhead outside the worker timeout, as described in the [budget guide](guides/budgets-and-resume.md).

## Certified joint Newton refinement

```python
small = (s.Rational(1,2)-s.I/4, 1+s.I/4)
q = fp.certify_quotient_isolation(g/s.sin(g)**2, z, *small, policy=policy)
r = fp.certify_quotient_refinement(q)
assert r.verify() and fp.verify_certificate(r)
assert len(r.cells) == 5
assert sum(c.numerator.zero_count for c in r.cells) == 1
assert sum(c.denominator.zero_count for c in r.cells) == 2
```

`QuotientNewtonRefinement` binds the original source, parent cell, original-guard contours, Krawczyk witness, child and four complement strips. The source-domain premise rules out nowhere-defined canceled sources. The checker independently verifies the contraction, exact partition and both divisor totals. It preserves source zeros, poles and excluded extension zeros whenever those counts are known.

A shared-order component transfers its multiplicity along the simple base's refined count-one/count-zero regions (`SharedZeroRegion`). An power factor uses its existing transfer record. A zero-free component transfers to a closed subset (`ComplexZeroSubsetProof`). Other components need independent counts on every child; failed counts discard the whole proposed refinement. Original guard exclusions and zero implications are retained/rebound on each child.

```python
q = fp.certify_complex_isolation(1/g, z, *rect, policy=policy,
    max_box_width=s.Rational(1,100), use_newton=True)
assert q.complete and q.verify() and q.refinements
assert all(r.verify() for r in q.refinements)
assert all(p.verify() for p in q.proof.pole_regions)
```

Automatic refinement is optional (`use_newton=False` selects the contour fallback) and uses bounded proposal work. Native and public root APIs honor this flag for quotients. The proof retains all accepted refinement records. Checkpoint paths include arbitrary strict rational cuts needed to describe a Newton child/strip; ordinary candidate cuts remain central and longest-side. Each Newton operation requires room for up to four path cuts within the depth budget.

The standalone helper accepts a checked quotient proof/state and `cell_index`, and returns a replayable record or None. A wall budget puts its parent replay inside the worker. It does not mutate or automatically install the returned refinement in its parent; automatic search assembles the same records into its ledger. Newton remains an acceleration: it supplies no broader completion class.

## Remaining scope

The grammar, exact source restrictions and zero-free outer-boundary requirements remain those in [quotient-isolation.md](quotient-isolation.md). The quotient search does not resolve general analytic root equivalence, branch charts, parameters, boundary-root ownership, zero numerators or essential singularities. Individual, coverage and requested-accuracy completion remain separate. Replay trusts the existing interval primitives and SymPy exact arithmetic/differentiation; this is an internal mathematical argument, not an external proof-assistant development. These proof and checkpoint contracts belong to funcprops.
