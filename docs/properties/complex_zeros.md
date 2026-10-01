# Complex zeros

`complex_zeros`

## Mathematical definition

Complex-zero isolation finds and certifies zeros inside a finite complex rectangle.

## API and return values

```python
complex_zeros(expr, *args, assumptions=True, return_result=False, **kwargs)
```

An exact finite set when available, or a ComplexRootIsolationResult containing certified rectangles, counts, completeness, and diagnostic evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Certified complex zero in a rectangle

<!-- example-id: complex-zeros-exp -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
z = sp.symbols('z'); result = fp.complex_zeros(sp.exp(z) - 1, z, rectangle=(-1-sp.I, 1+sp.I), return_result=True)
result
```

Expected: one certified zero in the rectangle.

Application: Certify contour root counts before complex continuation, inversion, or spectral calculations.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Exact complex solving first, then structural holomorphy checks, validated argument-principle contour counting, complex-interval boundary exclusion, and count-preserving rational subdivision.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General holomorphy and boundary nonvanishing may remain uncertified; numerical winding estimates never upgrade an incomplete result to a proof.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`zeros`](zeros.md)
- [`analytic`](analytic.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
