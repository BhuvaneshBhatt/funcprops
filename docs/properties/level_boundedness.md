# Level boundedness

`level_boundedness`

## Mathematical definition

A function is level-bounded when every sublevel set is bounded; on Euclidean spaces this is the coercivity notion used by the attainment machinery.

## API and return values

```text
level_boundedness(expr, variables, *, domain=Reals, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the level-boundedness certificate and evidence.

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

### Coercive quartic

<!-- example-id: level-bounded-quartic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.level_boundedness(x**4 - x, x)
assert result is fp.TruthValue.TRUE
```

Expected: a verified level-boundedness certificate.

Application: Prove bounded sublevel sets without numerical optimization.

## Applications

Use the executable level boundedness examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Bounded-domain closure, positive-infinity escape limits, strong convexity, and separable coercivity implications.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The proof engine uses sufficient structural implications and does not claim a complete decision procedure for general multivariate coercivity.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`boundary_behavior`](boundary_behavior.md)
- [`mode_existence`](mode_existence.md)
- [`geometry`](geometry.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.geometry`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).
