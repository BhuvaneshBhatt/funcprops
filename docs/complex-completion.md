# cofinal completeness and selected complex multiplicities

Python blocks on this page form one ordered session, executed from a fresh namespace.

## Bounded cofinal stages

```python
import sympy as s
import funcprops as fp

z = s.Symbol('z')
run = fp.adaptive_complex_isolation(s.sin(z), z, -4-s.I, 4+s.I, stages=0)
assert run.verify() and not run.complete
run = fp.resume_adaptive_complex_isolation(run, stages=4)
assert run.verify() and run.complete and run.root_count == 3
contract = run.termination_contract
assert contract.verify() and contract.conditional and not contract.complete
assert contract.applicable is True
```

For entire sources, `adaptive_complex_isolation` returns `ComplexIsolationRun`, containing the native state, base policy, next stage, boundary-depth base and mode flags. `resume_adaptive_complex_isolation` preserves that exact frontier. It also accepts a native `ComplexIsolationState`, wrapping it with the default stage policy. Every invocation runs finitely many stages. `stages=0` returns a source-bound seed. Native completion/count fields still come only from the assembly proof.

`complex_isolation_policy_stage(k, base=...)` grows maximum precision, refinements, series terms, split/boundary depth, cells and Taylor order. The starting precision stays fixed, so the growing precision portfolio retains all earlier precisions. Raising only the starting precision could discard a useful precision whose required erf series fits the current series budget.

Each task's attempt number enumerates `(candidate, effort)` diagonally in N². For a fixed candidate the effort tends to infinity. Candidate i selects the i-th central van der Corput rational cut on a longest side. At effort j the contour quantum is q=64(j+1)², with at most j+1 precision trials per boundary segment. Boundary subdivision is also capped by 14+j. Stage caps still limit all work.

Before an outer-count attempt the scheduler reserves q units. Before a split it reserves 4q+1 units, enough for the bounded recognition/refinement proposals, midpoint probe and both child counts. If insufficient work remains, the task stays at the head with the same attempt number for the next stage. Thus a hard candidate is not repeatedly tested only with a stage's leftover budget. The ordinary single-budget APIs retain their smaller partial-work behavior.

## Conditional termination argument for this protocol

This is an internal mathematical argument for the implemented protocol, not an external proof-assistant development or a claim established by finite tests. The proof kernel trusts the recognized outward arithmetic rules and exact SymPy/rational operations. The associated contract records a conditional theorem; it supplies no root count and always has `complete=False`.

### Hypotheses

1. The source is a finite expression in the documented entire grammar, with one default complex coordinate, exact coefficients and no other parameters.
2. The target is a finite nondegenerate Gaussian-rational rectangle, and the source is nonzero on its whole outer boundary.
3. Every zero in the target is simple. Distinct zeros then have a positive separation. The outer-boundary premise also rules out the identically zero function and gives finitely many zeros in the compact target.
4. The recognized outward value/derivative interval forms converge as input rectangles shrink and sufficient precision/series effort is supplied.
5. Completed cofinal stages continue without an eventual fixed resource cap; every finite primitive/replay operation can finish with sufficient storage. Requested width/diameter bounds, if supplied, are positive rationals.

The primitive convergence premise is the interval-kernel contract, not a test of an arbitrary supplied oracle. Rational constants and finite arithmetic compose convergent interval forms on compact sets; the entire primitives do likewise. For erf/erfc, the existing absolute series majorant gives a finite truncation for each fixed compact argument bound and fixed precision. Keeping earlier precisions while increasing the series cap preserves any such successful pair. Structural derivative/Taylor rules use the same entire primitives. Newton is optional; the contour fallback suffices for the argument.

The usual analytic Taylor/order facts underlying finite isolated zeros and multiplicities are described in [NIST DLMF §1.10(i)](https://dlmf.nist.gov/1.10#i). The scheduling argument below is specific to this implementation.

### A fixed contour has a finite sufficient effort

A zero-free compact contour has a positive image distance from zero. Convergent recognized enclosures therefore certify all panels at some finite dyadic boundary depth B, fixed precision portfolio index P and finite series cap T. There are finitely many nodes N in that panel-refinement tree. Before reaching the successful precision/panel, the contour search tries at most j+1 precisions per node. Its required charged work is therefore at most N(j+1). The reserved quadratic quantum 64(j+1)² eventually dominates that bound, while boundary depth, retained precision indices and series caps eventually include B, P and T. Replay checks the resulting finite contour; no limiting object is accepted as a count certificate.

### Every unfinished task receives sufficient attempts

FIFO order puts new work behind existing tasks. A fixed task has finitely many predecessors; each gets one finite attempt or is depth-deferred. Depth caps grow, so a fixed finite-depth task is eventually eligible. If its reserved work does not fit, it stays at the head without advancing its candidate/effort. Growing stage cell caps eventually accommodate that fixed reservation. Hence an unfinished task receives arbitrarily many full attempts, and every fixed candidate is retried with arbitrarily large effort. This is the missing step in a mere FIFO/growing-depth argument: neither freshness of cuts nor increasing depth alone ensures enough work on a usable cut.

### Every positive parent can be split or finished

There are finitely many root projections onto either coordinate axis. Only finitely many central cut positions are forbidden by roots on a new seam. The dense rational portfolio contains a usable candidate at a finite index. Both child contours for this fixed cut are zero-free; the preceding effort argument eventually certifies them. Their exact counts sum to the parent's count, so the atomic update succeeds. Rejected seams retain the whole parent and cannot lose a root. A successful Newton update instead contracts both sides by at least the checked factor 3/4 and retains all complement strips.

Every two accepted positive-path operations contract the maximum side by at least 3/4: two longest-side central binary cuts contract it by at least 2/3, and any Newton contraction already supplies the 3/4 bound. Thus a fixed finite number of accepted operations makes the diameter smaller than both the root separation and any requested positive accuracy. The corresponding split depth is finite (a Newton step records four cuts), and stage depth caps eventually permit it. Every remaining positive box then has count one and meets accuracy. The tree has finite branching and bounded required positive-path length, hence only finitely many tasks are needed. Each task finishes in finite effort as above. The native checker therefore eventually accepts a complete individual isolation.

No assumption here asserts a computable a priori stage/time bound. A boundary zero, unrecognized source, multiple zero outside 's selected proofs, fixed wall timeouts or permanently insufficient arithmetic may prevent completion.

## Contract status and wall checkpoints

`ComplexIsolationGuarantee.unproved_hypotheses` lists outer-boundary nonvanishing until certified, simplicity until established by an exhaustive simple cover, and unbounded completed cofinal stages. Its `applicable` is False when the current proof establishes a multiple root, None while finite-query premises are unresolved, and True when they are discharged. Its replay certifies only this conditional theorem instance, never the unproved premises or a root count. Changing the protocol/theorem identifier, source, policy or checkpoint inconsistently is rejected.

`policy.seconds` bounds a new adaptive invocation in an isolated worker; `resume_adaptive_complex_isolation(..., seconds=...)` also puts checkpoint replay inside that worker. Fully serialized checkpoints include the current stage and accepted mathematical cover. A killed stage can resume at the same stage without losing boxes. Infinite retries that never complete cofinal stages do not satisfy the effort hypothesis. Parent serialization/process/recovery overhead lies outside the worker timeout, as described in the [budget guide](guides/budgets-and-resume.md).

## two selected multiplicity theorems

```python
parent = fp.certify_analytic_contour(s.cosh(z)-1, z, -1-s.I, 1+s.I)
exact = fp.certify_complex_multiple_root(parent, center=s.S.Zero)
assert exact.verify() and exact.center == 0
assert exact.root_count == 1 and exact.multiplicity_count == 2

multiple = fp.certify_complex_isolation(s.exp(z)*(s.exp(z)-1)**2,
    z, -1-s.I, 1+s.I, max_box_diameter=s.Rational(1, 100),
    policy=fp.EnclosurePolicy(max_depth=40, max_cells=4096))
assert multiple.verify() and multiple.complete
assert multiple.root_count == 1 and multiple.total_count == 2
assert multiple.proof.individual_multiplicities == (2,)
```

**Exact Taylor order.** `ComplexExactMultiplicity` binds a checked multiplicity- inclusive parent count m, an exact interior Gaussian-rational center, exact zero jets through order m-1, and a `ComplexTaylorWitness` whose normalized coefficient of order m excludes zero. The local order is exactly m. Since the enclosing count is also m, this is the only zero in the rectangle. Float/approximate centers, small numerical derivatives and unproved symbolic zero jets do not qualify.

The outward Taylor primitive uses truncated sum/product/power and composition recurrences for the entire grammar. Its entries enclose f^(k)/k!, not unnormalized derivatives. Exact zero jets are independently recomputed by symbolic differentiation; interval proximity to zero never replaces equality.

**Power times unit.** `ComplexPowerFactorProof` checks the exact entire identity f=u*g**m, a zero-free unit on the full rectangle, a checked count-one proof for g and the source's count m. It proves one source zero of order m without assigning an exact center. The unit proof uses structural nonvanishing (nonzero constants, exponentials and their products/powers) or an outward range excluding zero. The proposer may factor, but replay only checks the submitted identity by exact arithmetic expansion and the supplied count/unit witnesses. Held source holes, free parameters, branch powers and floating source coefficients remain unsupported.

The helper returns a checked individual-root record or None. Automatic selected recognition is enabled with `use_multiple=True`; disable it to retain count-only clusters. Taylor order follows the policy's finite order cap; cofinal stages raise that cap. Symbolic proposals are restricted to sources with at most 512 operations. This is selected coverage, not general analytic factorization.

## Refinement, counts and limits

An exact located multiple zero transfers to any checked subrectangle containing its center strictly in the interior; subsets excluding the center have count zero. A subset whose boundary contains the center is rejected. The search stores the contracted child and all four excluded strips. Power-factor roots refine or subdivide their simple base proof and lift every root/exclusion region with multiplicity multiplier m. Nonvanishing units preserve zero-free shared boundaries.

The whole assembly checks these region graphs, full geometric coverage, source binding and totals. `isolation_complete` admits individually proved multiple zeros. `individual_multiplicities` gives their orders when complete; a positive cluster alone still has no distinct-root count. Whole-result `root_count` means distinct roots. Public box-level factory-based `root_count` is multiplicity-inclusive; `distinct_root_count` and `multiplicity_count` expose the distinction explicitly.

's simple-root guarantee is marked inapplicable when establishes multiplicity greater than one, even if the actual query completes. General multiple-root isolation, arbitrary parameters, branch-chart gluing, infinite-domain exhaustion and a universally terminating elementary solver remain outside this release. The trusted kernel includes structural interval/Taylor rules and SymPy exact differentiation/expansion. No external formal verification is claimed.

Supported quotients dispatch through the separately checked joint ledger, returning `QuotientIsolationRun` with its own conditional theorem. See [quotient-search.md](quotient-search.md) for its original-guard, shared-order, pole accounting and refinement premises. The entire-only theorem above is unchanged.
