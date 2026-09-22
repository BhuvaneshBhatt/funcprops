# Function geometry

`function_geometry`

## Mathematical definition

Function geometry combines regularity, analyticity, convexity, singularities, boundary escape, level-boundedness, and attainment information in one structural summary.

## API and return values

```python
function_geometry(expr, variables, *, domain=Reals, assumptions=True)
```

A FunctionGeometry object containing the component property results and certificates.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Combined function geometry

<!-- example-id: geometry-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_geometry(x**2, x)
result
```

Expected: a combined regularity, singularity, convexity, and attainment summary.

Application: Collect structural facts for optimization and probability workflows in one query.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Delegation to the regularity, singularity, convexity, boundary-behavior, level-boundedness, and mode-existence engines with shared assumptions and domains.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The summary is only as complete as its component proof engines; unresolved component properties remain explicitly unresolved.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_convexity`](convexity.md)
- [`function_singularities`](singularities.md)
- [`function_mode_existence`](mode_existence.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
