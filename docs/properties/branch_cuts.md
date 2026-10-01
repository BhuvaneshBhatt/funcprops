# Branch cuts

`branch_cuts`

## Mathematical definition

Branch-cut analysis returns the cuts used to make the selected principal branches single-valued.

## API and return values

```python
branch_cuts(expr, variable, *, assumptions=True, mode='conditions', return_result=False)
```

By default a tuple of logical cut conditions; alternate modes expose other supported representations.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Principal logarithm cut

<!-- example-id: branchcuts-log -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.branch_cuts(sp.log(x), x)
result
```

Expected: ``(x < 0,)``.

Application: Avoid crossing branch cuts in symbolic transformations and complex numerical paths.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Principal-branch registry facts, compositional preimages, algebraic transformation, simplification under assumptions, and cut normalization.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Branch cuts are representation/convention dependent; they are not intrinsic singularities of the underlying multivalued analytic object.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`branch_points`](branch_points.md)
- [`singularity_analysis`](singularity_analysis.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
