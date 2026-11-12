# Real outputs, source domains and proof scope

A real-valued result can pass through complex intermediate values. Discarding those intermediate values changes the function being analyzed. This matters for logarithms on negative inputs, absolute values, complex exponentials and principal branches.

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
D = sp.Interval(-2, -sp.Rational(1, 2))
f = sp.Abs(sp.log(x))
assert fp.track_domain(f, x, D).effective == D
condition = fp.range(f, x, y, domain=D)
assert condition.subs(y, sp.pi) is sp.true
assert condition.subs(y, 0) is sp.false
```

Here `log(-1) = I*pi`, so its absolute value is pi. The image is `[pi, sqrt(pi**2+log(2)**2)]`. A real-only image of the inner logarithm would be empty on this source and cannot be used to infer the outer image.

Real-only composition transfers therefore require that the entire effective source also belongs to the inner function's real domain. When supported, branch expansion on a signed real source produces a real formula for the same values. The original source guards remain in force. A union of source components is handled component by component, with every component represented in replay. If a suitable real formula cannot be established, analysis remains unresolved instead of claiming an empty image or using incomplete critical geometry.

```python
f = sp.cos(sp.I * sp.log(x), evaluate=False)
condition = fp.range(f, x, y, domain=D)
assert condition.subs(y, -1) is sp.true
assert condition.subs(y, -sp.Rational(5, 4)) is sp.true
assert condition.subs(y, 0) is sp.false
```

This image is `[-5/4,-1]`. The interior maximum at -1 must survive branch analysis. An interval result from a general calculus backend is insufficient if its critical-point solver assumes that every intermediate value is real.

## Finite source cells

A finite cell needs the same definedness and reality checks as an interval. Source points must satisfy the coordinate's real domain and intrinsic assumptions. Each retained source value must be finite and real. Complex intermediate constants are allowed when the final value satisfies these conditions.

```python
result = fp.analyze_range((x + sp.I) ** 2, x, sp.FiniteSet(0))
assert result.image == sp.FiniteSet(-1) and result.verify()
```

Standalone `CriticalValueCover` replay checks these source conditions too. Matching a supplied list of point/value pairs is not enough to establish a real image.

## Parameter domains and event ownership

`parameter_domain` in `analyze_parameter_range` constrains only the declared parameter Symbols. It cannot contain free source coordinates, output coordinates or undeclared symbols. Construction and replay enforce the same rule.

A root-count cell must have one valid root count and multiplicity count throughout its parameter region. A cell containing a double-root event and a separate regular level cannot discard the event by counting only the two simple-root branches. Minimum-event cells retain their separate identity even when a parameter set is finite.

For `parameter_root_coverage`, both supplied sets must be fixed and exact and must respect the corresponding Symbols' assumptions. Conflicting sets raise `ValueError`; they do not produce a record labelled complete with failed replay. A positive parameter therefore needs a positive parameter domain.

```python
p = sp.Symbol("p", positive=True)
cover = fp.parameter_root_coverage(
    sp.exp(x) - 1 - x - p,
    x,
    p,
    sp.Interval(-1, 1),
    parameter_domain=sp.Interval.open(0, sp.oo),
)
point = fp.specialize_parameter_coverage(cover, sp.Rational(1, 10))
assert cover.complete and cover.verify()
assert point.verify() and point.root_count == 2
```

See [range analysis](ranges.md), [oscillatory and parameter examples](range-applications.md) and [parameter root coverage](infinite-and-parameter-coverage.md). Image exactness, canonical expression form, critical coverage and proof replay remain separate properties.
