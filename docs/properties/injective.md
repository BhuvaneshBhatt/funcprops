# Injectivity

`injective`

## Mathematical definition

A function is injective when distinct domain points cannot have the same output.

## API and return values

```python
injective(expr, variable, *, domain=True, partition=None, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN. Parameter-stratified results are returned as a SymPy `Piecewise` by default; `return_result=True` preserves the full `PropertyResult`.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Injective exponential

<!-- example-id: injective-exponential -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.injective(sp.exp(x), x)
result
```

Expected: ``TruthValue.TRUE``.

Application: Establish whether a symbolic inverse is single-valued on the chosen domain.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Strict monotonicity, symmetry/periodicity obstructions, affine/structural rules, shared partitions, and exact collision reasoning where available.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General multivariate and transcendental injectivity are difficult; UNKNOWN is preferred to a heuristic collision claim.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`surjective`](surjective.md)
- [`bijective`](bijective.md)
- [`monotonicity`](monotonicity.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
