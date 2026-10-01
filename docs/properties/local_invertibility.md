# Local invertibility

`local_invertibility`

## Mathematical definition

A square differentiable map is locally invertible where its Jacobian determinant is nonzero, as certified by the inverse function theorem.

## API and return values

```python
local_invertibility(expressions, variables, *, domain=Reals, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the local-invertibility certificate and determinant evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Local invertibility

<!-- example-id: local-invertibility-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.local_invertibility((2*x + y, x - y), (x, y))
result
```

Expected: a verified local-invertibility certificate.

Application: Certify local coordinate validity without claiming global injectivity.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

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

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
