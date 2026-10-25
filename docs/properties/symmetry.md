# Symmetry

`symmetry`

## Mathematical definition

Symmetry detects even, odd, both, central, neither, or unresolved symmetry relative to a chosen center.

## API and return values

```text
symmetry(expr, variable, *, center=0, domain=True, assumptions=True, return_result=False)
```

A Symmetry value by default; return_result=True exposes center and evidence.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `center` | Reflection or central-symmetry center; supported discovery modes may infer it. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Even symmetry

<!-- example-id: symmetry-cosine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.symmetry(sp.cos(x), x)
assert result is fp.Symmetry.EVEN
```

Expected: ``Symmetry.EVEN``.

Application: Cut numerical or symbolic work in half on symmetric domains.

## Applications

Reduce paired domain calculations while retaining the required reflection or central-symmetry support.

## How funcprops proves it

Exact substitutions around the center, structural identities, domain compatibility, and simplification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Symbolic equivalence that SymPy cannot prove can leave symmetry UNKNOWN even when the identity is mathematically true.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`periodicity`](periodicity.md)
- [`injective`](injective.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.structural_properties`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/structural_properties.py).
