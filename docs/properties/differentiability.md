# Differentiability

`differentiability`

## Mathematical definition

Differentiability asks whether derivatives exist throughout a domain, optionally through a requested finite order.

## API and return values

```text
differentiability(expr, variable, *, domain=True, order=None, all_properties=False, max_order=6, work_budget=None, assumptions=True, return_result=False)
```

A Differentiability value or a SymPy Piecewise for parameter-dependent classifications; `return_result=True` preserves the full PropertyResult with regularity evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `order` | Requested differentiability order; omitted means the strongest certified regularity class. |
| `all_properties` | Return the primary classification together with certified implied properties. |
| `max_order` | Maximum finite derivative order tried when no structural smoothness proof is available. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### A corner at the origin

<!-- example-id: differentiability-absolute -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.differentiability(sp.Abs(x), x)
assert result is fp.Differentiability.NOT_DIFFERENTIABLE
```

Expected: ``Differentiability.NOT_DIFFERENTIABLE``.

Application: Check whether derivative-based solvers are valid on an entire domain.

## Applications

Determine whether a derivative-based argument is valid through every active seam in the requested domain.

## How funcprops proves it

The smoothness engine, domain-aware exceptional-locus analysis, analytic closure rules, and certified finite-order derivative checks.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The bounded max_order search is a certification limit, not a claim that higher derivatives fail to exist.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`smoothness`](smoothness.md)
- [`continuous`](continuous.md)
- [`analytic`](analytic.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.differentiability`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/differentiability.py).
