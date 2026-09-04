# Periodicity

`function_periodicity`

## Mathematical definition

Periodicity detects constants, periodic functions and certified aperiodic cases; detailed results can include a period.

## API and return values

```python
function_periodicity(expr, var, *, domain=True, assumptions=True, details=False)
```

A Periodicity value or detailed result containing the period and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Scaled periodic function

<!-- example-id: periodicity-scaled-sine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_periodicity(sp.sin(3 * x), x, details=True)
result
```

Expected: periodic with period ``2*pi/3``.

Application: Reduce analysis or integration to a fundamental period.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Structural periodic identities, affine pullbacks, compatible-period combination, parameter assumptions, and exact simplification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to find a period is not by itself proof of aperiodicity; UNKNOWN is used when no aperiodicity theorem applies.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_symmetry`](symmetry.md)
- [`function_oscillation`](oscillation.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
