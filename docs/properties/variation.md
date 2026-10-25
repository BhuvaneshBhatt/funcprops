# Total variation

`variation`

## Mathematical definition

Total variation is the supremum of sums of absolute increments along ordered finite partitions of the requested real interval.

## API and return values

```text
variation(expr, variable, *, domain=Reals, work_budget=None, assumptions=True, return_result=False)
```

A certified total variation, oo when proved infinite, or None when unresolved. return_result=True returns VariationResult with bounded_variation, total_variation, domain, source, evidence and optional proof. Supported finite motion/jump proofs expose verify(), complete, certified and source binding. Other variation routes can have no standalone replay proof.

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

### Both jumps of a singleton spike

<!-- example-id: variation-singleton-spike -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
spike = sp.Piecewise((10, sp.Eq(x, 0)), (0, True))
result = fp.variation(spike, x, domain=sp.Interval(-1, 1), return_result=True)
assert result.total_variation == 20 and result.bounded_variation is fp.TruthValue.TRUE and result.verify()
```

Expected: total variation 20, counting both incident jumps.

Application: Retain isolated function values when assembling Piecewise variation.

## Applications

Measure all monotone motion and owned jumps before invoking bounded-variation integration results.

## How funcprops proves it

Supported monotone/smooth interval rules and exact Piecewise branch motion, one-sided jumps and owned singleton values.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Arbitrary branch/seam limits and unsupported domain geometry can remain unresolved. A singleton spike contributes both incident jumps when both sides belong to the interval.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`monotonicity`](monotonicity.md)
- [`integrability`](integrability.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.variation`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/variation.py).
