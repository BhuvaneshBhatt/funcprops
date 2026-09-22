# Homogeneity

`function_homogeneity`

## Mathematical definition

A function is homogeneous when a common scaling of its variables produces a fixed power of the scale; weighted homogeneity allows variable-specific weights.

## API and return values

```python
function_homogeneity(expr, vars, *, degree=None, weights=None, assumptions=True, return_result=False)
```

A Homogeneity value by default; return_result=True exposes degree, weights, and parameter conditions.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Homogeneous quadratic form

<!-- example-id: homogeneity-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_homogeneity(x**2 + y**2, (x, y), return_result=True)
result
```

Expected: homogeneous of degree ``2``.

Application: Exploit scaling laws in dimensional analysis and optimization.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Polynomial weighted-degree grouping, exact scaling identities, parameter strata, and structural closure.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General nonpolynomial quasi-homogeneous identities may require simplification or assumptions beyond the current proof rules.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_symmetry`](symmetry.md)
- [`function_convexity`](convexity.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
