# Branch cuts

`branch_cuts`

## Mathematical definition

Branch-cut analysis returns the cuts used to make the selected principal branches single-valued.

## API and return values

```text
branch_cuts(expr, variable, *, assumptions=True, mode='conditions', return_result=False)
```

By default a tuple of logical cut conditions; alternate modes expose other supported representations.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `mode` | Select the supported branch-cut output representation. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query uses the natural source domain and the supplied assumptions. This API has no domain keyword. Parameter-dependent singularity or branch conditions remain explicit in the detailed result.

## Executable examples

### Principal logarithm cut

<!-- example-id: branchcuts-log -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.branch_cuts(sp.log(x), x)
assert result == (x < 0,)
```

Expected: ``(x < 0,)``.

Application: Avoid crossing branch cuts in symbolic transformations and complex numerical paths.

## Applications

Use the executable branch cuts examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Principal-branch registry facts, compositional preimages, algebraic transformation, simplification under assumptions, and cut normalization.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Branch cuts are representation/convention dependent; they are not intrinsic singularities of the underlying multivalued analytic object.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`branch_points`](branch_points.md)
- [`singularity_analysis`](singularity_analysis.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
