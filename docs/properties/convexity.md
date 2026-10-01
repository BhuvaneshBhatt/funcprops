# Convexity

`convexity`

## Mathematical definition

Convexity classifies ordinary, strict, strong, affine, concave, log-, quasi-, and pseudo-convex/concave behavior when certifiable.

## API and return values

```python
convexity(expr, variable, *, domain=True, strict_inequalities=True, all_properties=False, intervals=False, assumptions=True, return_result=False, **kwargs)
```

A Convexity value or a SymPy Piecewise for parameter-dependent classifications; `return_result=True` preserves the full PropertyResult and normalized ConvexityCertificate.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Strong convexity

<!-- example-id: convexity-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.convexity(x**2, x)
result
```

Expected: ``Convexity.STRONGLY_CONVEX``.

Application: Guarantee uniqueness and conditioning properties in optimization models.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Second-derivative/Hessian inequalities, semialgebraic certification, composition rules, strong-modulus bounds, piecewise slope-interface checks, and theorem-backed facts.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Secondary notions are often certified by sufficient implications.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`sign`](sign.md)
- [`monotonicity`](monotonicity.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
