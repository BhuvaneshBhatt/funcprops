# Discontinuities

`function_discontinuities`

## Mathematical definition

Discontinuity analysis locates points or guarded loci where continuity fails.

## API and return values

```python
function_discontinuities(expr, var, *, assumptions=True)
```

A tuple of Singularity records of kind DISCONTINUITY.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Jump discontinuity

<!-- example-id: discontinuities-piecewise -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
f = sp.Piecewise((0, x < 0), (1, True))
result = fp.function_discontinuities(f, x)
result
```

Expected: a discontinuity at ``x = 0``.

Application: Split quadrature, plotting, and approximation domains at genuine discontinuities.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Piecewise interface limits, denominator/domain failures, branch behavior, and structural singularity traversal.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

An empty tuple means no discontinuity was certified by the analysis, not necessarily a completeness theorem unless the associated detailed analysis is complete.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_continuous`](continuous.md)
- [`function_singularity_analysis`](singularity_analysis.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
