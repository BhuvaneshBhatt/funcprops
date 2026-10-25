# Certified quotient zeros and transcendental poles

Python blocks on this page form one ordered session, executed from a fresh namespace.

## Public use

```python
import sympy as s
import funcprops as fp
z = s.Symbol('z')
rectangle = (-1-s.I, 1+s.I)

q = fp.isolate_complex_roots((s.exp(z)-2)/(z+2), z, rectangle)
assert q.complete and q.verify() and q.root_count == 1
assert q.pole_multiplicity_count == 0
p = q.isolation_certificate
assert p.holomorphic_on_rectangle
assert all(w.verify() for w in p.denominator_exclusions)
```

```python
q = fp.isolate_complex_roots((s.exp(z)-2)/(s.exp(z)-1), z, rectangle)
assert q.complete and q.verify()
assert q.root_count == q.distinct_pole_count == 1
assert q.total_count == q.pole_multiplicity_count == 1
assert q.winding_count == 0
assert all(r.verify() for r in q.pole_regions)
assert fp.replay_status(q).factory_replay is False
```

`isolate_complex_roots` and `complex_zeros` route supported nonalgebraic quotients to this implementation. The algroots route retains precedence for supported algebraic inputs. Native `certify_complex_isolation` and `resume_complex_isolation` also dispatch to quotient states. The dedicated entrypoints are `certify_quotient_isolation`, `resume_quotient_isolation`, and `check_quotient_isolation`. `QuotientIsolationState.proof` is a frozen `QuotientIsolationProof`; public results expose it as `isolation_certificate`. All mathematical conclusions bind the source syntax and coordinate assumptions.

## Grammar and source restrictions

Use one unconstrained complex Symbol, exact Gaussian-rational rectangle corners, and the existing entire grammar. Rational arithmetic (addition, multiplication, and integer powers, including inverses) may combine entire expressions. Entire function arguments must themselves belong to the entire grammar; `exp(1/z)` is outside this scope. There are no free parameters, floating source constants, branch powers, logarithms, conjugation or Piecewise expressions.

Explicit tan/cot/sec/csc and tanh/coth/sech/csch with entire arguments are converted to their sine/cosine or hyperbolic quotients. The corresponding original denominator restriction is retained. This is an explicit meromorphic rule, not a rewrite of arbitrary functions to exponential form.

The structural parser gives an entire pair A/B and a tuple of entire guards. The original source is defined exactly where every guard is nonzero. An inverse adds the numerator of its recursively parsed base to the guards; the base's existing guards remain. Thus nested reciprocals and held zeroth powers do not erase an inner source hole. The parser performs no cancellation.

The proposer may submit a smaller pair N/D and entire factor C. Replay checks A=C*N and B=C*D by exact arithmetic expansion, with all source guards unchanged. It never calls cancel, factor, solveset or the proposing algorithm. A quotient already simplified by its caller cannot recover erased source syntax.

The contour contract requires N, D and every original guard to be nonzero on the whole outer boundary. Failure leaves the original rectangle unresolved, including a canceled source hole on that boundary. An identically zero numerator currently remains unresolved; this finite-isolation contract provides no representation for infinitely many zeros of such a quotient.

## Local lemmas and assembly

Every counted cell contains independently checked native counts for N and D. The cells plus explicit unresolved rectangles exactly tile the requested rectangle, with disjoint interiors. Each local N/D contour is zero-free, so a zero or pole is never counted twice on shared cell edges. Counts on every accepted split add to the counted parent's counts. Source holes can intersect internal edges; they are excluded by the same original guard formula on both sides, and no N/D zero lies on those edges.

* If N has no zeros and D has d zeros, the cell has no source zeros and d poles with multiplicity. A count-one denominator proves a simple pole; a larger count remains a pole cluster unless a multiplicity proof establishes one individual multiple zero.
* If D has no zeros and N has n zeros, transferring those zeros to the source requires a `DenominatorExclusionProof` for every raw guard on the cell. Each exclusion binds an independently checked entire count-zero contour on the cell or a containing rectangle. Count zero plus the zero-free contour proves nonvanishing on the full closed rectangle.
* All N zeros in a cell can instead be proved excluded from the source. Either an original guard is an entire multiple of N, all N zeros are proved to equal an exact rational point where a guard vanishes, or an implicit shared-zero order/guard implication proves every N zero excluded.
* A positive N count and positive D count do not imply a cancellation. Unless independently located at the same point or tied to the same unique simple base by an exhaustive shared-order proof, the cell stays unresolved or is subdivided until the zeros separate.

`ExactLocalZeroProof` checks a Gaussian-rational interior point c, a verified count m, and exact zero derivatives through order m-1 at c. The order is at least m, and the finite exhaustive count m proves it is exactly m, with no other zero in the cell. It works for simple zeros as well as selected repeated zeros. No small numerical derivative or approximate center proves a coincidence. If N and D have exact local orders n and d at the same point, the meromorphic order is n-d. The point is excluded from the raw source because D vanishes. It is a pole of order d-n when d>n, and a removable source hole otherwise. When n>d, the extension has a zero there, but the original source has no zero at that excluded point.

Automatic exact-point proposals try zero and the cell's rational midpoint, subject to the Taylor-order/work policy. Exact jet records can also be supplied and replayed directly. Shared-zero witnesses prove selected nonrational coincidences through exact factor/composition identities plus exhaustive counts. General analytic root equivalence remains unsupported; no numerical coincidence is accepted.

The checker validates source identities, every local count and exclusion, exact point jets, the tiling, and the outer/local totals. Region and source records reject self-attesting subclasses. `QuotientCellProof` is an assembly payload; its source-bound standalone counterpart is `QuotientRegionProof` for a zero or pole. All accepted local regions and the full result replay with search disabled.

## Completion and count meanings

`coverage_complete` requires exhaustive zero **and** pole accounting, including counted clusters. `isolation_complete` additionally requires every positive zero and pole region to represent one individual point. `accuracy_complete` also requires both root and pole boxes to satisfy the requested positive rational `max_box_width` and/or `max_box_diameter`. `complete` requires all three. Unresolved source collisions keep coverage incomplete. Known clusters retain multiplicity totals without inventing distinct counts.

* `total_count` / `multiplicity_count`: zeros of the original, defined source, counted with multiplicity, available only after complete coverage.
* `root_count` / `distinct_root_count`: distinct source zeros, available after individual isolation; a remaining pole cluster also keeps this joint ledger's distinct counts unavailable.
* `pole_multiplicity_count`: poles of the meromorphic extension, with multiplicity.
* `distinct_pole_count`: distinct poles after individual isolation.
* `extension_zero_count`: zeros of the meromorphic extension, with multiplicity.
* `excluded_zero_multiplicity`: extension zeros omitted from the raw source.
* `winding_count`: checked outer N count minus checked outer D count. With complete coverage this equals extension_zero_count-pole_multiplicity_count. It need not equal the original source's root multiplicity count minus its pole count.

The following example has one extension zero and no source zeros:

```python
f = s.Mul(z, s.Pow(z, -1, evaluate=False), s.exp(z)-1, evaluate=False)
q = fp.certify_quotient_isolation(f, z, *rectangle)
assert q.complete and q.verify() and q.root_count == 0
assert q.proof.extension_zero_count == q.proof.excluded_zero_multiplicity == 1
assert q.proof.winding_count == 1
assert q.proof.source.guards == (z,)
```

```python
q = fp.certify_quotient_isolation(s.sin(z)/(s.exp(z)-1)**3, z, *rectangle,
    policy=fp.EnclosurePolicy(max_taylor_order=5))
assert q.complete and q.verify()
assert q.root_count == 0 and q.pole_multiplicity_count == 2
```

## Bounded search and resume

One query-wide `max_cells` allowance charges contour evaluations, optional factor/multiplicity proposals, exact-point proposals, and source cancellation. Replay cost is not measured by that work counter. The search is FIFO and uses the existing central rational split portfolio on a longest side. Failed child counts never remove a parent. Precision and boundary/depth allowances remain bounded by the policy. The separate adaptive quotient API supplies 's cofinal schedule and its explicitly conditional simple-root/certified-collision guarantee. adds optional joint Newton transfer with retained root-free complements.

Frozen checkpoints retain every accepted cell and every pending path/attempt. Atomic updates preserve exact coverage. Wall-budget workers publish quotient checkpoints; timeout before the first checkpoint produces a source-bound unresolved seed. Resume validates the checkpoint and source before continuing. Symbolic cancellation runs inside the wall-budget worker and can be retried from an initial timeout seed. Root-free complements and all holes remain covered.

```python
q = fp.certify_quotient_isolation((s.exp(z)-2)/(s.exp(z)-1), z, *rectangle,
    policy=fp.EnclosurePolicy(max_cells=0))
assert q.verify() and not q.complete
q = fp.resume_complex_isolation(q)
assert q.complete and q.verify() and q.distinct_pole_count == 1
```

General branch-chart gluing, arbitrary parameters, essential singularities, boundary ownership and complete nonrational coincidence detection remain future work. Contour-moment candidate discovery is a separate possible acceleration; it must submit witnesses to this checker and cannot change completion rules.

## Meromorphic count API

`meromorphic_rectangle_count` accepts exact rational inputs and supported supported transcendental quotients, returning `QuotientContourCertificate`. Its `zeros`, `poles`, and `winding` are divisor counts of the meromorphic extension; `source_zero_count` is the original source's zero multiplicity count. The wrapper needs exhaustive accounting, but does not require individual isolation or box accuracy. It declines unresolved coincidences. The underlying proof remains available as `.proof`, with all original source exclusions.

```python
c = fp.meromorphic_rectangle_count(s.sin(z)**3/(s.exp(z)-1), z, *rectangle)
assert c.verify() and c.complete
assert (c.zeros, c.poles, c.winding, c.source_zero_count) == (2, 0, 2, 0)
assert fp.replay_status(c).factory_replay is False
```

## Standalone source definition

Standalone pole proofs carry raw-guard contours. A canceled formal factor can be identically zero, leaving the original source nowhere defined. A meromorphic extension therefore requires nontriviality of every original guard. Both full isolation proofs and standalone local pole records check this premise. The verifier registry accepts exact registered record types and rejects unregistered self-attesting subclasses.
