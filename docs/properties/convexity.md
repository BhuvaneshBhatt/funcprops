# Convexity

`convexity`

## Mathematical definition

Convexity classifies ordinary, strict, strong, affine, concave, log-, quasi-, and pseudo-convex/concave behavior when certifiable.

## API and return values

```text
convexity(expr, variable, *, domain=True, strict_inequalities=True, all_properties=False, intervals=False, work_budget=None, assumptions=True, return_result=False, **kwargs)
```

A Convexity value or a SymPy Piecewise for parameter-dependent classifications; `return_result=True` preserves the full PropertyResult and normalized ConvexityCertificate.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `strict_inequalities` | Whether strict classifications are distinguished from their weak implications. |
| `all_properties` | Return the primary classification together with certified implied properties. |
| `intervals` | Request an interval decomposition. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |
| `kwargs` | Operation-specific options, including supported budgets and native isolation policy/accuracy targets; see the linked guide. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Strong convexity

<!-- example-id: convexity-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.convexity(x**2, x)
assert result is fp.Convexity.STRONGLY_CONVEX
```

Expected: ``Convexity.STRONGLY_CONVEX``.

Application: Guarantee uniqueness and conditioning properties in optimization models.

## Applications

Check sufficient hypotheses for optimization and separate strict, weak and unresolved curvature.

## How funcprops proves it

Second-derivative/Hessian inequalities, rational-box C2 diagonal-dominance bounds, semialgebraic certification, composition rules, strong-modulus bounds, Piecewise slope-interface checks, and theorem-backed facts.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Secondary notions are often certified by sufficient implications.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`sign`](sign.md)
- [`monotonicity`](monotonicity.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.convexity`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/convexity.py).
