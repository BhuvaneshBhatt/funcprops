# Adaptive real root coverage

`adaptive_root_coverage` combines interval exclusion, monotone crossing, interval Newton, Taylor bounds and supported multiplicity proofs on exact finite-component real domains. It returns an `AdaptiveRootResult` with a replayable `CoverageProof` and a resumable `CoverageState`.

## Coverage invariant

Accepted leaves and pending tasks partition the effective source domain with one owner for each endpoint. The pending union equals `proof.unresolved`. Counts are global only when this union is empty. State replay rejects missing tasks, overlaps, altered source premises and false totals.

The breadth-first scheduler subdivides failed compact cells. Certified one-root windows may replace several pending cells, but every complement remains represented. Windows intersecting an accepted positive-count leaf are declined. `located-subset` witnesses use a checked parent and Newton bounds or an exact root location; `zero-subset` inherits a zero count on a subset.

## Effort and resumption

`EnclosurePolicy` bounds each invocation's cells, depth, precision, Taylor order, series terms and elapsed time. `resume_root_coverage` continues from a checked state. Cumulative work is recorded separately from the per-invocation cap. `coverage_policy_stage` supplies an increasing schedule.

For supported C1 functions on compact domains with finitely many simple separated roots and convergent value/derivative enclosures, fair subdivision eventually finds exclusion cells and root windows. This conditional statement supplies no finite runtime bound. Unsupported domains or missing regularity premises remain unresolved.

## Multiplicity and clusters

Rational Sturm counts, explicit power factors and checked Taylor deflation distinguish root count from total multiplicity. Deflation requires an exact center, vanishing lower jets, a nonzero leading coefficient and a controlled remainder. A floating approximation cannot establish an exact center. Piecewise branch multiplicity does not establish the whole function's order at a seam without additional regularity evidence.

`certify_complex_cluster` uses supported analytic Cauchy/Rouché witnesses for selected disks. A cluster count includes multiplicity and does not claim individual isolation. See [complex isolation](native-complex-isolation.md) for rectangle coverage.

See [enclosures](enclosures.md), [infinite coverage](infinite-and-parameter-coverage.md) and the [root tutorial](tutorials/real-root-coverage.md).
