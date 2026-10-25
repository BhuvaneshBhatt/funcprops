# Uniform continuity

`uniformly_continuous`

## Mathematical definition

Uniform continuity requires one input-distance bound for every pair of domain points at a given output tolerance.

## API and return values

```text
uniformly_continuous(expr, variable, *, domain=Reals, work_budget=None, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE or UNKNOWN; return_result=True exposes a DetailedPropertyResult.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

Use variable for the real scalar coordinate, domain for its support, and assumptions for parameter guards. The public API also accepts conditional expressions and return_result=True. Natural-domain restrictions and supported branch/seam rules remain relevant. A detailed evidence record is not automatically a registered replay certificate; inspect its concrete type and result contract.

## Executable examples

### Compact-domain uniform continuity

<!-- example-id: uniform-compact -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.uniformly_continuous(x**2, x, domain=sp.Interval(-1, 1))
assert result is fp.TruthValue.TRUE and fp.uniformly_continuous(x**2, x) is fp.TruthValue.FALSE
```

Expected: TRUE on [-1, 1], while the same polynomial is not uniformly continuous on R.

Application: Choose a globally valid error tolerance on an explicitly bounded input region.

## Applications

Check whether one continuity tolerance can control every pair in a noncompact or restricted domain.

## How funcprops proves it

Finite domains, continuity on compact domains, Lipschitz implications and guarded nonlinear-polynomial obstructions on the whole real line.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to prove a Lipschitz constant does not disprove uniform continuity. Unsupported domains and unresolved continuity remain UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`lipschitz`](lipschitz.md)
- [`continuous`](continuous.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.regularity_extensions`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/regularity_extensions.py).
