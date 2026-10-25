# Smoothness

`smoothness`

## Mathematical definition

Smoothness records continuity, the certified differentiability order, C-infinity status, analyticity, and exceptional loci.

## API and return values

```text
smoothness(expr, variable, *, domain=True, max_order=6, work_budget=None, assumptions=True, return_result=False)
```

A SmoothnessResult with regularity fields and evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `max_order` | Maximum finite derivative order tried when no structural smoothness proof is available. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Smooth entire function

<!-- example-id: smoothness-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.smoothness(sp.exp(x), x)
assert result is sp.oo
```

Expected: ``oo`` (C-infinity).

Application: Verify regularity assumptions required by approximation and differential methods.

## Applications

Establish the supported derivative order needed for Taylor bounds or local approximation.

## How funcprops proves it

Analytic-implies-smooth closure, structural regularity rules, branch/interface checks, and bounded derivative-order certification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Finite-order search can understate differentiability when no structural C-infinity proof is available.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`differentiability`](differentiability.md)
- [`analytic`](analytic.md)
- [`continuous`](continuous.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.smoothness`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/smoothness.py).
