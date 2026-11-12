# Exact and partial real images

Use a range when you need to know which outputs a function attains, including missing values and endpoint membership. This can answer whether an equation has a real solution, constrain a model's possible outputs or provide image information to an optimizer. `range` returns a mathematical condition. `analyze_range` exposes the domain, critical-value evidence and any unresolved work behind an image computation. Neither interface depends on symbopt.

## Choose the interface

| Need | Interface | Mathematical return |
| --- | --- | --- |
| A direct condition on an output symbol | `range(f, x, y, domain=D)` | An exact supported condition, guarded result or unresolved answer |
| Explicit bounded, periodic or tail analysis | `analyze_range(f, x, D)` | `RangeAnalysis` with `image`, `inner`, `outer` and unresolved source regions |
| More effort on an existing analysis | `refine_range(result, policy=...)` | Refined analysis reusing retained search states |
| A supported polynomial parameter family | `parameter_range` or `analyze_parameter_range` | A quantifier-free condition, with optional transition/replay information |

Automatic `range` tries structural, algebraization, calculus and special-function rules before a bounded analytic image fallback, including supported periodic and tail transfers. Fixed finite-domain families with declared real coefficients can use the polynomial parameter rules up to degree three. Explicit `analyze_range` supplies partial information, a configurable policy, reusable evidence and provider-supplied tail facts; `analyze_parameter_range` supplies family transitions and replay metadata. Unsupported inputs still remain unresolved.

For an exact algebraic image, semialg's `function_range` offers graph projection. Its `bounds` mode returns the interval between the extremal bounds and can contain missing interior values. For an infimum, optimizer or optimization certificate, use symbopt. See [package roles and range semantics](https://github.com/BhuvaneshBhatt/symbopt/blob/main/docs/guide/ranges-and-extrema.md).

## Implicit critical values

A stationary point need not have a closed form. For `x**2 + sin(x)` on `[-1,1]`, the unique minimum is the value at the unique root of `2*x + cos(x)`. funcprops can keep both the root and its value as exact SymPy expressions.

```python
import sympy as sp
import funcprops as fp

x = sp.Symbol("x", real=True)
analysis = fp.analyze_range(x * x + sp.sin(x), x, sp.Interval(-1, 1))
assert analysis.complete and not analysis.certified
assert analysis.image.end == 1 + sp.sin(1)
minimum = analysis.image.start
assert isinstance(minimum, fp.CriticalValue)
bounds = minimum.enclosure(20)
assert bounds.verify()
assert bounds.upper - bounds.lower < sp.Rational(1, 10**19)
assert analysis.verify()
```

`ImplicitRealRoot(Lambda(x, f), interval)` means the unique real zero of a fixed exact function in a finite rational isolating interval. `ImplicitRealRoot.from_cover` reuses a checked single-root cover or a selected owned leaf, including exact nonrational interval bounds. Neither construction treats a numerical estimate as an exact root. `CriticalValue(Lambda(x, g), root)` means the exact value of `g` there. Their bound coordinate is not a free symbol, and numerical evaluation uses outward enclosures. Different isolating descriptions of the same number need not have identical SymPy structure. `same_root` compares selected root descriptions using uniqueness and checked locations. `critical_values_equal` also recognizes selected reflected-root identities. Equality and ordering of arbitrary implicit values can remain undecided. Bound coordinates remain constant under substitution and transport retains the proof without another root search.

## One-sided endpoints and finite seams

General cells can use a checked real C1 interior and one-sided limits, without a smooth derivative extension through the boundary. Owned endpoints are evaluated separately. Finite `Piecewise`, `Abs`, `Min` and `Max` seams use owned source cells. Unsupported symbolic continuity or critical-root analysis can leave a cell unresolved. This route declares exact symbolic continuity/root-backend replay; native root covers retain their independent kernel checks.

```python
x = sp.Symbol("x", real=True)
assert fp.analyze_range(x * sp.log(x), x, sp.Interval(0, 1)).image == sp.Interval(
    -1 / sp.E, 0
)
assert fp.analyze_range(
    sp.sqrt(x) + sp.exp(x), x, sp.Interval(0, 1)
).image == sp.Interval(1, 1 + sp.E)
assert fp.analyze_range(
    sp.log(x) + 1 / x, x, sp.Interval.open(0, 1)
).image == sp.Interval.open(1, sp.oo)
```

The first source is undefined at zero, yet the image includes zero because it is attained at 1. The real-domain fallback for rational affine expressions in one principal logarithm retains coefficient-zero points, log-zero exclusions and original rational poles.

## Refinement and completion

```python
coarse = fp.analyze_range(
    x * x + sp.sin(x),
    x,
    sp.Interval(-1, 1),
    policy=fp.EnclosurePolicy(max_cells=0),
)
assert not coarse.complete
assert coarse.inner is sp.S.EmptySet
assert coarse.outer is sp.S.Reals
fine = fp.refine_range(coarse, policy=fp.EnclosurePolicy(max_cells=128))
assert fine.complete and fine.verify()
```

`inner` contains only attained values justified by the analysis. `outer` contains the entire image. `unresolved` identifies source regions whose images are not yet exact. A partial cover can verify successfully: replay validity does not imply completion. Critical-root coverage and value coverage are reported separately. Canonical interval endpoints require enough value ordering. When critical geometry and endpoint limits are complete but values cannot be sorted, `image` can be an exact SymPy `ConditionSet`. `as_condition(y)` returns its output membership formula without selecting a least and greatest site. A constant cell retains an owned interior representative. Source components are joined by union.

`certified=False` is the default for these analysis interfaces. `certified=True` requests replay of the returned record and sets its certification field only on success. A caller can replay later with `verify()` or `verify_certificate()`. Critical-root and value witnesses are checked independently of root discovery. Transfer replay can also use the documented source-domain and exact-limit backends.

`EnclosurePolicy` controls each cell's root-search and enclosure precision. `refine_range` resumes retained root-search states and refines value bounds. `seconds` runs the whole range query in an isolated worker with a hard wall-clock deadline; exhaustion returns a `BudgetedResult` without an exact image claim. Symbolic image rules and implicit-expression constructors have their own bounded operations, so `max_cells` is not a global instruction counter.

## Flat stationary points and effort

`EnclosurePolicy.max_root_order` caps automatic exact-jet deflation independently of `max_taylor_order`, which controls exclusion polynomials. Its default is 8. The first nonzero jet is inspected once per candidate and shared across nested cells. A nonzero derivative enclosure then proves the Taylor unit and root multiplicity. Numerical near-zeros cannot establish a vanishing jet.

```python
flat = x**6 + (sp.exp(x) - 1) ** 6
D = sp.Interval(-sp.Rational(1, 100), sp.Rational(1, 100))
analysis = fp.analyze_range(
    flat, x, D, policy=fp.EnclosurePolicy(max_cells=16, max_depth=2)
)
assert analysis.image.start == 0
assert analysis.cells[0].critical_cover.root_count == 1
assert analysis.cells[0].critical_cover.multiplicity_count == 5
assert analysis.verify()
```

## Interpreting unresolved work

Start with `reason`, `domain_record.complete` and `unresolved`. An unresolved source-domain record needs definedness or real-output analysis. `unsupported-closure-regularity` means that neither a real C1 extension through both endpoints nor the supported interior-and-limit route succeeded; it does not imply that the image fails to exist. `unresolved-critical-values-or-order` can indicate incomplete critical geometry, missing value bounds or value comparisons that have not separated. More precision can separate unequal values. Selected identity rules can establish common-root or reflection equalities; general analytic equality remains unresolved. Exact image conditions can still be complete without a canonical interval order.

`critical_coverage_complete` describes derivative-root coverage in routes that supply it. An elementary image rule can complete without enumerating critical roots. `value_coverage_complete` describes exact transferred image information or available value-site bounds. Neither field alone proves an exact image or an optimizer's attainment. Ordinary partial intervals can supply attained inner values by continuity and witnessed source values. The computation must preserve each source component when taking unions.

## Periods, tails and compositions

```python
periodic = fp.analyze_range(sp.sin(x) + sp.cos(2 * x), x)
assert periodic.image == sp.Interval(-2, sp.Rational(9, 8))
global_image = fp.analyze_range(x * x + sp.exp(x), x)
assert global_image.complete and global_image.image.end is sp.oo
assert isinstance(global_image.image.start, fp.CriticalValue)
```

Elementary images transfer through supported monotone and piecewise monotone heads. Domain tracking retains original holes before normalization. Sine and cosine use an explicit stationary lattice; tangent and cotangent split at poles. Rational quadratic trigonometric reductions use `sin(x)**2 + cos(x)**2 = 1`.

A syntactically proved common period reduces an unbounded interval request to a fully contained finite window at least one period long. The period check applies to the original expression, including its source restrictions. A bounded window may still return partial information. Monotone-tail transfers require a derivative sign on the whole tail and its exact limit. Polynomial-plus-bounded-remainder facts can also close some nonmonotone tails. Both routes retain the compact core and source binding. A sample or an eventual trend without a finite exclusion bound is insufficient.

## Explicit bounds for nonmonotone tails

```python
f = x * x + sp.sin(x**3) ** 2
image = fp.analyze_range(f, x)
assert image.image == sp.Interval(0, sp.oo)
assert image.verify()
fact = fp.bound_range_tail(f, x, sp.Interval.open(sp.Rational(1, 2), sp.oo))
assert fact.bound == sp.Rational(1, 4) and fact.limit is sp.oo
assert fact.verify() and not fact.certified
```

`TailValueBound` records a rational polynomial trend, a bounded oscillatory remainder, a whole-tail finite bound and an infinite limit. Its checker reconstructs the structural bounds and outward polynomial signs. The connected source must be continuous; tail exclusion and the core image then establish the remaining intermediate values. This can work even when the derivative has infinitely many tail zeros. Critical coverage of those tails is not claimed. If checked tails have opposite infinite limits and the entire source is a continuous interval, the intermediate value theorem gives the whole real line without a compact critical-root search.

The optional caller-side adapter `asymptotic.range_facts.range_tail_facts` proposes limits and returns these funcprops-owned records. Pass them as the tuple `tail_facts` to `analyze_range`. Funcprops does not import asymptotic. Certified analysis replays the actual tail bounds, not a provider status flag. The current adapter covers polynomial trends with supported bounded remainders and rationally damped bounded oscillators with finite limits. Arbitrary uniform remainders and parameter-dependent cutoffs remain unsupported.

## Parameter-dependent ranges

```python
x, a, y = sp.symbols("x a y", real=True)
family = fp.analyze_parameter_range(
    sp.exp(x * x + a * x),
    x,
    (a,),
    sp.Interval.open(-1, 1),
    value=y,
)
assert family.complete and family.verify()
assert family.specialize({a: 0}) == sp.Interval.Ropen(1, sp.E)
assert family.specialize({a: 2}) == sp.Interval.open(sp.exp(-1), sp.exp(3))
condition = family.condition
```

The condition is quantifier free in the declared output and parameters. Polynomial coefficients through degree three can be rational functions of several real parameters. The formula retains lower-degree cases, coefficient poles, endpoint ownership, guarded real critical points and endpoint ties. `transitions` lists candidate degree-loss, critical-collision, endpoint-crossing and equal-value events. Some events may not change the image. An optional `parameter_domain` constrains the declared parameters; specialization outside it or at a coefficient pole has empty image.

Supported outer maps are `exp`, `log`, `sinh`, `asinh`, `tanh`, `atanh`, `atan`, `asin`, `acos`, `acosh`, `erf` and `erfc`. Their real inverse branch and output guard transfer the polynomial image formula without optimizing over parameters. `parameter_range` returns the condition directly; `analyze_parameter_range` also returns transitions and replay metadata.

## Source and proof scope

Real-only composition preserves the entire effective inner domain. Supported signed-source branch expansions retain the original guards and all source components. Finite-cell replay requires defined finite real outputs. See [real outputs and proof scope](real-source-contracts.md) for examples and parameter-domain requirements.

## Capability boundaries

| Source or operation | Support | Remaining limitations |
| --- | --- | --- |
| Elementary compositions | Exact image rules with domain intersections and endpoint ownership | Unsupported heads or undecided real order decline |
| Bounded analytic cells | Complete critical covers, exact value conditions and one-sided endpoint data | Native closure proofs or supported exact real-interior/limit backends |
| Partial bounded images | Inner/outer sets with retained root-search state | Value bounds or implicit-value ordering may remain unresolved |
| Periodic unbounded sources | Common affine trigonometric periods and a contained full-period window | Unproved source periodicity declines; selected incommensurate rules use a separate density proof |
| Unbounded nonperiodic sources | Monotone tails, polynomial trends with bounded remainders, rationally damped oscillators and selected oscillatory escape | Other growth and parameterized tail facts can remain unresolved |
| Parameter families | Rational polynomials of degree at most three on fixed finite rational interval/point unions, with one supported invertible outer head | Moving source cells and general transcendental critical-point collisions remain unsupported |
| Global optimization | Image and critical-value primitives for consumers | Optimizers and optimization certificates belong to symbopt |

These methods do not supply a complete range algorithm for arbitrary transcendental expressions. Unsupported work retains an explicit reason or unresolved set. See the [executable example](../examples/range_analysis.py), [source-domain contract](domain-tracking-and-components.md) and [analysis primitives](analysis-interface.md).

## Related guides

See the [image methods and proof obligations](design/real-images.md) for the evidence contracts. Selected incommensurate phases, damped oscillatory tails, cubic images and convex parameter collisions are covered in [image applications](range-applications.md). More general root clusters, analytic parameter events, higher-rank phase relations and multivariate transcendental images remain gaps.
