# Exact and partial real images

Which outputs are possible when critical points have no closed form?

Keep implicit critical values, refine partial images and transfer supported parameter families through real inverse branches.

Run `python examples/range_analysis.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: range-analysis -->

## Example

```python
import sympy as sp

import funcprops as fp
```

## Implicit values and refinement

A finite critical-root cover gives an exact implicit minimum. A zero-cell policy leaves the image partial and resumable.

```python
x, a, y = sp.symbols("x a y", real=True)
f = x * x + sp.sin(x)
partial = fp.analyze_range(
    f, x, sp.Interval(-1, 1), policy=fp.EnclosurePolicy(max_cells=0)
)
assert partial.verify() and not partial.complete
exact = fp.refine_range(partial, policy=fp.EnclosurePolicy(max_cells=128))
assert exact.complete and exact.verify()
assert exact.image.end == 1 + sp.sin(1)
assert exact.image.start.enclosure(16).verify()
```

## Periods and tails

Periodic image rules and derivative signs on whole tails extend finite-source analysis.

```python
periodic = fp.analyze_range(sp.sin(x) + sp.cos(2 * x), x)
assert periodic.image == sp.Interval(-2, sp.Rational(9, 8))
unbounded = fp.analyze_range(x * x + sp.exp(x), x)
assert unbounded.complete and unbounded.image.end is sp.oo
```

## Parameter families

The output condition retains open endpoints, vertex crossings and degree loss. Specialization is exact at the parameter boundary.

```python
family = fp.analyze_parameter_range(
    sp.exp(x * x + a * x), x, (a,), sp.Interval.open(-1, 1), value=y
)
assert family.verify() and not family.certified
assert family.specialize({a: 0}) == sp.Interval.Ropen(1, sp.E)
assert family.specialize({a: 2}) == sp.Interval.open(sp.exp(-1), sp.exp(3))
```

## Expected result

The implicit minimum has checked outward bounds; periodic and monotone-tail images complete; an open quadratic family retains its endpoint transitions.

An exact image, valid partial evidence, exhaustive critical roots and value accuracy are separate conclusions.

## Scope and next steps

Analytic cells need checked interior regularity and one-sided endpoint limits or closure regularity. Parameter images support rational polynomial families through degree three on fixed finite rational cells and selected invertible outer heads. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
