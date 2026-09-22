# Range

`function_range`

## Mathematical definition

The range is the set of output values attained by the expression on the requested input constraints.

## API and return values

```python
function_range(expr, var, y, *, constraints=True, method='auto', partition=None, assumptions=True, **kwargs)
```

A SymPy condition in the output symbol, possibly wrapped in a conditional PropertyResult for parameter strata.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Range on a restricted interval

<!-- example-id: range-restricted-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_range(x**2, x, y, constraints=sp.And(x >= -2, x <= 3))
result
```

Expected: ``(y >= 0) & (y <= 9)``.

Application: Derive certified output bounds for downstream constraints.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Semialgebraic elimination, monotone partitions, endpoint limits, extrema, structural special-function facts, and exact set reasoning.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General transcendental range computation is undecidable in closed form; unsupported cases remain conservative rather than sampled.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_boundedness`](boundedness.md)
- [`function_surjective`](surjective.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
