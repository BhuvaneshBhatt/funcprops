# Common zeros and orders at implicit roots

The proof language binds an exact value or local order to one certified implicit root. It accepts general supported entire expressions, not only a single factor or outer composition. It is a certificate language and a bounded proposer, not a universally deciding analytic-equivalence solver.

See the [executable workflow](tutorials/implicit-common-orders.md).

## Exact value and radical identities

`certify_root_value(F, base_region, max_nodes=..., max_power=...)` proposes an `ImplicitRootValueProof`. The base record must independently prove one distinct zero of G in its rectangle. Multiple base zeros are permitted when uniqueness of the distinct root is independently certified.

A value proof stores previously proved values of proper subexpressions. After those congruence substitutions, replay checks the exact analytic identity `(rewritten_F-value)**power = quotient*G`, with a positive integer power and an entire quotient. At the base zero this forces F=value. A variable-dependent reciprocal is not an entire quotient and cannot manufacture this equality. Arithmetic coefficients may be finite exact constants; no free parameters or floating inputs are admitted. This also accommodates exact derivative constants.

The proposer recursively discovers congruences, keeps useful descendants of nonconstant subexpressions, and uses polynomial division in formal entire atoms. Small powers provide radical-ideal witnesses, for example H**2=G at a multiple base. Replay checks the resulting identity directly and does not call division, root search or the proposing functions. Failure to find an identity is unknown.

## Local order and common-zero status

`certify_implicit_multiplicity` proves consecutive zero derivatives, then a nonzero exact derivative value or a nonzero normalized derivative enclosure over the entire base rectangle. `ImplicitJetWitness` binds the source, full box, derivative order, precision and series allowance. Its box is not a midpoint evaluation. An exact nonzero value proof can replace that box witness when the leading derivative has a provable constant value. The first nonzero jet establishes the exact local order. A proved nonzero value gives order zero. For the analytic zero/order convention see [DLMF 1.10](https://dlmf.nist.gov/1.10).

`certify_common_zero((F,H,...), base_region)` assembles the local proofs:

- `common_zero_status` is TRUE when all vanish, FALSE when one is proved nonzero, and UNKNOWN when neither conclusion is established.
- `orders_complete` means all local orders are known; `multiplicities` may include zero for a function that does not vanish at the base point.
- `coverage_complete` and `complete` remain False. Exact order at one point does not exclude additional zeros elsewhere. Identically zero expressions do not acquire an invented finite multiplicity.

## Exhaustive count and quotient integration

An independently checked contour count equal to a proved minimum local order allows `SharedZeroOrderProof` to certify that the rectangle contains precisely that one zero of the corresponding multiplicity. This exhaustive evidence is separate from the local order record. The existing rectangle transfer and quotient root/pole ledger consume these records. Generic zero-at-base proofs can also establish that a canceled original source guard removes an extension zero. Newton transfers rebind their identity graphs and jet enclosures to the child.

Finite node/order/cell/precision caps and wall budgets preserve unresolved cases. A tiny shift is not a shared zero just because its root lies in the same box. This addition does not implement arbitrary analytic gcd discovery, all special function identities, general parameter geometry, or a termination guarantee for arbitrary elementary expressions. See [tests](../tests/test_implicit_orders.py).
