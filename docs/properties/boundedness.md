# Boundedness

`function_boundedness`

## Mathematical definition

Boundedness records whether the image is bounded above, below, both, or neither on the requested domain.

## API and return values

```python
function_boundedness(expr, var, *, domain=True)
```

A Boundedness value or conditional PropertyResult.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### A globally bounded function

<!-- example-id: boundedness-sine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_boundedness(sp.sin(x), x)
result
```

Expected: ``Boundedness.BOUNDED``.

Application: Establish stability envelopes and safe numerical search regions.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Cheap structural closure rules first, followed by range/extremum reasoning, limits, periodic structure, and parameter stratification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to prove a finite extremum or range enclosure can yield UNKNOWN even when the function is mathematically bounded.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_range`](range.md)
- [`function_oscillation`](oscillation.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
