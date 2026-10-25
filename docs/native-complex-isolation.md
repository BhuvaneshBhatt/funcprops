# Native complex isolation

Python blocks on this page form one ordered session, executed from a fresh namespace.

## APIs and example

```python
import sympy as s
import funcprops as fp

z = s.Symbol('z')             # unconstrained complex coordinate
state = fp.certify_complex_isolation(s.sin(z), z, -4-s.I, 4+s.I)
assert state.complete and state.verify()
assert state.root_count == state.multiplicity_count == 3
assert len(state.isolating_boxes) == 3
assert fp.check_complex_isolation(state.proof).certified is True

result = fp.complex_zeros(s.exp(z)+1, z,
    rectangle=(-1-4*s.I, 1+4*s.I), return_result=True)
assert result.complete and result.root_count == 2
assert result.isolation_certificate.verify()
assert result.state.verify()
```

`certify_complex_isolation` returns a frozen `ComplexIsolationState` containing the frozen `ComplexIsolationProof` and pending work. The corresponding public `isolate_complex_roots` and `complex_zeros` routes expose this same proof as `isolation_certificate` and checkpoint as `state`. Algebraic results retain `algebraic_certificate`. `result.proof` selects the relevant certificate. `verify_certificate` and `replay_status` support the proof, checkpoint and public result. Native replay reports `factory_replay=False`; algroots replay continues to be labeled as a backend adapter. Factory-based unsupported branches retain their existing replay limitations.

## Scope and theorem

Use one default complex Symbol, no additional free parameters, exact rational rectangle corners, and the existing entire grammar: rational constants, I, pi, E, addition, multiplication, nonnegative integer powers, and compositions of exp, sin, cos, sinh, cosh, erf and erfc. The contour and isolation checkers share outward complex enclosure primitives. Inconclusive bounds do not establish a count.

The native query is for the whole closed rectangle. It first certifies a zero-free outer boundary. A boundary zero leaves the outer region unresolved. No boundary root is assigned to one side by a numerical convention. General branch charts, source poles, free parameters and extra native domain/condition restrictions are outside this starting class. The public algebraic route still supports its documented domains, guards and principal rational-power sources.

An accepted contour count is the number of zeros with multiplicity. Count zero excludes roots, count one proves exactly one simple root, and count greater than one remains a cluster unless a multiplicity proof isolates one individual multiple zero. A positive cluster alone proves neither its number of distinct roots nor their individual multiplicities. Native boxes do not claim exact symbolic locations or classify a zero as real from a positive count.

## Three completion fields

| Field | Meaning |
| --- | --- |
| `coverage_complete` | Every point is covered by counted leaves, with no unresolved regions and a certified outer contour. Clusters are permitted. |
| `isolation_complete` | Coverage is complete and every positive leaf proves one individual zero, either simple or with a multiplicity proof. |
| `accuracy_complete` | Individual isolation is complete and every root box meets the requested maximum side length, if supplied. |
| `complete` | All three requirements hold. |

`total_count` / `multiplicity_count` is available when coverage is complete. `root_count` / `distinct_root_count` is available when individual isolation is complete, even if the requested accuracy is unmet. Without a requested width, accuracy imposes no additional obligation beyond individual isolation. Empty root sets meet accuracy vacuously.

Use `coverage_complete` when only an exhaustive multiplicity count is required.

```python
q = fp.certify_complex_isolation(s.sin(z)**2, z, -1-s.I, 1+s.I,
    policy=fp.EnclosurePolicy(max_depth=0), use_multiple=False)
assert q.verify() and q.coverage_complete
assert q.multiplicity_count == 2 and q.root_count is None
assert not q.complete and len(q.clusters) == 1
```

## What assembly replay checks

The proof binds the raw source syntax, coordinate assumptions, outer rectangle, outer contour, zero leaves, root leaves, clusters, unresolved rectangles, target width and derived totals/flags. Replay:

1. Checks the schema, source binding and entire grammar.
2. Replays contour counts and any checked Newton count transfers.
3. Uses the existing exact rectangle partition checker to establish full geometric coverage and disjoint interiors. Omitted or duplicated leaves, overlap, and altered rectangles are rejected.
4. Checks zero/individual/cluster classifications, selected multiplicity proofs and all derived fields.
5. For full counted coverage, compares the sum of leaf counts with the outer count. Whole-query counts stay unavailable for unresolved covers.

Every counted region proves its entire boundary nonzero, including shared edges and corners, through its contour or checked Newton transfer. Unresolved regions make no count or clear-boundary claim; the full assembly cannot be complete while they remain. Strict record types at the proof boundary prevent self-attesting contour/image subclasses from replacing the arithmetic checks.

Replay never invokes subdivision, root solving, split selection or contour proposal. It recomputes the declared primitive bounds and exact geometry. SymPy, the outward arithmetic primitive and rational operations remain trusted; this is not external formal verification.

## Fair subdivision and seam handling

Pending work uses a FIFO queue. A failed attempt moves to the back; accepted children join the back. Each task remembers its attempt number and exact split path. Cuts use a dense van der Corput rational portfolio in the central third of a longest side. This avoids repeatedly accepting a shorter-side cut while leaving the requested maximum width unchanged.

Both child contour counts must be certified and sum to the parent's count before the parent is replaced. Count-zero children remain as exclusion leaves. A failed or interrupted split retains the entire parent certificate. An exact zero at a proposed edge midpoint can reject that proposal early, but is only a search hint; successful child contours establish boundary clearance.

For finitely many isolated zeros, only finitely many projected coordinates are forbidden cuts. This motivates the growing portfolio. It is not a termination theorem for the full implementation: precision, series limits, cell work and depth must also suffice. Multiple roots can remain positive clusters indefinitely.

## Budgets and resume

`EnclosurePolicy.max_cells` is one query-wide search budget. It charges all boundary attempts, including failed child counts, plus one outward midpoint probe per split. Replay arithmetic, source setup, serialization and queue bookkeeping are not cell units. additionally charges two outward jet evaluations per attempted precision, including failed Newton attempts. The cumulative `state.tested` records charged work across resumes. Per-task contour quotas grow with its retained attempt number; uses the policy's bounded precision portfolio and series allowance.

`policy.max_depth` limits isolation split depth. A Newton contraction charges four split levels: its exact child path cuts off four complement strips. `max_boundary_depth` separately limits boundary subdivision. Depth-blocked tasks remain pending. `policy.seconds` adds a process-isolated wall budget covering worker setup, validation, search and worker replay. It returns the last fully serialized checkpoint on expiry; without one, a supported native query returns an unresolved source-bound seed. Parent-side serialization, timeout recovery and process setup/shutdown add overhead outside the worker timeout. For an unsupported public query, timeout can return an uncertified incomplete result with the original query in its evidence instead of a native checkpoint.

```python
q = fp.certify_complex_isolation(s.exp(z)-1, z, -1-s.I, 1+s.I,
    max_box_width=s.Rational(1, 2),
    policy=fp.EnclosurePolicy(max_depth=0))
assert q.coverage_complete and q.isolation_complete and not q.accuracy_complete
q = fp.resume_complex_isolation(q,
    policy=fp.EnclosurePolicy(max_depth=12, max_cells=2048, seconds=10))
assert q.complete and q.verify()
```

Resume accepts a checkpoint or a native public result, validates its entire proof and exact pending frontier, and continues with a fresh per-call budget. It preserves the original source, rectangle and requested accuracy. Increase precision/series/depth/cells as needed. Tiny unchanged budgets need not make progress. A wall timeout during checkpoint validation preserves the earlier evidence without adding mathematical claims; verification is still required.

Checkpoints are ordinary frozen Python records. Trusted local programs may serialize them with pickle; never load untrusted pickle data. The replay contract describes in-memory Python records; no cross-language storage format is provided.

The public route accepts `policy` and `max_box_width`. With an explicit policy, its precision and split depth control native search; otherwise the existing `precision` and `max_isolation_depth` options supply those defaults. `max_box_width` must be a positive exact rational and measures the maximum side. `certify_complex_isolation` also accepts `max_box_diameter`, a positive exact rational bound on Euclidean diameter, checked by the squared diagonal inequality. Both constraints apply when supplied. Algebraic exact locations satisfy any positive target.

`use_newton=True` enables acceleration by default when a count-one box needs refinement. `use_newton=False` retains the fair contour-subdivision path for comparison. A failed contraction keeps the parent and falls back to subdivision. `state.refinements` and detailed public `result.refinements` expose the accepted Newton certificates, including their derivative bounds and inclusion images. The [refinement contract](complex-newton-refinement.md) gives the theorem, independent replay, direct helper and complete complement accounting.

`use_multiple=True` enables selected recognition. A certified count m can become one individual zero of order m only after a separate exact Taylor or power-factor theorem verifies. `individual_multiplicities` reports those orders when isolation is complete. `use_multiple=False` retains count-only clusters. Box-level `root_count` remains the factory-based multiplicity-inclusive count; `distinct_root_count` and `multiplicity_count` make its two meanings explicit. Whole-result `root_count` is the distinct-root total.

## Regression scope

The tests exercise the documented sine and exponential examples, explicit clusters/unresolved coverage, producer-disabled replay, source/count/geometry mutations, false nested evidence, checkpoint validation, reordered frontiers, failed-split fairness, axis seam avoidance, precision/series/cell/depth limits, width refinement, wall expiry, and recovery from a truncated checkpoint frame. The release report records exact source and installed-wheel results.

## Quotient and pole extension

The 16 October extension dispatches rational arithmetic over the entire grammar to a separate [quotient ledger](quotient-isolation.md). It adds denominator exclusion, source-hole tracking and selected transcendental pole accounting, with the same independent contour kernel. Its frozen checkpoints and separate coverage/isolation/accuracy fields do not extend 's entire-function termination contract. The scope restrictions above describe the original entire route.
