# Branch points

`branch_points`

## Mathematical definition

Branch-point analysis identifies points around which analytic continuation can change the value of a multivalued function.

## API and return values

```text
branch_points(expr, variable, *, assumptions=True, return_result=False)
```

A Boolean branch-point locus by default; return_result=True returns the supporting Singularity records.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query uses the natural source domain and the supplied assumptions. This API has no domain keyword. Parameter-dependent singularity or branch conditions remain explicit in the detailed result.

## Executable examples

### Logarithmic branch point

<!-- example-id: branchpoints-log -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.branch_points(sp.log(x), x)
assert result == sp.Eq(x, 0)
```

Expected: a branch point at ``x = 0``.

Application: Identify non-isolated analytic structure relevant to continuation and contour choices.

## Applications

Use the executable branch points examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Known principal-branch structure, compositional preimages, algebraic/logarithmic branch rules, and assumptions.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General nested transcendental preimages can be difficult to reduce to a simple exact locus.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`branch_cuts`](branch_cuts.md)
- [`singularities`](singularities.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.records`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/records.py).
