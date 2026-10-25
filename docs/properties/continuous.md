# Continuity

`continuous`

## Mathematical definition

Continuity certifies that the function has no value/limit mismatch at points of the requested domain.

## API and return values

```text
continuous(expr, variable, *, domain=Reals, assumptions=True, work_budget=None, return_result=False)
```

Continuity.CONTINUOUS, DISCONTINUOUS, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the rich result and evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Continuous but nonsmooth

<!-- example-id: continuous-absolute -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.continuous(sp.Abs(x), x)
assert result is fp.Continuity.CONTINUOUS
```

Expected: ``Continuity.CONTINUOUS``.

Application: Verify hypotheses of existence theorems and interval methods.

## Applications

Check source holes, branch cuts and Piecewise seams before using interval theorems.

## How funcprops proves it

Structural closure, one-sided interface limits for Piecewise expressions, singularity analysis, and domain restriction.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Complicated limit problems can remain UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`discontinuities`](discontinuities.md)
- [`differentiability`](differentiability.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.analysis`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/analysis.py).
