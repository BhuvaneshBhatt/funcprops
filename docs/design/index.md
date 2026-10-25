# Proof design

The design separates candidate construction from checking and binds each conclusion to its source, domain and assumptions. These references describe the mathematical obligations at each boundary.

| Layer | Reference |
| --- | --- |
| Source and effective domain | [Domain tracking](../domain-tracking-and-components.md), [source semantics](../source-semantics.md) |
| Real proof records and arithmetic | [Enclosures](../enclosures.md), [root coverage](../root-coverage-checker.md) |
| Compact search and multiplicity | [Adaptive coverage](../adaptive-coverage.md) |
| Infinite domains and parameters | [Families, tails and uniform boxes](../infinite-and-parameter-coverage.md) |
| Contours and property consumers | [Contour and property proofs](../contour-and-property-proofs.md) |
| Algebraic backend | [Complex backend adapter](../algroots-complex-backend.md) |
| Complex isolation and completion | [Rectangle assembly](../native-complex-isolation.md), [cofinal search](../complex-completion.md) |
| Certified acceleration | [Newton refinement](../complex-newton-refinement.md) |
| Quotient roots and poles | [Joint ledger](../quotient-isolation.md), [shared orders and search](../quotient-search.md) |
| Higher-level conclusions | [Extrema](../certified-extrema-bounds.md), [charts](../branch-atlas.md), [implicit orders](../implicit-orders.md) |

[Architecture](../architecture.md) identifies module responsibilities. [Certification](../certification.md) explains trusted arithmetic, backend replay and independent witness checking.
