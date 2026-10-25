"""Reuse exact Piecewise cells without losing owned values or jumps."""

# %% Partition a function with a jump
#| A jump can preserve strict order. A reusable partition records the input ownership of each interval and all seam values.
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
f = sp.Piecewise((x, x < 0), (x + 2, True))
p = fp.monotonic_partition(f, x, domain=sp.Interval(-1, 1), return_result=True)
assert p.complete and not p.critical_points_complete
assert p.same_strict_direction() is fp.Monotonicity.STRICTLY_INCREASING
image = fp.range_from_monotonic_partition(f, x, p).image
assert image == sp.Union(sp.Interval.Ropen(-1, 0), sp.Interval(2, 3))

# %% Inspect an owned point
#| The image is [-1,0) union [2,3]. Replacing the value at zero with 100 adds an isolated image point and breaks global increasing order.
spike = sp.Piecewise((100, sp.Eq(x, 0)), (x, True))
s = fp.monotonic_partition(spike, x, domain=sp.Interval(-1, 1), return_result=True)
assert s.complete and s.same_strict_direction() is None
assert fp.range_from_monotonic_partition(spike, x, s).image == sp.Union(
    sp.Interval(-1, 1) - sp.FiniteSet(0), sp.FiniteSet(100)
)

# %% Keep undefined points separate
#| A requested interval containing an original source hole is not certified as a full partition by this route. Partition completeness also does not assert completeness of the derivative zero set.
held = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
holey = sp.Piecewise((held, x < 1), (x, True), evaluate=False)
assert not fp.monotonic_partition(
    holey, x, domain=sp.Interval(-1, 2), return_result=True
).complete
