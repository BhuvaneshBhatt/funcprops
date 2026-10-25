# Implicit common zeros and orders

Can I prove common zeros and their orders at an implicitly located root?

Congruence/radical identities and local orders, separately from exhaustive root coverage.

Run `python examples/implicit_common_orders.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: implicit-common-orders -->

## Example

```python
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
g = sp.exp(z) - 2
rectangle = (sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100)
policy = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=192
)
base = fp.certify_analytic_contour(g, z, *rectangle, policy=policy)
f = sp.sin(g) + z * (sp.exp(g) - 1)
h = sp.sin(g) ** 2 + z * (sp.exp(g) - 1) ** 2
common = fp.certify_common_zero((f, h), base, max_order=3, policy=policy)
assert common.verify() and common.common_zero_status is fp.TruthValue.TRUE
assert common.orders_complete and common.multiplicities == (1, 2)
assert not common.coverage_complete and not common.complete
assert fp.verify_certificate(common)
# Exact local order does not exclude other zeros elsewhere in the rectangle.
```

## Expected result

The local multiplicities are (1,2); this local theorem is not exhaustive root coverage.

Exact congruences and nonzero jets establish local orders.

## Scope and next steps

Unproved identities and possible additional zeros keep the corresponding completion fields false. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
