# Source, domain and branch semantics

Funcprops analyzes the expression it receives. SymPy evaluation can erase denominator holes before the call, so retain arithmetic with `evaluate=False` when source definition matters. `DomainRecord` binds the requested set, natural-domain evidence, effective set and raw restrictions. Transformations must transfer restrictions exactly or leave that route unresolved.

Real-domain conditions describe finite real outputs of the received SymPy expression. Complex intermediate values can contribute real outputs: for example, `cos(log(-1))` is `cosh(pi)`. Supported elementary compositions retain the complex definition guards and impose reality on the final value. If the resulting locus cannot be resolved, range and sign queries can remain unknown. A composition theorem that assumes a real inner image must prove that premise on the requested domain.

## Exactness

Proofs of exact zero values and local orders require exact coefficients and centers. A decimal approximation is not an exact rational zero. Outward numerical enclosures can prove nonzero bounds, but a small residual cannot prove equality. Canceled source factors still constrain definition, including accumulating holes near a candidate singularity.

## Branches and local orders

A selected logarithm germ has an explicit base value and consistency premises. Its continuation does not automatically equal the principal branch on another region. Local multiplicity needs vanishing lower derivatives and a nonzero leading jet. Exhaustive rectangle counts are separate evidence that no other roots occur.

## Proof records

Checkers bind concrete record types, exact sources, domains and plain data containers. User callbacks and custom equality methods cannot replace the checked mathematical data. Replay may validate a useful partial result; unresolved regions and completion flags remain part of the conclusion.

## Property assembly

Disconnected images are assembled with endpoint ownership intact. Piecewise conditions use first-match semantics. Branch-local regularity and derivative signs prove only what their domains and seams support. See [domains and branches](guides/domains-and-branches.md), [certification](certification.md) and [contracts](reference/result-contracts.md).

## Worker transport

Wall-budget queries retain held source operations when sending inputs, results and checkpoints between processes. Arithmetic, function applications, relations and Boolean guards are reconstructed without evaluating away their operands. Polynomial records also retain their coefficient domain. This keeps the source-hole contract the same for direct and budgeted queries: a held `x/x` still excludes zero after transport. The transport is internal trusted-process data, not an untrusted-file interchange format.
