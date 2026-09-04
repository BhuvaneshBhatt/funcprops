# Domain

`function_domain`

## Mathematical definition

The domain is the set of input values for which the expression is defined under the selected real-domain convention.

## API and return values

```python
function_domain(expr, var, *, domain=Reals, stratified=False)
```

A SymPy logical condition, or a stratified result when parameter cases must be separated.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Radical with an excluded pole

<!-- example-id: domain-radical-pole -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_domain(sp.sqrt(x - 1) / (x - 2), x)
result
```

Expected: ``(x >= 1) & Ne(x, 2)``.

Application: Validate the admissible input region before symbolic optimization or plotting.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Expression-domain rules, algebraic constraints, radical/logarithm restrictions, denominator exclusions, and exact semialgebraic reduction.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Complicated transcendental preimages and unresolved parameter relations can prevent a fully simplified condition.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_continuous`](continuous.md)
- [`function_singularities`](singularities.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
