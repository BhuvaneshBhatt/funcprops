# Discontinuities

`discontinuities`

## Mathematical definition

Discontinuity analysis locates points or guarded loci where continuity fails.

## API and return values

```text
discontinuities(expr, variable, *, assumptions=True, return_result=False)
```

A Boolean discontinuity locus by default; return_result=True returns the supporting Singularity records.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query uses the natural source domain and the supplied assumptions. This API has no domain keyword. Parameter-dependent singularity or branch conditions remain explicit in the detailed result.

## Executable examples

### Jump discontinuity

<!-- example-id: discontinuities-piecewise -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
f = sp.Piecewise((0, x < 0), (1, True))
result = fp.discontinuities(f, x)
assert result == sp.Eq(x, 0)
```

Expected: a discontinuity at ``x = 0``.

Application: Split quadrature, plotting, and approximation domains at genuine discontinuities.

## Applications

Use the executable discontinuities examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Piecewise interface limits, denominator/domain failures, branch behavior, and structural singularity traversal.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

A false locus means no discontinuity was certified by the analysis, not necessarily a completeness theorem unless detailed singularity analysis is complete.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`continuous`](continuous.md)
- [`singularity_analysis`](singularity_analysis.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.records`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/records.py).
