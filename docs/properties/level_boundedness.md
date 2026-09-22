# Level boundedness

`function_level_boundedness`

## Mathematical definition

A function is level-bounded when every sublevel set is bounded; on Euclidean spaces this is the coercivity notion used by the attainment machinery.

## API and return values

```python
function_level_boundedness(expr, variables, *, domain=Reals, return_result=False, assumptions=True)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the level-boundedness certificate and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Coercive quartic

<!-- example-id: level-bounded-quartic -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_level_boundedness(x**4 - x, x)
result
```

Expected: a verified level-boundedness certificate.

Application: Prove bounded sublevel sets without numerical optimization.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Bounded-domain closure, positive-infinity escape limits, strong convexity, and separable coercivity implications.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The proof engine uses sufficient structural implications and does not claim a complete decision procedure for general multivariate coercivity.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_boundary_behavior`](boundary_behavior.md)
- [`function_mode_existence`](mode_existence.md)
- [`function_geometry`](geometry.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
