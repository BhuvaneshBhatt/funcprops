# Singularities

`function_singularities`

## Mathematical definition

This query returns a grouped inventory of poles, removable/essential singularities, branch points, branch cuts, and definition cuts.

## API and return values

```python
function_singularities(expr, var, *, domain=Complexes, assumptions=True)
```

A dictionary whose values are tuples of Singularity records or cut conditions.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Grouped singularities

<!-- example-id: singularities-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_singularities(1 / x, x)
result
```

Expected: one pole and no branch points.

Application: Obtain a compact inventory of analytic obstructions before complex-domain analysis.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Shared structural singularity traversal and branch analysis, grouped by singularity kind.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Use function_singularity_analysis when completeness and unknown function heads matter to a proof.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_singularity_analysis`](singularity_analysis.md)
- [`function_branchcuts`](branchcuts.md)
- [`function_poles`](poles.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
