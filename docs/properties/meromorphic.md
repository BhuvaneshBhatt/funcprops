# Meromorphicity

`meromorphic`

## Mathematical definition

A meromorphic function is analytic except for isolated poles on the domain under consideration.

## API and return values

```text
meromorphic(expr, variable, *, assumptions=True, work_budget=None, return_result=False)
```

Meromorphicity.MEROMORPHIC, NOT_MEROMORPHIC, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the rich result and evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query uses the natural source domain and the supplied assumptions. This API has no domain keyword. Parameter-dependent singularity or branch conditions remain explicit in the detailed result.

## Executable examples

### Rational meromorphic function

<!-- example-id: meromorphic-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.meromorphic(1 / x, x)
assert result is fp.Meromorphicity.MEROMORPHIC
```

Expected: ``Meromorphicity.MEROMORPHIC``.

Application: Determine whether residue and pole-based complex_analysis techniques apply.

## Applications

Check whether isolated-pole methods can apply on a requested complex region.

## How funcprops proves it

Structural singularity traversal, branch-point/cut exclusion, pole classification, and known meromorphic closure rules.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Natural boundaries, unresolved singularity heads, or branch structure may prevent a complete classification.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`poles`](poles.md)
- [`singularity_analysis`](singularity_analysis.md)
- [`analytic`](analytic.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.regularity`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/regularity.py).
