"""Exact implicit values, refinement and parameter-dependent real images."""

import sympy as sp

import funcprops as fp

# %% Implicit values and refinement
#| A finite critical-root cover gives an exact implicit minimum. A zero-cell policy leaves the image partial and resumable.
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
# %% Periods and tails
#| Periodic image rules and derivative signs on whole tails extend finite-source analysis.
periodic = fp.analyze_range(sp.sin(x) + sp.cos(2 * x), x)
assert periodic.image == sp.Interval(-2, sp.Rational(9, 8))
unbounded = fp.analyze_range(x * x + sp.exp(x), x)
assert unbounded.complete and unbounded.image.end is sp.oo
# %% Parameter families
#| The output condition retains open endpoints, vertex crossings and degree loss. Specialization is exact at the parameter boundary.
family = fp.analyze_parameter_range(
    sp.exp(x * x + a * x), x, (a,), sp.Interval.open(-1, 1), value=y
)
assert family.verify() and not family.certified
assert family.specialize({a: 0}) == sp.Interval.Ropen(1, sp.E)
assert family.specialize({a: 2}) == sp.Interval.open(sp.exp(-1), sp.exp(3))
