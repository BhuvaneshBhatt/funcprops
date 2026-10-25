# Periodicity

`periodicity`

## Mathematical definition

Periodicity detects constants, periodic functions and certified aperiodic cases; return_result=True can include a certified period.

## API and return values

```text
periodicity(expr, variable, *, domain=True, assumptions=True, return_result=False)
```

A Periodicity value by default; return_result=True returns the period and evidence when available.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Scaled periodic function

<!-- example-id: periodicity-scaled-sine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.periodicity(sp.sin(3 * x), x, return_result=True)
assert result.classification is fp.Periodicity.PERIODIC and sp.simplify(result.period - 2*sp.pi/3) == 0
```

Expected: periodic with period ``2*pi/3``.

Application: Reduce analysis or integration to a fundamental period.

## Applications

Reduce a supported infinite-domain problem to a fundamental period with exact endpoint ownership.

## How funcprops proves it

Structural periodic identities, affine pullbacks, compatible-period combination, parameter assumptions, and exact simplification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to find a period is not by itself proof of aperiodicity; UNKNOWN is used when no aperiodicity theorem applies.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`symmetry`](symmetry.md)
- [`oscillation`](oscillation.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.structural_properties`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/structural_properties.py).
