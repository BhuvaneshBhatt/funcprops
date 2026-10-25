# Function geometry

`geometry`

## Mathematical definition

Function geometry combines regularity, analyticity, convexity, singularities, boundary escape, level-boundedness, and attainment information in one structural summary.

## API and return values

```text
geometry(expr, variables, *, domain=Reals, assumptions=True, return_result=False)
```

A FunctionGeometry object containing the component property results and certificates.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variables` | Independent symbol or ordered variable sequence for multivariate geometry. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Combined function geometry

<!-- example-id: geometry-quadratic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.geometry(x**2, x)
assert result.c2 is fp.TruthValue.TRUE and result.minimum_exists.exists is True
```

Expected: a combined regularity, singularity, convexity, and attainment summary.

Application: Collect structural facts for optimization and probability workflows in one query.

## Applications

Use the executable function geometry examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Delegation to the regularity, singularity, convexity, boundary-behavior, level-boundedness, and mode-existence engines with shared assumptions and domains.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The summary is only as complete as its component proof engines; unresolved component properties remain explicitly unresolved.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`convexity`](convexity.md)
- [`singularities`](singularities.md)
- [`mode_existence`](mode_existence.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.geometry`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).
