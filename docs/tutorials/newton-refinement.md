# Count-preserving Newton refinement

Can I shrink a root box without discarding its complement?

A checked simple base, certified contraction and all complement strips.

Run `python examples/newton_refinement.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: newton-refinement -->

## Example

```python
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
radius = sp.Rational(1, 10)
parent = fp.certify_analytic_contour(
    sp.exp(z) - 1, z, -radius - sp.I * radius, radius + sp.I * radius
)
assert parent.verify() and parent.zero_count == 1
refined = fp.certify_complex_refinement(parent)
assert refined is not None and refined.verify() and fp.verify_certificate(refined)
assert len(refined.regions) == 5
assert sum(c.zero_count for c in refined.regions) == 1
```

## Expected result

Five child/complement regions preserve total zero count one.

Certified contraction accelerates an already checked local count.

## Scope and next steps

A small candidate box alone does not prove isolation or discard the surrounding region. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
