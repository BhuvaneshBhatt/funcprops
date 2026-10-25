# Polynomial parameter geometry

How many distinct real roots does a polynomial family have?

Partition a bounded polynomial family by distinct real-root counts and retain unresolved regions.

Run `python examples/parameter_geometry.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: parameter-geometry -->

## Separate root-count strata

For x**2+a*x+b, the discriminant separates zero, one and two distinct real roots. The count at a repeated root is one, not its multiplicity two.

```python
import sympy as sp

import funcprops as fp

x, a, b = sp.symbols("x a b", real=True)
proof = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=100)
assert proof.verify() and proof.complete
assert proof.specialize({a: 0, b: -1}) == 2
assert proof.specialize({a: 2, b: 1}) == 1
assert proof.specialize({a: 0, b: 1}) == 0
```

## Resume an unfinished partition

With no cell work, the exact unresolved frontier covers the whole query. It is valid partial evidence. Resumption discharges that frontier without changing the source or parameter domain.

```python
partial = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=0)
assert partial.verify() and not partial.complete
assert partial.specialize({a: 0, b: -1}) is None
assert fp.resume_parameter_geometry(partial, max_cells=100).complete
```

## Respect parameter assumptions and scope

A positive parameter cannot be specialized to zero or a negative value. This interface supports rational polynomial families of degree at most four; it does not decompose arbitrary transcendental families.

```python
p = sp.Symbol("p", positive=True)
guarded = fp.certify_parameter_geometry(x * x - p, x, (p,), max_cells=100)
assert guarded.specialize({p: 1}) == 2 and guarded.specialize({p: -1}) is None
try:
    fp.certify_parameter_geometry(sp.exp(x) - a, x, (a,))
except ValueError:
    pass
else:
    raise AssertionError("transcendental family admitted to polynomial geometry")
```

## Expected result

The demonstrated quadratic strata have counts 2, 1 and 0; the partial frontier resumes to completion.

Counts refer to distinct roots and exact guarded regions, including degree loss.

## Scope and next steps

Degree is at most four in the root coordinate, with up to four real parameters and rational interval endpoints. Transcendental families are outside this interface. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
