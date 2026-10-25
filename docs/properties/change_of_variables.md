# Change of variables

`change_of_variables`

## Mathematical definition

Change-of-variables geometry records the local measure factor Abs(det J) for a square locally invertible coordinate transformation.

## API and return values

```text
change_of_variables(expressions, variables, *, domain=Reals, assumptions=True, return_result=False, work_budget=None)
```

A ChangeOfVariablesCertificate containing the Jacobian, determinant, absolute determinant, orientation, local-invertibility certificate, and classification.

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

### Change-of-variables volume factor

<!-- example-id: change-variables-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.change_of_variables((2 * x + y, x - y), (x, y))
assert result.classification is fp.TruthValue.TRUE and result.volume_factor == 3
```

Expected: the certified factor ``Abs(det J) = 3``.

Application: Carry the correct local measure factor into transformed integrals or densities.

## Applications

Use the executable change of variables examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Exact Jacobian/determinant computation plus local-invertibility certification and symbolic verification of the absolute determinant factor.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The certificate is local and does not by itself prove a globally one-to-one parametrization or account for multiplicity across a noninjective map.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`local_invertibility`](local_invertibility.md)
- [`transformation_geometry`](transformation_geometry.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
