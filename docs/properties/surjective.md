# Surjectivity

`surjective`

## Mathematical definition

A function is surjective onto a codomain when every codomain value is attained by some domain point.

## API and return values

```text
surjective(expr, variable, *, domain=True, codomain=Reals, work_budget=None, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the full `PropertyResult`.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `codomain` | Target set for surjectivity or bijectivity. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### A surjection onto the reals

<!-- example-id: surjective-cubic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.surjective(x**3, x)
assert result is fp.TruthValue.TRUE
```

Expected: ``TruthValue.TRUE``.

Application: Verify that every target value in a codomain is attainable.

## Applications

Determine whether the requested codomain is reached, separately from source injectivity.

## How funcprops proves it

Exact range comparison, structural mappings, monotone/range closure, and parameter stratification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The answer depends on both domain and codomain; an omitted or unsuitable codomain can change the mathematical question.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`range`](range.md)
- [`bijective`](bijective.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.mapping`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/mapping.py).
