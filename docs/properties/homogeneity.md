# Homogeneity

`homogeneity`

## Mathematical definition

A function is homogeneous when a common scaling of its variables produces a fixed power of the scale; weighted homogeneity allows variable-specific weights.

## API and return values

```text
homogeneity(expr, variables, *, degree=None, weights=None, assumptions=True, return_result=False)
```

A Homogeneity value by default; return_result=True exposes degree, weights, and parameter conditions.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variables` | Independent symbol or ordered variable sequence for multivariate geometry. |
| `degree` | Requested homogeneity degree, when one is prescribed. |
| `weights` | Optional variable weights for weighted homogeneity. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The scaling identity is checked on the natural source domain under its scaling premises, intrinsic coordinate assumptions and supplied assumptions. This API has no domain keyword. Weighted homogeneity assigns one weight per coordinate; parameter-dependent conclusions retain their guards.

## Executable examples

### Homogeneous quadratic form

<!-- example-id: homogeneity-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.homogeneity(x**2 + y**2, (x, y), return_result=True)
assert result.classification is fp.Homogeneity.HOMOGENEOUS and result.degree == 2
```

Expected: homogeneous of degree ``2``.

Application: Exploit scaling laws in dimensional analysis and optimization.

## Applications

Check exact scaling laws before reducing variables or rescaling an optimization problem.

## How funcprops proves it

Polynomial weighted-degree grouping, exact scaling identities, parameter strata, and structural closure.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General nonpolynomial quasi-homogeneous identities may require simplification or assumptions beyond the current proof rules.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`symmetry`](symmetry.md)
- [`convexity`](convexity.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.structural_properties`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/structural_properties.py).
