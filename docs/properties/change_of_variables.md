# Change of variables

`function_change_of_variables`

## Mathematical definition

Change-of-variables geometry records the local measure factor Abs(det J) for a square locally invertible coordinate transformation.

## API and return values

```python
function_change_of_variables(expressions, variables, *, domain=Reals, assumptions=True)
```

A ChangeOfVariablesCertificate containing the Jacobian, determinant, absolute determinant, orientation, local-invertibility certificate, and classification.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Change-of-variables volume factor

<!-- example-id: change-variables-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_change_of_variables((2*x + y, x - y), (x, y))
result
```

Expected: the certified factor ``Abs(det J) = 3``.

Application: Carry the correct local measure factor into transformed integrals or densities.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Exact Jacobian/determinant computation plus local-invertibility certification and symbolic verification of the absolute determinant factor.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The certificate is local and does not by itself prove a globally one-to-one parametrization or account for multiplicity across a noninjective map.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_local_invertibility`](local_invertibility.md)
- [`function_transformation_geometry`](transformation_geometry.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
