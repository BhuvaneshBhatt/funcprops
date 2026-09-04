# Zeros

`function_zeros`

## Mathematical definition

The zero set contains the domain points at which the expression is exactly zero.

## API and return values

```python
function_zeros(expr, var, *, domain=True, return_result=False, allow_numerical=False)
```

Usually a SymPy Set; return_result=True exposes structured/conditional information.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Exact real zeros

<!-- example-id: zeros-polynomial -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_zeros((x - 1) * (x + 2), x)
result
```

Expected: ``{-2, 1}``.

Application: Locate exact roots used for sign partitions and critical-event analysis.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Exact algebraic solving, semialgebraic reduction, structural special-function rules, guarded parameter cases, and certified real univariate isolation on finite intervals. Before isolation, disconnected real domains are decomposed into interval and point cells, so certificates never cross poles, logarithmic exclusions, radical gaps, or other undefined points. Concrete solution sets may contain both isolated roots and intervals on which the expression is identically zero; both are retained as parts of the mathematical zero set.

When ordinary symbolic solving is undecided on a finite interval, funcprops first tries an outward-rounded interval evaluation for a supported elementary vocabulary. An enclosure excluding zero proves the cell root-free; an enclosure of the derivative excluding zero proves strict monotonicity and reduces the cell to endpoint signs plus rational root isolation. Exact range reasoning is an independent second route when interval evaluation is unsupported or inconclusive. The monotonic-partition isolator remains available for harder cells. Exact roots at attained critical boundaries are retained directly, with finite multiplicity when repeated differentiation proves it.

Point signs used by these certificates go through `robust_real_sign()`: exact symbolic sign reasoning is preferred, with an interval-arithmetic exp/log fallback only for unresolved numeric expressions. For a restricted class of real exponential polynomials, `exponential_fourier_count()` recursively normalizes and differentiates the expression, removing one exponential term per level; exact derivative roots then partition the interval into monotonic cells whose endpoint signs certify a distinct-root count.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Infinite or transcendental zero sets may require structured representations. Domain-cell decomposition requires the real domain and structural exceptional points to reduce to explicit exact interval/point components. Interval resolution requires either a supported rigorous interval enclosure or an exact range/derivative-range proof; otherwise funcprops falls back to monotonic partitioning and existing certified/numerical layers. If any valid domain cell remains unresolved, completeness is not claimed. Heuristic numerical roots remain opt-in and are never promoted to certified roots merely because a numerical solver converged.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_sign`](sign.md)
- [`function_oscillation`](oscillation.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).


### Repeated and touching roots

For an explicit repeated factor ``g(x)**m`` with integer ``m >= 2``, funcprops isolates
the roots of ``g`` and lifts the resulting certificates to the original expression.
This certifies even-multiplicity roots that do not change sign and scales a proved
underlying multiplicity by ``m``.

With ``allow_numerical=True``, a second fallback samples the derivative only to propose
stationary candidates.  A numerical candidate is never accepted merely because the
residual is small: it must first be reconstructed as an exact value, exact substitution
must prove that the original expression vanishes there, and repeated differentiation
must prove a finite even multiplicity.  Such results are certified roots, but the
result remains incomplete unless the surrounding interval has independently been
proved root-complete.
