# Finite branch-chart gluing

Can local logarithms cover a loop without a global logarithm?

Checked logarithm transitions and selected power branches; nontrivial cycles remain explicit.

Run `python examples/branch_chart_gluing.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: branch-chart-gluing -->

## Example

```python
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
regions = (
    fp.CoverageRectangle(-2 - sp.I / 4, 2 - sp.I / 8),
    fp.CoverageRectangle(-2 + sp.I / 8, 2 + sp.I / 4),
    fp.CoverageRectangle(-2 - sp.I / 4, -sp.Rational(7, 4) + sp.I / 4),
    fp.CoverageRectangle(sp.Rational(7, 4) - sp.I / 4, 2 + sp.I / 4),
)
policy = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=160, max_depth=8
)
logarithm = fp.certify_log_atlas(z, z, regions, policy=policy)
assert logarithm.verify() and logarithm.coverage_complete
assert logarithm.obstructions and not logarithm.complete
square_log = fp.certify_log_atlas(z * z, z, regions, policy=policy)
power = fp.GluedPowerProof(square_log, sp.S.Half)
assert power.verify() and power.complete
assert fp.verify_certificate(power)
# This selects a glued square root; it does not redefine principal sqrt(z**2).
```

## Expected result

The logarithm has full chart coverage and an obstruction; the selected square root of z**2 glues.

Logarithm sheet transitions and power multipliers have different completion conditions.

## Scope and next steps

Finite log/power atlases do not supply a general chart-aware contour grammar. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
