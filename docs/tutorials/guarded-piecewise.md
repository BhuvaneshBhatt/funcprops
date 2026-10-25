# Guarded and Piecewise results

How do parameter guards and singleton branches reach downstream results?

Finite real affine coefficients, supported branch coverage and singleton seams.

Run `python examples/guarded_piecewise.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: guarded-piecewise -->

## Example

```python
import sympy as sp

import funcprops as fp

x, a, b = sp.symbols("x a b", real=True)
cases = fp.solve(a * x + b, x, domain=sp.S.Reals, guarded=True, return_certificate=True)
assert cases.verify() and cases.complete and len(cases.cases) == 3
assert cases.specialize(sp.Ne(a, 0)).root_count == 1
assert (
    fp.monotonicity(a * x, x, assumptions=a > 0) is fp.Monotonicity.STRICTLY_INCREASING
)
f = sp.Piecewise((x, x < 0), (100, sp.Eq(x, 0)), (x + 10, True))
proof = fp.certify_property_coverage(f, x, sp.Interval(-1, 1))
assert proof.verify() and proof.complete
assert proof.conclusion("maximum").value == (100, sp.FiniteSet(0))
image = proof.conclusion("range").value.doit()
assert image.contains(100) is sp.true and image.contains(0) is sp.false
```

## Expected result

The affine equation has three guarded cases, and the Piecewise maximum is 100 at zero.

First-match ownership and parameter hypotheses are mathematical premises.

## Scope and next steps

Unresolved guards or missing seams cannot supply unconditional conclusions. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
