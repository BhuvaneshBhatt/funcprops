# Local invertibility

`local_invertibility`

## Mathematical definition

A square real C1 map is locally invertible where its Jacobian determinant is nonzero, as certified by the inverse function theorem.

## API and return values

```text
local_invertibility(expressions, variables, *, domain=Reals, assumptions=True, return_result=False, work_budget=None)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the local-invertibility certificate and determinant evidence.

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

### Local invertibility

<!-- example-id: local-invertibility-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.local_invertibility((2 * x + y, x - y), (x, y))
assert result is fp.TruthValue.TRUE
```

Expected: a verified local-invertibility certificate.

Application: Certify local coordinate validity without claiming global injectivity.

## Applications

Use the executable local invertibility examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

The exact Jacobian and determinant-nonvanishing certificate are combined through the inverse-function-theorem implication.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Local invertibility is not global injectivity; nonsquare maps and unresolved determinant geometry remain UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`determinant_nonvanishing`](determinant_nonvanishing.md)
- [`change_of_variables`](change_of_variables.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
