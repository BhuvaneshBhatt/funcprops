# Range

`range`

## Mathematical definition

The range is the set of output values attained by the expression on the requested input constraints.

## API and return values

```text
range(expr, variable, y, *, constraints=True, domain=None, method='auto', partition=None, work_budget=None, assumptions=True, return_result=False, **kwargs)
```

A SymPy condition in the output symbol, possibly wrapped in a conditional PropertyResult for parameter strata.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `y` | Output symbol used to represent the range condition. |
| `constraints` | Input constraints used by range analysis. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `method` | Select the supported range-analysis strategy; ``auto`` chooses the normal proof cascade. |
| `partition` | Optional precomputed monotonic partition for exact reuse. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |
| `kwargs` | Operation-specific options, including supported budgets and native isolation policy/accuracy targets; see the linked guide. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Range on a restricted interval

<!-- example-id: range-restricted-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.range(x**2, x, y, constraints=sp.And(x >= -2, x <= 3))
assert sp.simplify(result ^ ((y >= 0) & (y <= 9))) is sp.false
```

Expected: ``(y >= 0) & (y <= 9)``.

Application: Derive certified output bounds for downstream constraints.

## Applications

Determine reachable outputs on a restricted interval and whether a requested target can be attained.

## How funcprops proves it

Semialgebraic elimination, monotone partitions, endpoint limits, extrema, structural special-function facts, and exact set reasoning.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

There is no general completeness guarantee for arbitrary transcendental inputs; unsupported cases remain unresolved.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`boundedness`](boundedness.md)
- [`surjective`](surjective.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.range`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/range.py).
