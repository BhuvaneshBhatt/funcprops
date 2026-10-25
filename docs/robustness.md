# Input and replay contracts

Use these contracts when integrating funcprops into a symbolic workflow. They distinguish invalid inputs, unsupported mathematics, rejected evidence and a valid partial answer. The [result glossary](reference/result-contracts.md) describes completion and certification separately.

## Domains and coordinates

Real continuity requires a real domain. Passing `Complexes` raises a clear `ValueError`; use the supported complex analyticity and contour interfaces for their separate theorems. Unsupported nested sign, Heaviside and Min/Max range problems return an unknown image. A symbolic limit failure cannot establish an endpoint value.

Polynomial complex rectangle/disk counts and rational contour counts require an unconstrained commutative coordinate, matching native complex isolation. Declare `z = Symbol("z")` and give a real contour parameter its own symbol. A real, positive or explicitly `complex=True` coordinate carries narrowed intrinsic assumptions and is outside these counting contracts. Coordinates are part of the proof binding, not just printed names.

Complex aggregate count fields use Python integers, excluding Boolean and numerically equal floating values. Some real proof schemas also accept exact symbolic integers; inspect the concrete record. Distinct counts and counts with multiplicity remain separate.

Supplied `critical_covers` and `zero_covers` must be plain tuples of supported coverage records or `None` entries. Invalid container or entry types raise `TypeError` before analysis. A valid supplied proof must also match the source, domain and coordinate; a wrong proof raises `ValueError`.

## Replay and metadata

`verify_certificate` is the shared boundary for registered proof records. Malformed registered evidence returns `False` for structural and expected symbolic errors. An unregistered type raises `TypeError`; missing source arguments required by an unbound proof raise `ValueError`. This interface does not deserialize arbitrary Python objects or promise to catch every possible user-defined exception. Use `replay_status` for diagnostic rejection and unsupported outcomes. Native rejection retains its replay route and schema information.

Where an adapter accepts optional source or coordinate arguments, those arguments must match. Scalar, tuple and list forms are normalized for supported scalar/vector bindings. A theorem with no expanded source formula rejects an expanded-form context it cannot authenticate. Successful replay establishes the concrete theorem and does not imply exhaustive coverage.

Guard-only normalization preserves exceptions, domain records, evidence and completion metadata when it rewrites equivalent guards. Substitution can change the mathematical source, so general case specialization does not inherit a source-bound proof flag. Use a typed specialization adapter to obtain replayable evidence for a changed source.

A local invertibility result describes applicability of the real C1 inverse function theorem. Failed Jacobian hypotheses do not rule out every continuous inverse. A Krawczyk certificate's `center` is its iteration point; its `enclosure` bounds the unique root. The center need not satisfy the equation.

## Bounded computation and remaining scope

Quotient search distinguishes cell-budget, depth-budget and unresolved boundary obligations. Completed local evidence can remain useful after exhaustion, but no unresolved region becomes root-free from a budget stop. A symbolic operation-count estimate is a routing heuristic, not a runtime bound; large exponents and coefficients can cost more than their operation count suggests. Use a wall budget where supported.

Some route identifiers and search-work fields are descriptive metadata, not independently authenticated execution provenance. A checked backend identifier and replayed numerical enclosure are different obligations. General zero-duration and arbitrary Piecewise contour wrappers, exact images for unsupported nested catalogue functions, and unrestricted domain simplification remain capability limits. See the [capability matrix](capabilities.md).

The [robustness regression suite](../tests/test_robustness_contracts.py) checks these boundaries alongside the [family test matrix](reference/testing-matrix.md). Historical observations are reconciled separately in the delivery validation report, including findings already corrected and limitations that remain open.
