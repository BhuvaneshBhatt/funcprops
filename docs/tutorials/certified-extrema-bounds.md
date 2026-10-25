# Certified extrema bounds

Can I bound extrema without solving the stationary equation exactly?

Finite real components, implicit critical points, and separate coverage/value accuracy.

Run `python examples/certified_extrema_bounds.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: certified-extrema-bounds -->

## Example

```python
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
policy = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=160, max_depth=7
)
proof = fp.certify_extrema_bounds(
    sp.exp(x) + x * x,
    x,
    sp.Interval(-1, 1),
    tolerance=sp.Rational(1, 10000),
    policy=policy,
)
assert proof.verify() and proof.complete
assert proof.coverage_complete and proof.accuracy_complete
assert proof.minimum_bounds[1] - proof.minimum_bounds[0] <= proof.tolerance
assert proof.maximum_bounds[1] - proof.maximum_bounds[0] <= proof.tolerance
assert not proof.exact_complete
assert fp.verify_certificate(proof)
```

## Expected result

Both value brackets have width at most 1/10000, while exact extrema remain unresolved.

Value accuracy can be certified without a closed-form stationary coordinate.

## Scope and next steps

The supported finite smooth branches and interval enclosures do not cover arbitrary nonsmooth inputs. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
