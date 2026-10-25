# Infinite-domain and parameter root coverage

Compact root counts do not cover an infinite domain or an unspecified parameter family. Funcprops requires explicit tail or indexed-family proofs and exhaustive parameter guards.

## Infinite domains

`infinite_root_coverage` combines supported finite covers with `ExponentialTailWitness` records or recognized rational trigonometric families. Exponential-polynomial tails require bounds proving eventual nonvanishing on the stated ray. Periodic rational sin/cos/tan expressions require exact affine frequency/offset data, denominator exclusions, index ranges and endpoint ownership. Every source pole remains excluded.

A finite root count on a compact core is global only when both required tails are proved. An infinite root set needs an exhaustive indexed family; numerical sampling is not an exclusion theorem. Unsupported oscillations and unresolved tails keep the result incomplete.

## Guarded families

`parameter_root_coverage` handles selected polynomial, monotone and exponential families. `ParameterCoverageProof` binds the parameter guard, source domain, strata and local counts. Transition loci record where degree, multiplicity or endpoint ownership can change. `specialize_parameter_coverage` checks exact real substitutions and their guards.

`certify_parameter_box` and uniform-box witnesses bound functions and derivatives on Cartesian parameter/domain boxes. Uniform counts need the same crossing and exclusion premises throughout the box. Overlapping parameter cells, missing strata and unproved realness prevent exhaustive coverage.

## Polynomial parameter geometry

`certify_parameter_geometry` partitions rational polynomial families of degree at most four in the root coordinate, with up to four real parameters. It checks exact Hermite trace signatures, degree-loss guards and endpoint ownership on rational-endpoint intervals. Counts are distinct real roots. Intrinsic assumptions and the explicit parameter domain remain premises. Unfinished sign prefixes stay in `unresolved` and can be passed to `resume_parameter_geometry`. This is a separate interface from selected-family and uniform-box coverage. See the [tutorial](tutorials/parameter-geometry.md) and [field contracts](reference/helper-contracts.md).

## Limits

These methods do not solve general transcendental parameter geometry. A family declaration is not a theorem for every composition, boundary case or parameter value. Local witnesses remain useful when the complete parameter partition is unavailable. See [capabilities](capabilities.md), [root coverage](root-coverage-checker.md) and [result contracts](reference/result-contracts.md).
