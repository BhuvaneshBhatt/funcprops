# Zeros

`zeros`

## Mathematical definition

The zero set contains the domain points at which the expression is exactly zero.

## API and return values

```text
zeros(expr, variable, *, domain=True, allow_numerical=False, assumptions=True, return_result=False)
```

Usually a SymPy Set; return_result=True exposes structured/conditional information.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `allow_numerical` | Permit explicitly marked numerical zero information when exact analysis is unavailable. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Exact real zeros

<!-- example-id: zeros-polynomial -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.zeros((x - 1) * (x + 2), x)
assert result == sp.FiniteSet(-2, 1)
```

Expected: ``{-2, 1}``.

Application: Locate exact roots used for sign partitions and critical-event analysis.

## Applications

Locate candidate stationary points, source exclusions or intersections and retain whether the root description is exhaustive.

## How funcprops proves it

Exact algebraic solving, semialgebraic reduction, monotone partitions, structural special-function rules, and guarded parameter cases.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Infinite or transcendental zero sets may require structured representations, and numerical roots are opt-in and are not mixed with exact results.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`sign`](sign.md)
- [`oscillation`](oscillation.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.zeros`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/zeros.py).
