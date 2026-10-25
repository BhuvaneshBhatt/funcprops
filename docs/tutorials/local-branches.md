# Selected local branches

How does a selected logarithmic germ affect a local residue?

Explicit local logarithm values; no global chart-gluing claim.

Run `python examples/local_branches.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: local-branches -->

## Example

```python
from dataclasses import replace

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
chart = fp.LocalBranchContext(-1, ((z, sp.I * sp.pi),))
residue = fp.residue(
    sp.log(z) / (z + 1), z, -1, branch_context=chart, return_certificate=True
)
assert residue is not None and residue.verify() and residue.residue == sp.I * sp.pi
assert not replace(residue, branch_context=None).verify()
assert fp.residue(sp.log(z) / (z + 1), z, -1, return_certificate=True) is None
```

## Expected result

The selected residue is I*pi; removing the branch context fails replay.

A local germ supplies source-bound branch values at a particular point.

## Scope and next steps

A local branch calculation is not a global principal-branch identity. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
