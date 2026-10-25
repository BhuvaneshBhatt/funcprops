# Real root coverage

When is a real-root count exhaustive?

Compact witnesses, rational multiplicities, recognized periodic families and tails.

Run `python examples/real_root_coverage.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: real-root-coverage -->

## Example

```python
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
compact = fp.adaptive_root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 1))
assert compact.verify() and compact.complete and compact.root_count == 1
multiple = fp.prove_root_coverage((x * x - 2) ** 3, x, sp.Interval(-2, 2))
assert (
    multiple.verify() and multiple.root_count == 2 and multiple.multiplicity_count == 6
)
open_domain = fp.adaptive_root_coverage(sp.exp(x) - 1, x, sp.Interval.open(0, 1))
assert open_domain.complete and open_domain.root_count == 0
periodic = fp.infinite_root_coverage(sp.sin(x), x)
assert periodic.verify() and periodic.complete and periodic.root_count is sp.oo
tails = fp.infinite_root_coverage(sp.exp(x) - x * x, x)
assert tails.verify() and tails.complete and tails.root_count == 1
```

## Expected result

The compact exponential has one root; the repeated polynomial has two distinct roots of total multiplicity six.

Open endpoints, periodic indexed families and tail proofs complete different parts of the domain.

## Scope and next steps

A compact root count cannot cover an infinite domain without exhaustive families or tails. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
