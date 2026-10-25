"""Count distinct real roots throughout a polynomial parameter family."""

# %% Separate root-count strata
#| For x**2+a*x+b, the discriminant separates zero, one and two distinct real roots. The count at a repeated root is one, not its multiplicity two.
import sympy as sp

import funcprops as fp

x, a, b = sp.symbols("x a b", real=True)
proof = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=100)
assert proof.verify() and proof.complete
assert proof.specialize({a: 0, b: -1}) == 2
assert proof.specialize({a: 2, b: 1}) == 1
assert proof.specialize({a: 0, b: 1}) == 0

# %% Resume an unfinished partition
#| With no cell work, the exact unresolved frontier covers the whole query. It is valid partial evidence. Resumption discharges that frontier without changing the source or parameter domain.
partial = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=0)
assert partial.verify() and not partial.complete
assert partial.specialize({a: 0, b: -1}) is None
assert fp.resume_parameter_geometry(partial, max_cells=100).complete

# %% Respect parameter assumptions and scope
#| A positive parameter cannot be specialized to zero or a negative value. This interface supports rational polynomial families of degree at most four; it does not decompose arbitrary transcendental families.
p = sp.Symbol("p", positive=True)
guarded = fp.certify_parameter_geometry(x * x - p, x, (p,), max_cells=100)
assert guarded.specialize({p: 1}) == 2 and guarded.specialize({p: -1}) is None
try:
    fp.certify_parameter_geometry(sp.exp(x) - a, x, (a,))
except ValueError:
    pass
else:
    raise AssertionError("transcendental family admitted to polynomial geometry")
