# Analyticity

`analytic`

## Mathematical definition

Analyticity certifies local representation by convergent power series throughout the requested domain.

## API and return values

```python
analytic(expr, variable, *, domain=Reals, assumptions=True, return_result=False)
```

Analyticity.ANALYTIC, NOT_ANALYTIC, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the rich result and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Entire real restriction

<!-- example-id: analytic-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.analytic(sp.exp(x), x)
result
```

Expected: ``Analyticity.ANALYTIC``.

Application: Justify convergent local power-series methods and analytic continuation steps.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Singularity/branch analysis, analytic closure rules, piecewise interface checks, domain restrictions, and theorem-backed function facts.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Real analyticity is stricter than smoothness; unresolved branch or singularity structure can produce UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`smoothness`](smoothness.md)
- [`meromorphic`](meromorphic.md)
- [`singularities`](singularities.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
