# Jacobian

`jacobian`

## Mathematical definition

The Jacobian is the matrix of first partial derivatives of an explicit coordinate map with respect to its analysis variables.

## API and return values

```text
jacobian(expressions, variables, *, assumptions=True, return_result=False, work_budget=None)
```

The exact SymPy Jacobian matrix by default; return_result=True returns a replayable JacobianCertificate with derivative evidence.

| Parameter | Meaning |
| --- | --- |
| `expressions` | Ordered expression sequence defining a coordinate transformation. |
| `variables` | Independent symbol or ordered variable sequence for multivariate geometry. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |

## Domains, assumptions, and parameters

Differentiate the supplied map with respect to the declared coordinates. Assumptions can refine symbolic coefficients; this API has no domain keyword. A Jacobian alone does not certify a local or global inverse.

## Executable examples

### Exact affine Jacobian

<!-- example-id: jacobian-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.jacobian((2 * x + y, x - y), (x, y))
assert result == sp.ImmutableMatrix([[2, 1], [1, -1]])
```

Expected: the exact matrix ``[[2, 1], [1, -1]]``.

Application: Compute a replayable derivative matrix for a coordinate transformation.

## Applications

Use the executable jacobian examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Exact symbolic differentiation, including registered derivative rules where available, with structural replay of the derivative matrix.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The Jacobian matrix alone does not establish injectivity, global invertibility, or domain-wide nonvanishing of its determinant.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`determinant_nonvanishing`](determinant_nonvanishing.md)
- [`transformation_geometry`](transformation_geometry.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
