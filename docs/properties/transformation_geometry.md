# Transformation geometry

`transformation_geometry`

## Mathematical definition

Transformation geometry collects the derivative, determinant, local-invertibility, orientation, and change-of-variables facts for an explicit coordinate map.

## API and return values

```text
transformation_geometry(expressions, variables, *, domain=Reals, assumptions=True, return_result=False, work_budget=None)
```

A TransformationGeometry summary containing the exact Jacobian and the associated transformation certificates.

| Parameter | Meaning |
| --- | --- |
| `expressions` | Ordered expression sequence defining a coordinate transformation. |
| `variables` | Independent symbol or ordered variable sequence for multivariate geometry. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Combined transformation geometry

<!-- example-id: transformation-geometry-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.transformation_geometry((x + y, x - y), (x, y))
assert result.determinant == -2 and result.local_invertibility.classification is fp.TruthValue.TRUE
```

Expected: a combined Jacobian, determinant, local-invertibility, and change-of-variables summary.

Application: Inspect all transformation certificates with one query.

## Applications

Use the executable transformation geometry examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Delegation to the Jacobian, determinant-nonvanishing, inverse-function-theorem, and local measure-factor proof engines.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Global bijectivity is outside this local summary and must be established separately when an application requires it.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`jacobian`](jacobian.md)
- [`change_of_variables`](change_of_variables.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
