# Certified extrema bounds at implicit stationary points

`certify_extrema_bounds(expr, var, domain, tolerance=..., policy=...)` encloses both the infimum and supremum. It does not need closed-form critical coordinates. The two returned rational pairs are `minimum_bounds` and `maximum_bounds`. They do not assert attainment or return a minimizer.

Start with the [executable workflow](tutorials/certified-extrema-bounds.md).

## Contract and proof

The initial scope is parameter-free real expressions, finite unions of bounded intervals and finite sets, exact inputs, and supported C1 branch extensions to interval closures. Piecewise singleton values and one-sided branch limits are separate sites. Natural-domain tracking uses the original source. Held canceled holes remain excluded even when arithmetic normalization supplies a regular extension for computing a limit.

At an interior extremum of a C1 extension its derivative vanishes. A checked critical-root cover therefore permits endpoint/limit sites and positive-count root regions to contain every possible extremum. Unresolved critical regions are retained as possible sites, with outward value bounds over the whole region. Every nonempty region also supplies a possible value (or limit), so aggregating site bounds gives a bracket for each infimum/supremum without guessing value ordering. Explicit algebraic critical points are used when already certified.

| Field | Meaning after successful replay |
| --- | --- |
| `coverage_complete` | Every possible extremum is covered by checked value sites. |
| `critical_coverage_complete` | No unresolved derivative-zero region was needed. |
| `accuracy_complete` | Both value brackets have width at most `tolerance`. |
| `exact_complete` | Both rational brackets collapse to points. |
| `complete` | Coverage and requested value accuracy are both established. |

Value coverage can be complete even while critical-root coverage is partial. A coarse bracket is still certified; it does not meet a finer requested accuracy. An empty effective domain has no returned finite extrema and `complete=False`. Unbounded components or unsupported closure regularity decline this route.

## Search, budget and replay

The proposer reuses adaptive real-root covers and checked Newton location transfers, refining value enclosures within finite depth, precision and cell caps. Caller-supplied `critical_covers` must follow source-cell order and match the exact branch derivative on its open interior. A mismatched supplied cover raises an error. `policy.seconds` uses the existing process-isolated wall budget; a worker timeout does not produce a certified value.

`ExtremaBoundsProof.check()` replays the domain, cover, candidate sites and outward bounds. It never calls the extrema or root proposers. Altered bounds, omitted/duplicated sites, substituted source/domain records and undeclared record subclasses are rejected. See [tests](../tests/test_extrema_bounds.py).
