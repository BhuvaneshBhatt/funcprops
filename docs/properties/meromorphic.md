# Meromorphicity

`function_meromorphic`

## Mathematical definition

A meromorphic function is analytic except for isolated poles on the domain under consideration.

## API and return values

```python
function_meromorphic(expr, var, *, assumptions=True, details=False)
```

Meromorphicity.MEROMORPHIC, NOT_MEROMORPHIC, or UNKNOWN.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Rational meromorphic function

<!-- example-id: meromorphic-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_meromorphic(1 / x, x)
result
```

Expected: ``Meromorphicity.MEROMORPHIC``.

Application: Determine whether residue and pole-based complex-analysis techniques apply.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Structural singularity traversal, branch-point/cut exclusion, pole classification, and known meromorphic closure rules.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Natural boundaries, unresolved singularity heads, or branch structure may prevent a complete classification.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_poles`](poles.md)
- [`function_singularity_analysis`](singularity_analysis.md)
- [`function_analytic`](analytic.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
