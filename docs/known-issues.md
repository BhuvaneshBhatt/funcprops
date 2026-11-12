# Known issues

These are interface inconsistencies and incomplete dispatch routes. Consult the [capability matrix](capabilities.md) for mathematical scope and the [robustness contracts](robustness.md) for input and replay behavior.

- Determinant zero-set routing can decline a set-valued interval restriction that succeeds as an equivalent Boolean inequality. No affirmative result is inferred from that decline.
- `registry_hessian` accepts repeated argument positions, unlike `registry_gradient`. Callers should supply distinct positions; input-validation consistency remains to be improved.
- Registry gradient, Hessian, chain-rule and Jacobian records have direct checkers but no unified replay adapters. Custom registry proofs require an explicit trusted registry at direct replay.
- A malformed root result with `isolated_intervals=None` is rejected by replay but can raise `TypeError` during detailed-result projection. Typed result display is not a deserializer.
- The general Piecewise sign aggregator can lose a branch's `SIGN_CHANGING` conclusion and return `UNKNOWN`. The bounded rational and chart rules retain that conclusion in their component assembly.

Remaining limitations include unsupported exact images for some nested sign/Heaviside/Min/Max expressions, route-specific path geometry, an operation-count cost heuristic, and descriptive metadata without universal provenance authentication. These do not establish affirmative mathematical results. General mathematical limits and bounded computations that remain unresolved are described in the [capability matrix](capabilities.md). See [troubleshooting](troubleshooting.md) for interpreting a partial, rejected or unsupported result.
