# Oscillation

`oscillation`

## Mathematical definition

Oscillation distinguishes persistent oscillation, finite oscillatory behavior, and nonoscillatory behavior on the selected domain.

## API and return values

```python
oscillation(expr, variable, *, domain=True, partition=None, assumptions=True, return_result=False)
```

An Oscillation classification by default; return_result=True exposes supporting partitions and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Persistent oscillation

<!-- example-id: oscillation-sine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.oscillation(sp.sin(x), x)
result
```

Expected: ``Oscillation.OSCILLATORY``.

Application: Detect repeated sign/turning behavior relevant to asymptotics and root searches.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Zeros, extrema, monotone partitions, periodic structure, asymptotic behavior, and special-function knowledge.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Highly irregular or parameter-dependent oscillation can remain UNKNOWN without a certifiable infinite pattern.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`zeros`](zeros.md)
- [`periodicity`](periodicity.md)
- [`boundedness`](boundedness.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
