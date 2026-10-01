# Smoothness

`smoothness`

## Mathematical definition

Smoothness records continuity, the certified differentiability order, C-infinity status, analyticity, and exceptional loci.

## API and return values

```python
smoothness(expr, variable, *, domain=True, max_order=6, assumptions=True, return_result=False)
```

A SmoothnessResult with regularity fields and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Smooth entire function

<!-- example-id: smoothness-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.smoothness(sp.exp(x), x)
result
```

Expected: ``oo`` (C-infinity).

Application: Verify regularity assumptions required by approximation and differential methods.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Analytic-implies-smooth closure, structural regularity rules, branch/interface checks, and bounded derivative-order certification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Finite-order search can understate differentiability when no structural C-infinity proof is available.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`differentiability`](differentiability.md)
- [`analytic`](analytic.md)
- [`continuous`](continuous.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
