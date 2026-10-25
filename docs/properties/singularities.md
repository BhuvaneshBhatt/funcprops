# Singularities

`singularities`

## Mathematical definition

This query returns the Boolean locus where a function is singular: the disjunction of poles, removable and essential singularities, branch points and cuts, definition cuts, and discontinuities.

## API and return values

```text
singularities(expr, variable, domain=Complexes, *, assumptions=True, return_result=False)
```

A SymPy Boolean condition by default; return_result=True returns a SingularityResult with classified Boolean loci and supporting records.

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

### Boolean singularity locus

<!-- example-id: singularities-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.singularities(1 / x, x)
assert result == sp.Eq(x, 0)
```

Expected: the singular locus ``x = 0``.

Application: Obtain one composable Boolean locus for analytic obstructions before downstream analysis.

## Applications

Use the executable singularities examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Shared structural singularity traversal and branch analysis, followed by guard-aware locus union and ConditionalExpression restriction.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Use singularity_analysis when completeness and unknown function heads matter to a proof.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`singularity_analysis`](singularity_analysis.md)
- [`branch_cuts`](branch_cuts.md)
- [`poles`](poles.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
