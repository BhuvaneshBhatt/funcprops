# Oscillation

`oscillation`

## Mathematical definition

Oscillation distinguishes persistent oscillation, finite oscillatory behavior, and nonoscillatory behavior on the selected domain.

## API and return values

```text
oscillation(expr, variable, *, domain=True, partition=None, assumptions=True, return_result=False)
```

An Oscillation classification by default; return_result=True exposes supporting partitions and evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `partition` | Optional precomputed monotonic partition for exact reuse. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

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
assert result is fp.Oscillation.OSCILLATORY
```

Expected: ``Oscillation.OSCILLATORY``.

Application: Detect repeated sign/turning behavior relevant to asymptotics and root searches.

## Applications

Distinguish finite turning behavior from supported infinite oscillation without treating samples as a global theorem.

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

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.oscillation`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/oscillation.py).
