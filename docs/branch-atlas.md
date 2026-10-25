# Finite logarithm and power chart gluing

`certify_log_atlas(base, z, rectangles, policy=...)` constructs checked logarithm charts on a finite union of closed rational rectangles. The base uses the existing parameter-free entire-function grammar. The coordinate is an unconstrained commutative Symbol. Each component chooses an initial sheet; the result is a selected branch, not an identity with the original principal expression.

See the [executable workflow](tutorials/branch-chart-gluing.md).

## Local charts and overlap theorem

A `LogBranchChart` contains an outward image box for F and a phase `a` chosen from 1, I, -1, -I. Replay establishes `Re(F/a)>0` throughout its rectangle. Strict separation gives a neighborhood where F is nonzero and `L=log(F/a)+log(a)+2*pi*I*sheet` is holomorphic. This can cross the old principal cut of `log(F)` while preserving the selected branch.

For the branch conventions see [DLMF 4.2](https://dlmf.nist.gov/4.2). The overlap argument below is the implementation's theorem specialization.

On an overlap, both exponentials equal F. The imaginary part of each chart lies in an open interval of width pi. The difference is an integer multiple of `2*pi*I`, and the difference of those argument intervals admits at most one such integer. The checker derives that integer exactly from phases and sheets. Every intersecting pair is checked, including shared edges and corners. A rational-grid union check verifies the entire requested region, including seams. Charts may overlap; disjointness is not required for an atlas.

`glue_log_charts` normalizes sheets along each connected component. Remaining nonzero transitions describe inconsistent selected chart values; after automatic normalization they witness a cycle obstruction. Caller-supplied unnormalized sheet choices can also yield a nonzero transition without proving that every possible choice fails.

## Completion and powers

`LogAtlasProof.coverage_complete` means all requested points have charts. `gluing_complete` and `complete` additionally require every logarithm transition to vanish. A loop around a zero can have full chart coverage and a genuine obstruction. Successful replay of that obstruction must not claim a global log.

`GluedPowerProof(atlas, q)` checks constant finite exact exponents. Its overlap multipliers are `exp(2*pi*I*q*turns)`. The power can glue when every multiplier is one even if the logarithm does not. For example, a selected square root of z**2 can glue on a region around zero that excludes zero. This does not change the principal-power convention used by existing property queries.

## Supplied holomorphic recipes

`certify_branch_chart` checks a supplied formula for an entire implicit relation. A recipe can combine several selected logarithms, supported entire primitives and arithmetic; supported denominator bases require explicit nonzero image witnesses. `glue_branch_charts` binds all charts to the same relation and checks every touching overlap and the requested rational rectangle union. Log-sheet identities or an exact derivative identity plus an anchor establish agreement. Two implicit branches meeting at one point are not thereby equal.

Selected recipes can disagree even on a region that admits another compatible choice. Such disagreement is valid partial evidence; it is not automatically a topological impossibility theorem. Coverage and compatible gluing remain separate. See [local recipes](tutorials/branch-recipes.md), [tests](../tests/test_proof_obligations.py) and [field contracts](reference/helper-contracts.md). Automatic discovery of arbitrary implicit branches remains unsupported.

## Limits

Subdivision, precision and series work are bounded. Any uncharted region remains explicit and prevents completion. Original variable-dependent divisions, branch powers inside the base, free parameters and narrowed coordinates are declined before algebraic cancellation. These are finite log/power atlases, not arbitrary Riemann-surface gluing. Native root isolation has not acquired a general logarithm or chart-aware contour grammar from this addition.

Replay checks supplied evidence and exact transitions without the chart search. See [tests](../tests/test_branch_atlas.py).
