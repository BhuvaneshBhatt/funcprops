# Periodicity

`periodicity`

## Mathematical definition

Periodicity detects constants, periodic functions and certified aperiodic cases; return_result=True can include a certified period.

## API and return values

```python
periodicity(expr, variable, *, domain=True, assumptions=True, return_result=False)
```

A Periodicity value by default; return_result=True returns the period and evidence when available.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Scaled periodic function

<!-- example-id: periodicity-scaled-sine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.periodicity(sp.sin(3*x), x, return_result=True)
result
```

Expected: periodic with period ``2*pi/3``.

Application: Reduce analysis or integration to a fundamental period.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Structural periodic identities, affine pullbacks, compatible-period combination, parameter assumptions, and exact simplification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to find a period is not by itself proof of aperiodicity; UNKNOWN is used when no aperiodicity theorem applies.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`symmetry`](symmetry.md)
- [`oscillation`](oscillation.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
