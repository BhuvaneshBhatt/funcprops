# Jacobian

`function_jacobian`

## Mathematical definition

The Jacobian is the matrix of first partial derivatives of an explicit coordinate map with respect to its analysis variables.

## API and return values

```python
function_jacobian(expressions, variables, *, return_result=False)
```

The exact SymPy Jacobian matrix by default; return_result=True returns a replayable JacobianCertificate with derivative evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Exact affine Jacobian

<!-- example-id: jacobian-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_jacobian((2*x + y, x - y), (x, y))
result
```

Expected: the exact matrix ``[[2, 1], [1, -1]]``.

Application: Compute a replayable derivative matrix for a coordinate transformation.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Exact symbolic differentiation, including registered derivative rules where available, with structural replay of the derivative matrix.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The Jacobian matrix alone does not establish injectivity, global invertibility, or domain-wide nonvanishing of its determinant.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_determinant_nonvanishing`](determinant_nonvanishing.md)
- [`function_transformation_geometry`](transformation_geometry.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
