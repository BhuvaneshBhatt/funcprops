# Transformation geometry

`transformation_geometry`

## Mathematical definition

Transformation geometry collects the derivative, determinant, local-invertibility, orientation, and change-of-variables facts for an explicit coordinate map.

## API and return values

```python
transformation_geometry(expressions, variables, *, domain=Reals, assumptions=True, return_result=False)
```

A TransformationGeometry summary containing the exact Jacobian and the associated transformation certificates.

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
result
```

Expected: a combined Jacobian, determinant, local-invertibility, and change-of-variables summary.

Application: Inspect all transformation certificates with one query.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

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

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
