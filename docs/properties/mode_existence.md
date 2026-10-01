# Mode existence

`mode_existence`

## Mathematical definition

Mode-existence analysis certifies structural attainment of a global minimum or maximum on the requested domain.

## API and return values

```python
mode_existence(expr, variables, *, domain=Reals, sense='max', assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the attainment certificate and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Structural maximum existence

<!-- example-id: mode-gaussian-log-density -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.mode_existence(-x**2/2, x, sense='max')
result
```

Expected: a verified global-maximum existence certificate.

Application: Establish existence of a mode from continuity, closedness, and coercivity.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

A Weierstrass-style implication combines continuity, closedness, and level-boundedness; maxima are reduced to level-boundedness of the negated objective.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Failure to prove the structural hypotheses is reported as unresolved.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`level_boundedness`](level_boundedness.md)
- [`geometry`](geometry.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
