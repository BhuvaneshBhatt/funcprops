# Singularities

`singularities`

## Mathematical definition

This query returns the Boolean locus where a function is singular: the disjunction of poles, removable and essential singularities, branch points and cuts, definition cuts, and discontinuities.

## API and return values

```python
singularities(expr, variable, domain=Complexes, *, assumptions=True, return_result=False)
```

A SymPy Boolean condition by default; return_result=True returns a SingularityResult with classified Boolean loci and supporting records.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Boolean singularity locus

<!-- example-id: singularities-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.singularities(1/x, x)
result
```

Expected: the singular locus ``x = 0``.

Application: Obtain one composable Boolean locus for analytic obstructions before downstream analysis.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Shared structural singularity traversal and branch analysis, followed by guard-aware locus union and ConditionalExpression restriction.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Use singularity_analysis when completeness and unknown function heads matter to a proof.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`singularity_analysis`](singularity_analysis.md)
- [`branch_cuts`](branch_cuts.md)
- [`poles`](poles.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
