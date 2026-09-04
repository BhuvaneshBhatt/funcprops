# Differentiability

`function_differentiability`

## Mathematical definition

Differentiability asks whether derivatives exist throughout a domain, optionally through a requested finite order.

## API and return values

```python
function_differentiability(expr, var, *, domain=True, order=None, all_properties=False, details=False, max_order=6)
```

A Differentiability value or PropertyResult with regularity evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### A corner at the origin

<!-- example-id: differentiability-absolute -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_differentiability(sp.Abs(x), x)
result
```

Expected: ``Differentiability.NOT_DIFFERENTIABLE``.

Application: Check whether derivative-based solvers are valid on an entire domain.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

The smoothness engine, domain-aware exceptional-locus analysis, analytic closure rules, and certified finite-order derivative checks.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The bounded max_order search is a certification limit, not a claim that higher derivatives fail to exist.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_smoothness`](smoothness.md)
- [`function_continuous`](continuous.md)
- [`function_analytic`](analytic.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
