# Injectivity

`injective`

## Mathematical definition

A function is injective when distinct domain points cannot have the same output.

## API and return values

```text
injective(expr, variable, *, domain=True, partition=None, work_budget=None, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the full `PropertyResult`.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `partition` | Optional precomputed monotonic partition for exact reuse. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Injective exponential

<!-- example-id: injective-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.injective(sp.exp(x), x)
assert result is fp.TruthValue.TRUE
```

Expected: ``TruthValue.TRUE``.

Application: Establish whether a symbolic inverse is single-valued on the chosen domain.

## Applications

Check whether an inverse can be single-valued on the requested source domain.

## How funcprops proves it

Strict monotonicity, symmetry/periodicity obstructions, affine/structural rules, shared partitions, and exact collision reasoning where available.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General multivariate and transcendental injectivity are difficult; UNKNOWN is preferred to a heuristic collision claim.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`surjective`](surjective.md)
- [`bijective`](bijective.md)
- [`monotonicity`](monotonicity.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.mapping`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/mapping.py).
