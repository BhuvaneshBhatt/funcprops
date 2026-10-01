# Branch points

`branch_points`

## Mathematical definition

Branch-point analysis identifies points around which analytic continuation can change the value of a multivalued function.

## API and return values

```python
branch_points(expr, variable, *, assumptions=True, return_result=False)
```

A Boolean branch-point locus by default; return_result=True returns the supporting Singularity records.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Logarithmic branch point

<!-- example-id: branchpoints-log -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.branch_points(sp.log(x), x)
result
```

Expected: a branch point at ``x = 0``.

Application: Identify non-isolated analytic structure relevant to continuation and contour choices.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Known principal-branch structure, compositional preimages, algebraic/logarithmic branch rules, and assumptions.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General nested transcendental preimages can be difficult to reduce to a simple exact locus.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`branch_cuts`](branch_cuts.md)
- [`singularities`](singularities.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
