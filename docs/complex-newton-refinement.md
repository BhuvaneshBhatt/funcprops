# certified Krawczyk refinement

Python blocks on this page form one ordered session, executed from a fresh namespace.

## Public use

```python
import sympy as s
import funcprops as fp

z = s.Symbol('z')
r = s.Rational(1, 10)
parent = fp.certify_analytic_contour(s.exp(z)-1, z, -r-s.I*r, r+s.I*r)
step = fp.certify_complex_refinement(parent)
assert step is not None and step.verify()
assert step.contraction < 1
assert step.root_region.zero_count == 1
assert len(step.zero_regions) == 4
assert all(region.verify() for region in step.regions)

state = fp.certify_complex_isolation(s.exp(z)-1, z, -r-s.I*r, r+s.I*r,
    max_box_diameter=s.Rational(1, 10**8),
    policy=fp.EnclosurePolicy(max_depth=32, max_cells=1024))
assert state.complete and state.verify() and state.refinements
assert state.coverage_complete and state.isolation_complete and state.accuracy_complete
```

The direct helper accepts an count-one certificate, a prior `ComplexNewtonRegion` with count one, or a public root rectangle carrying one of these certificates. It returns one `ComplexNewtonRefinement`, or `None` if its premises or effort are insufficient. A decline adds no conclusion and leaves the parent intact. The count-two/cluster case always declines.

The isolation search repeats successful steps until the requested width and/or diameter is reached. Public `isolate_complex_roots` and detailed `complex_zeros` accept the same accuracy options and expose `refinements`. Existing algroots queries retain their exact location route and do not need Newton boxes.

## Checked theorem and arithmetic

Let B be the closed parent rectangle, m its exact midpoint, V an outward box for f(m), and D an outward complex box for f'(B). Choose a nonzero Gaussian rational C. Compute, using exact rational rectangle arithmetic,

```
E = 1 - C D
K = m - C V + E (B - m)
q = max(|Re E|) + max(|Im E|).
```

The checker requires q < 1 and a rational child R with K strictly inside R, which is strictly inside B. It also requires the stored parent's checked count to be exactly one, and a substantial reduction in both side lengths.

For the real two-dimensional map T(w)=w-Cf(w), holomorphy identifies its Jacobian with complex multiplication by 1-Cf'(w). The computed q bounds that Jacobian's infinity norm. Integration along segments in convex B places T(B) inside K. Thus T maps B into itself and is a contraction. Its fixed point is a unique simple zero of f because C is invertible. Every zero in B must lie in K, hence in the interior of R. The already checked parent count transfers to R; the four complement strips contain no zeros, including on their new boundaries.

This is a scalar complex specialization with an explicit norm bound of the standard real Krawczyk inclusion approach. For the general inclusion theorem and interval-gradient interpretation, see Rump and Graillat, Section 2, [Verified error bounds for multiple roots of systems of nonlinear equations](https://www.tuhh.de/ti3/paper/rump/RuGr09.pdf). The package implements only the simple-root contraction described here, not that paper's multiple-root perturbation methods.

The certificate stores B, m, V, D, a derivative enclosure at m, C, E, K, q, R, the parent count proof and raw source/coordinate metadata. C is the exact reciprocal of the midpoint of the recorded point-derivative enclosure. It is an approximate inverse of f'(m), with no assertion that this midpoint is the true derivative. All resulting residual and inclusion inequalities are checked.

## Derivative enclosures and replay

`ComplexDerivativeWitness` uses forward interval automatic differentiation on the original entire source tree. It implements sum/product/integer-power and chain rules for exp, sin, cos, sinh, cosh, erf and erfc. The erf/erfc rule uses an outward enclosure of 2/sqrt(pi) and exp(-w**2). Those derivative constants do not broaden the accepted input grammar. Held source holes, branch powers, parameters, conjugation and floating input coefficients remain unsupported.

`check_complex_refinement` validates the source, coordinate, schema, all value and derivative witnesses, the rational inverse, residual, contraction, strict inclusions, child geometry and parent count graph. Changed derivatives, inverses or images do not pass by assertion. Parent graphs use memoized replay with cycle rejection. Strict record types prevent self-attesting subclasses.

Replay calls the outward arithmetic and exact rectangle checker. It does not invoke the refinement producer, contour proposal, symbolic solving, subdivision or split selection. The proof, transferred regions and derivative witnesses are registered with `verify_certificate` and `replay_status`; their native statuses are distinct from the algroots backend adapter.

## Coverage and interruption

A successful step partitions B into the child and four closed rational strips: left/right strips span B's height, and bottom/top strips span the child's width. Their interiors are disjoint. The existing rectangle-cover checker verifies the exact finite tiling. Count transfer proves each strip's zero count and every new seam's nonvanishing; no root-free complement is discarded.

`ComplexNewtonRegion` references its refinement and identifies one of these five regions. A refined root can itself be the parent of another refinement. The main assembly accepts counts and these transferred counts together, replays their graph, checks the complete leaf partition and compares its total with the outer contour. An omitted, duplicated, overlapping or relabeled complement is rejected even if the summary fields are recomputed.

Updates remain atomic: the old parent is retained until its full refinement verifies, then the child and all four zero strips replace it together. The child's checkpoint path records four exact binary cuts, so the existing frontier checker also validates Newton states. Resume validates the full graph and retains source, rectangle and requested accuracy. Wall interruption returns a fully serialized earlier checkpoint, including accepted refinement evidence.

## Accuracy, effort and fallback

`max_box_width` bounds the maximum side. `max_box_diameter` bounds Euclidean diameter by the exact inequality width**2+height**2 <= diameter**2. Both must be positive exact rationals when present. Unmet accuracy keeps `complete=False` even when all roots are already individually isolated.

One attempted precision charges two query-wide work units for outward jets on B and at m. Failed attempts are charged as well. Witness replay, exact rational geometry and proof bookkeeping are outside the cell counter. `policy.seconds` provides the same isolated worker wall timeout, subject to parent/process overhead. Direct-helper timeout returns `None`; the original count remains valid.

The policy's bounded precision portfolio is tried. The proposer uses strict interior padding and requires each child side to be at most three quarters of its parent side. An accepted step uses four depth levels corresponding to its four complement cuts. If fewer levels remain, or contraction cannot be proved, ordinary fair contour subdivision remains available. Failed attempts rotate through the existing fair queue and cannot replace the parent with an unproved child. Newton never upgrades an unresolved cluster to an individual root.

`use_newton=False` disables acceleration for comparison and retains the checked contour-bisection route. For exp(z)-1 and sin(z) on [-1/10,1/10]+i[-1/10,1/10], the validated diameter-10**-6 examples use 12 and 10 charged units with refinement, versus 403 each without it. These are two measured cases, not asymptotic or universal speed claims; timings and the exact runtime are in the release report.

## Remaining scope

This implements 's local contraction and acceleration. The later [contract](complex-completion.md) adds a cofinal protocol and selected multiple-root proofs; neither is a universally terminating elementary solver. Difficult bounds may still force subdivision or leave unresolved work. Arbitrary parameters, general multiple roots and branch-chart gluing remain outside scope. Replay trusts the structural derivative rules, outward interval primitive and SymPy/rational arithmetic, instead of an external formal proof system.
