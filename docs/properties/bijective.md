# Bijectivity

`bijective`

## Mathematical definition

A function is bijective when it is both injective on its domain and surjective onto its codomain.

## API and return values

```text
bijective(expr, variable, *, domain=True, codomain=Reals, work_budget=None, assumptions=True, return_result=False)
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

### A real bijection

<!-- example-id: bijective-cubic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.bijective(x**3, x)
assert result is fp.TruthValue.TRUE
```

Expected: ``TruthValue.TRUE``.

Application: Certify existence of a globally single-valued inverse between two domains.

## Applications

Check both source uniqueness and target coverage before constructing an inverse.

## How funcprops proves it

Composition of certified injectivity and surjectivity with shared structural shortcuts.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

UNKNOWN from either component generally propagates unless an independent bijection theorem applies.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`injective`](injective.md)
- [`surjective`](surjective.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.mapping`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/mapping.py).
