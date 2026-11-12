# Oscillatory images and parameter events

Use image analysis to determine which model outputs are possible, including whether boundary values are attained. Oscillations can have infinitely many stationary points while still admitting a short exact image proof. Parameter events describe where root counts or competing extremal values change. These facts belong to funcprops and require no optimization package.

## Oscillatory escape

A polynomial amplitude times a sine or cosine can escape in both output directions along exact phase sequences. Continuity then supplies every intermediate value. The source must contain a continuous unbounded interval for this rule.

```python
import sympy as sp
import funcprops as fp

x, y, a = sp.symbols("x y a", real=True)
r = fp.analyze_range(x * sp.sin(x), x, sp.Interval.open(0, sp.oo))
assert r.image is sp.S.Reals and r.verify()
assert not r.certified and not r.critical_coverage_complete
```

The supported escape grammar is a nonconstant rational polynomial amplitude of degree at most sixteen times one affine sine/cosine, plus a fixed real offset. The two exact sequences set the oscillator to opposite extrema. This proves surjectivity without enumerating stationary points. Bounded source intervals use the ordinary finite-cell machinery.

## Cubic parameter images

The parameter-image interface supports rational polynomial coefficients through degree three on fixed finite rational source cells, including degree loss and coefficient poles. It keeps critical candidates guarded and real even when their branches are inactive. The image condition does not require a total ordering of parameter-dependent critical values.

```python
family = fp.analyze_parameter_range(
    x**3 + a * x, x, (a,), sp.Interval.open(-1, 1), value=y
)
assert family.complete and family.verify()
assert family.specialize({a: 0}) == sp.Interval.open(-1, 1)
assert family.specialize({a: -sp.Rational(3, 4)}) == sp.Interval(
    -sp.Rational(1, 4), sp.Rational(1, 4)
)
assert family.condition.subs({a: -sp.Rational(3, 4), y: sp.Rational(1, 4)}) is sp.true
```

At the second specialization the same boundary value occurs at an owned interior stationary point, so it is attained even though the source endpoints are excluded. Candidate transition equations include degree loss, critical collisions, endpoint crossings and critical/endpoint value ties. They are event candidates, not a separately solved global parameter stratification. Supported invertible outer heads retain their output guards.

## Finite-limit oscillatory tails

`bound_range_tail` returns a `FiniteTailBound` for a fixed constant plus rationally decaying amplitudes times supported bounded oscillators. Rational amplitude ranges provide whole-tail bounds. Numerator degree must be smaller than denominator degree, with denominator degree at most six. The finite cutoff is rational and belongs to the compact core.

```python
sinc = sp.sin(x) / x
fact = fp.bound_range_tail(sinc, x, sp.Interval.open(8, sp.oo))
assert (fact.limit, fact.lower, fact.upper) == (
    0,
    -sp.Rational(1, 8),
    sp.Rational(1, 8),
)
assert fact.verify() and not fact.certified
r = fp.analyze_range(sinc, x)
assert r.complete and r.verify()
assert r.image.end == 1 and r.image.right_open
assert isinstance(r.image.start, fp.CriticalValue) and not r.image.left_open
assert r.domain_record.effective == sp.S.Reals - sp.FiniteSet(0)
```

The maximum remains unattained because the original expression is undefined at zero. Its minimum is an exact implicit stationary value. Native numerator-root covers can be reused for interior derivatives whose denominator is proved nonzero on the open cell. Symmetric disconnected sources can reduce to a checked reflected component. Tail bounds must lie inside the exact core image before they complete the image; a limiting value alone is insufficient.

The caller-side `asymptotic.range_facts.range_tail_facts` adapter can supply both infinite-limit and finite-limit facts. funcprops does not import asymptotic. Arbitrary uniform remainders and parameter-dependent cutoffs remain unsupported.

## Incommensurate phases and endpoint membership

Two affine trigonometric phases with algebraic irrational frequency ratio are dense on their phase torus. The selected rules support rational multiples of pi as phase offsets, rational weights, and sine/cosine powers one or two. Integer phase compatibility decides whether an extremal value occurs; density supplies its closure but does not prove attainment.

```python
u, v = sp.sin(x), sp.sin(sp.sqrt(2) * x)
assert fp.analyze_range(u + v, x).image == sp.Interval.open(-2, 2)
assert fp.analyze_range(u * u + v * v, x).image == sp.Interval.Ropen(0, 2)
assert fp.analyze_range(
    u * u + v * v, x, sp.S.Reals - sp.FiniteSet(0)
).image == sp.Interval.open(0, 2)
```

For these offsets, any simultaneous extremal phases must occur at zero. Removing that point can therefore remove endpoint ownership. More than two frequencies, general phase relations, nonalgebraic ratios and bounded source domains are outside this rule.

## Larger exact coefficient fields

The default coefficient discovery policy allows field degree four, four nonrational constants and eighty input operations. Larger fields are opt-in. Replay checks the actual isolated generator and coefficient identities independently of the discovery caps.

```python
c = sp.sqrt(2) + sp.sqrt(3) + sp.sqrt(5)
policy = fp.CoefficientFieldPolicy(max_degree=8)
field = fp.encode_algebraic_coefficients((c * x,), (x,), policy=policy)
assert field.verify() and sp.degree(field.polynomial, field.generator) == 8
assert fp.encode_algebraic_coefficients((c * x,), (x,)) is None
```

`range(..., coefficient_policy=policy)` also permits this field lift in exact semialgebraic range delegation. Native structural rules may already handle a query without lifting. Raising the cap can increase elimination cost; `work_budget` can bound the public query in an isolated process. Extra symbolic coefficient parameters, inexact coefficients and nonreal embeddings are unsupported.

## Convex level families

Root counts of a strongly convex level family can be partitioned at its minimum and endpoint values. Curvature and an exact interior critical point prove the two monotone branches. The event itself has one root of multiplicity two.

```python
f = sp.exp(x) - 1 - x - a
cover = fp.parameter_root_coverage(f, x, a, sp.Interval(-1, 1))
assert cover.complete and cover.verify()
for value, count, multiplicity in [(-1, 0, 0), (0, 1, 2), (sp.Rational(1, 10), 2, 2)]:
    point = fp.specialize_parameter_coverage(cover, value)
    assert point.verify() and (point.root_count, point.multiplicity_count) == (
        count,
        multiplicity,
    )
```

This route needs a finite fixed source interval, a positive outward curvature bound, an exact critical coordinate and ordered exact event values. It retains the source endpoint ownership and all unfinished parameter strata. Zero cell budgets still return incomplete coverage. General analytic bifurcation discovery, changing source domains and parameter-dependent tails remain open work.
