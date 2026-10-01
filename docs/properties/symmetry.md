# Symmetry

`symmetry`

## Mathematical definition

Symmetry detects even, odd, both, central, neither, or unresolved symmetry relative to a chosen center.

## API and return values

```python
symmetry(expr, variable, *, center=0, domain=True, assumptions=True, return_result=False)
```

A Symmetry value by default; return_result=True exposes center and evidence.

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
result
```

Expected: ``Symmetry.EVEN``.

Application: Cut numerical or symbolic work in half on symmetric domains.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

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

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
