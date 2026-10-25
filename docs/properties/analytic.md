# Analyticity

`analytic`

## Mathematical definition

Analyticity certifies local representation by convergent power series throughout the requested domain.

## API and return values

```text
analytic(expr, variable, *, domain=Reals, assumptions=True, work_budget=None, return_result=False)
```

Analyticity.ANALYTIC, NOT_ANALYTIC, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the rich result and evidence.

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

### Entire real restriction

<!-- example-id: analytic-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.analytic(sp.exp(x), x)
assert result is fp.Analyticity.ANALYTIC
```

Expected: ``Analyticity.ANALYTIC``.

Application: Justify convergent local power-series methods and analytic continuation steps.

## Applications

Check branch and seam hypotheses for local analytic arguments or contour operations.

## How funcprops proves it

Singularity/branch analysis, analytic closure rules, piecewise interface checks, domain restrictions, and theorem-backed function facts.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Real analyticity is stricter than smoothness; unresolved branch or singularity structure can produce UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`smoothness`](smoothness.md)
- [`meromorphic`](meromorphic.md)
- [`singularities`](singularities.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.analysis`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/analysis.py).
