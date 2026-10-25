# Mode existence

`mode_existence`

## Mathematical definition

Mode-existence analysis certifies structural attainment of a global minimum or maximum on the requested domain.

## API and return values

```text
mode_existence(expr, variables, *, domain=Reals, sense='max', assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the attainment certificate and evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variables` | Independent symbol or ordered variable sequence for multivariate geometry. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `sense` | Optimization sense, either ``min`` or ``max`` for structural attainment analysis. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Structural maximum existence

<!-- example-id: mode-gaussian-log-density -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.mode_existence(-(x**2) / 2, x, sense="max")
assert result is fp.TruthValue.TRUE
```

Expected: a verified global-maximum existence certificate.

Application: Establish existence of a mode from continuity, closedness, and coercivity.

## Applications

Use the executable mode existence examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

A Weierstrass-style implication combines continuity, closedness, and level-boundedness; maxima are reduced to level-boundedness of the negated objective.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to prove the structural hypotheses is reported as unresolved.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`level_boundedness`](level_boundedness.md)
- [`geometry`](geometry.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.geometry`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/geometry.py).
