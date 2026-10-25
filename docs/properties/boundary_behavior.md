# Boundary behavior

`boundary_behavior`

## Mathematical definition

Boundary behavior records certified limits at unbounded real-domain escape directions relevant to global geometry.

## API and return values

```text
boundary_behavior(expr, variable, *, domain=Reals, assumptions=True, return_result=False)
```

A BoundaryBehavior summary containing the analyzed domain, certified BoundaryLimit records, completeness, and provenance.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Quadratic escape limits

<!-- example-id: boundary-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.boundary_behavior(x**2, x)
assert result.complete is True and all(item.value is sp.oo for item in result.limits)
```

Expected: both real escape limits are ``+oo``.

Application: Certify endpoint escape behavior before coercivity or attainment reasoning.

## Applications

Use the executable boundary behavior examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Exact symbolic one-sided limits at real escape boundaries, while unsupported multivariate radial escape geometry remains unresolved.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General multivariate escape directions are not exhaustively classified; an incomplete result explicitly preserves that limitation.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`level_boundedness`](level_boundedness.md)
- [`geometry`](geometry.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.geometry`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).
