# Zeros

`function_zeros`

## Mathematical definition

The zero set contains the domain points at which the expression is exactly zero.

## API and return values

```python
function_zeros(expr, var, *, domain=True, return_result=False, allow_numerical=False, assumptions=True)
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

Exact algebraic solving, semialgebraic reduction, monotone partitions, structural special-function rules, and guarded parameter cases.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Infinite or transcendental zero sets may require structured representations, and numerical roots are opt-in rather than silently mixed with exact results.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_sign`](sign.md)
- [`function_oscillation`](oscillation.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
