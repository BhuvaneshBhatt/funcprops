# Monotonicity

`function_monotonicity`

## Mathematical definition

Monotonicity classifies a function as strictly increasing/decreasing, weakly monotone, constant, non-monotone, or unknown on a domain.

## API and return values

```python
function_monotonicity(expr, var, *, domain=True, strict_inequalities=True, all_properties=False, intervals=False, return_result=False, partition=None, assumptions=True)
```

A Monotonicity value, PropertyResult, or interval decomposition when requested.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Strict increase

<!-- example-id: monotonicity-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_monotonicity(sp.exp(x), x)
result
```

Expected: ``Monotonicity.STRICTLY_INCREASING``.

Application: Certify uniqueness of inverse values and one-dimensional optimization behavior.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Derivative-sign certification, shared monotone partitions, structural composition rules, theorem-backed special functions, piecewise interface checks, and parameter strata.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Disconnected domains and functions with many turning points may require interval output rather than a single global class.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_sign`](sign.md)
- [`function_injective`](injective.md)
- [`function_range`](range.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
