# Reachable outputs and missing values

A range describes the outputs a function actually attains on its source domain. Lower and upper bounds alone cannot describe its holes or disconnected components. funcprops assembles ranges from domain-aware image rules, monotone partitions, exact semialgebraic projection, critical-point geometry and supported special-function results. These operations do not require symbopt.

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
condition = fp.range(1 / x, x, y)
assert fp.condition_to_real_set(condition, y) == sp.S.Reals - sp.FiniteSet(0)
condition = fp.range(1 / x, x, y, domain=sp.Interval(-1, 1))
expected = sp.Union(sp.Interval(-sp.oo, -1), sp.Interval(1, sp.oo))
assert fp.condition_to_real_set(condition, y) == expected
```

For a rational inverse branch, its own domain restrictions remain necessary after substituting it into the source constraints. Omitting the inverse pole would add unreachable values such as zero in the reciprocal example. The semialg image backend preserves these restrictions. Its exact `qe`, `cad` and `auto` modes use graph projection or decline; explicitly requested optimization bounds describe an interval enclosure.

General transcendental range computation is incomplete. A returned enclosure, a partial critical-root cover and an exact image are different conclusions. An unresolved endpoint membership or attainment claim remains unknown. A finite sample of function values cannot establish exhaustive range coverage. Preserve the original source expression and domain record when applying algebraic simplifications; restrictions already erased by expression construction must be supplied explicitly.

See the [range API](properties/range.md), [source domains](domain-tracking-and-components.md) and [public analysis primitives](analysis-interface.md).

For transcendental expressions with implicit critical points, use [`analyze_range`](ranges.md). It can retain a unique critical point as an exact symbolic root, refine its value enclosure and distinguish a complete image from partial inner and outer sets. The same tutorial covers finite-period reductions, proved monotone tails and exact quadratic parameter families.
