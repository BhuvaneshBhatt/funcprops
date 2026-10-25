# Monotonicity

`monotonicity`

## Mathematical definition

Monotonicity classifies a function as strictly increasing/decreasing, weakly monotone, constant, non-monotone, or unknown on a domain.

## API and return values

```text
monotonicity(expr, variable, *, domain=True, strict_inequalities=True, all_properties=False, intervals=False, partition=None, work_budget=None, assumptions=True, return_result=False)
```

A Monotonicity value, a SymPy Piecewise for parameter-dependent classifications, or an interval decomposition when requested; `return_result=True` preserves the full PropertyResult when one is produced.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `strict_inequalities` | Whether strict classifications are distinguished from their weak implications. |
| `all_properties` | Return the primary classification together with certified implied properties. |
| `intervals` | Request an interval decomposition. |
| `partition` | Optional precomputed monotonic partition for exact reuse. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Strict increase

<!-- example-id: monotonicity-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.monotonicity(sp.exp(x), x)
assert result is fp.Monotonicity.STRICTLY_INCREASING
```

Expected: ``Monotonicity.STRICTLY_INCREASING``.

Application: Certify uniqueness of inverse values and one-dimensional optimization behavior.

## Applications

Justify ordered search or inverse uniqueness while retaining branch jumps and disconnected-domain seams.

## How funcprops proves it

Derivative-sign certification, shared monotone partitions, structural composition rules, theorem-backed special functions, piecewise interface checks, and parameter strata.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Disconnected domains and functions with many turning points may require interval output.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`sign`](sign.md)
- [`injective`](injective.md)
- [`range`](range.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.monotonicity`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/monotonicity.py).
