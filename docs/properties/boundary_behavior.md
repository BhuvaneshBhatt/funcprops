# Boundary behavior

`boundary_behavior`

## Mathematical definition

Boundary behavior records certified limits at unbounded real-domain escape directions relevant to global geometry.

## API and return values

```python
boundary_behavior(expr, variable, *, domain=Reals, assumptions=True, return_result=False)
```

A BoundaryBehavior summary containing the analyzed domain, certified BoundaryLimit records, completeness, and provenance.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Quadratic escape limits

<!-- example-id: boundary-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.boundary_behavior(x**2, x)
result
```

Expected: both real escape limits are ``+oo``.

Application: Certify endpoint escape behavior before coercivity or attainment reasoning.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Exact symbolic one-sided limits at real escape boundaries, while unsupported multivariate radial escape geometry remains unresolved.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General multivariate escape directions are not exhaustively classified; an incomplete result explicitly preserves that limitation.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`level_boundedness`](level_boundedness.md)
- [`geometry`](geometry.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
