# Sign

`function_sign`

## Mathematical definition

Sign classification determines whether an expression is positive, nonnegative, zero, nonpositive, negative, or sign-changing throughout a domain.

## API and return values

```python
function_sign(expr, var=None, *, domain=True, strict_inequalities=True, all_properties=False, assumptions=True)
```

A Sign value or PropertyResult containing guarded parameter cases and implied weaker sign classes.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Strict positivity

<!-- example-id: sign-positive -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_sign(x**2 + 1, x)
result
```

Expected: ``Sign.POSITIVE``.

Application: Prove denominator positivity or inequality preconditions without sampling.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Structural sign rules, exact inequality proving, semialgebraic certification, zero geometry, special-function facts, and parameter stratification.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

A result of UNKNOWN means the available proof engines could not certify a uniform sign; it does not mean the sign is arbitrary.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_zeros`](zeros.md)
- [`function_monotonicity`](monotonicity.md)
- [`function_convexity`](convexity.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
