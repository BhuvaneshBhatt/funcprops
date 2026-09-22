# Bijectivity

`function_bijective`

## Mathematical definition

A function is bijective when it is both injective on its domain and surjective onto its codomain.

## API and return values

```python
function_bijective(expr, var, *, domain=True, codomain=Reals, assumptions=True)
```

TruthValue.TRUE, FALSE, or UNKNOWN, possibly stratified by parameters.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### A real bijection

<!-- example-id: bijective-cubic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_bijective(x**3, x)
result
```

Expected: ``TruthValue.TRUE``.

Application: Certify existence of a globally single-valued inverse between two domains.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Composition of certified injectivity and surjectivity with shared structural shortcuts.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

UNKNOWN from either component generally propagates unless an independent bijection theorem applies.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_injective`](injective.md)
- [`function_surjective`](surjective.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
