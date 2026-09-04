# Singularity analysis

`function_singularity_analysis`

## Mathematical definition

Detailed singularity analysis reports analytic obstructions together with completeness and unresolved-head information.

## API and return values

```python
function_singularity_analysis(expr, var, *, domain=Complexes, assumptions=True, ignore_unknown=False)
```

A SingularityAnalysis object containing singularity groups, domain exterior, completeness, unknown heads, and provenance.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Detailed singularity analysis

<!-- example-id: singularity-analysis-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_singularity_analysis(1 / x, x)
result
```

Expected: a complete analysis with one pole.

Application: Inspect completeness and provenance when a downstream proof requires certified singularity coverage.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Structural traversal, local singularity classification, branch analysis, discontinuity analysis, and domain comparison.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

complete=False is an explicit warning that the returned inventory is not exhaustive.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_singularities`](singularities.md)
- [`function_discontinuities`](discontinuities.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
