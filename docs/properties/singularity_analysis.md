# Singularity analysis

`singularity_analysis`

## Mathematical definition

Detailed singularity analysis reports analytic obstructions together with completeness and unresolved-head information.

## API and return values

```text
singularity_analysis(expr, variable, *, domain=Complexes, assumptions=True, ignore_unknown=False, return_result=False)
```

A SingularityAnalysis object containing singularity groups, domain exterior, completeness, unknown heads, and provenance.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `ignore_unknown` | Allow detailed singularity analysis to omit unresolved primitive heads from completeness checks. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Detailed singularity analysis

<!-- example-id: singularity-analysis-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.singularity_analysis(1 / x, x)
assert result.complete is True and len(result.poles) == 1 and result.unknown_heads == ()
```

Expected: a complete analysis with one pole.

Application: Inspect completeness and provenance when a downstream proof requires certified singularity coverage.

## Applications

Use the executable singularity analysis examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Structural traversal, local singularity classification, branch analysis, discontinuity analysis, and domain comparison.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

complete=False is an explicit warning that the returned inventory is not exhaustive.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`singularities`](singularities.md)
- [`discontinuities`](discontinuities.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.analysis`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/analysis.py).
