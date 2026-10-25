# Contour counts and property proof assembly

## Entire-function contours

`certify_analytic_contour` bounds the source image along the boundary of a rational rectangle in the supported parameter-free entire grammar. Every boundary segment has an outward complex box excluding zero. The checker reconstructs a winding number from these boxes and verifies holomorphy and orientation before accepting a multiplicity count.

Complex rectangle coverage additionally checks exact union, disjoint interiors and clear shared boundaries. A zero on a proposed split line requires a different split or a retained unresolved region. A root-free outer boundary is a premise, not a sampling observation. Counts alone do not give individual root locations or requested accuracy; [complex isolation](native-complex-isolation.md) supplies those contracts.

## Real property consumers

`certify_property_coverage` assembles supported sign, monotonicity, range and optimization conclusions from domain evidence, derivative-root coverage and value enclosures. Every effective component and seam must be accounted for. Open endpoints contribute limits, while attainment requires an owned source point. A branch extension cannot add a missing source value.

Piecewise assembly uses first-match branch domains and seam certificates. A smooth branch away from a seam does not prove whole-function differentiability there. Unknown comparisons, unresolved critical regions and missing seams keep the corresponding conclusion incomplete.

[Extrema bounds](certified-extrema-bounds.md) provide rational value brackets when exact stationary values are unavailable. The [result contracts](reference/result-contracts.md) separate replay validity, coverage, isolation, attainment and accuracy.
