# Quotients, holes and poles

Which counted points are source zeros, excluded extension zeros or poles?

Certified entire quotients; shared orders require exact identities and exhaustive counts.

Run `python examples/quotients_and_holes.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: quotients-and-holes -->

## Example

```python
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
g = sp.exp(z) - 2
rectangle = (-1 - sp.I, 1 + sp.I)
policy = fp.EnclosurePolicy(max_cells=8192, max_depth=24, max_taylor_order=5)
held = sp.Mul(g**2, g, sp.Pow(g, -1, evaluate=False), evaluate=False)
hole = fp.certify_quotient_isolation(held, z, *rectangle, policy=policy)
assert hole.verify() and hole.complete and hole.total_count == 0
assert hole.proof.extension_zero_count == hole.proof.excluded_zero_multiplicity == 2
assert hole.proof.source.guards == (g,)
for denominator, poles in ((sp.sin(g), 0), (sp.sin(g) ** 2, 1)):
    q = fp.certify_quotient_isolation(g / denominator, z, *rectangle, policy=policy)
    assert q.verify() and q.complete and q.total_count == 0
    assert q.pole_multiplicity_count == poles
    assert q.proof.winding_count == -poles
```

## Expected result

The held cancellation has zero source roots and extension multiplicity two; the examples have zero and one pole.

Original denominator restrictions survive meromorphic extension.

## Scope and next steps

Unknown shared orders or unclear boundaries prevent the corresponding complete ledger. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
