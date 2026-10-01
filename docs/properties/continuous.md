# Continuity

`continuous`

## Mathematical definition

Continuity certifies that the function has no value/limit mismatch at points of the requested domain.

## API and return values

```python
continuous(expr, variable, *, domain=Reals, assumptions=True, return_result=False)
```

Continuity.CONTINUOUS, DISCONTINUOUS, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the rich result and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Continuous but nonsmooth

<!-- example-id: continuous-absolute -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.continuous(sp.Abs(x), x)
result
```

Expected: ``Continuity.CONTINUOUS``.

Application: Verify hypotheses of existence theorems and interval methods.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Structural closure, one-sided interface limits for Piecewise expressions, singularity analysis, and domain restriction.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Complicated limit problems can remain UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`discontinuities`](discontinuities.md)
- [`differentiability`](differentiability.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
