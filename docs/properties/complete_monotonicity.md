# Complete monotonicity

`function_complete_monotonicity`

## Mathematical definition

A function is completely monotone when all derivatives exist and (-1)^n f^(n)(x) is nonnegative for every nonnegative integer n on the requested domain.

## API and return values

```python
function_complete_monotonicity(expr, var, *, domain=Reals, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN; return_result=True exposes a CompleteMonotonicityCertificate when a theorem-backed proof is available.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Mittag-Leffler complete monotonicity

<!-- example-id: complete-monotonicity-mittag-leffler -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
alpha = sp.symbols('alpha', positive=True); t = sp.symbols('t', nonnegative=True); result = fp.function_complete_monotonicity(fp.MittagLefflerE(alpha, -t), t, domain=t >= 0, assumptions=alpha <= 1)
result
```

Expected: ``TruthValue.TRUE`` for ``0 < alpha <= 1``.

Application: Certify Laplace-transform and survival-kernel structure in fractional probability models.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Theorem-backed families, structural exponential kernels, parameter guards, and exact domain implication rather than finite derivative sampling.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

The implementation certifies supported sufficient theorem families; absence of a matching theorem yields UNKNOWN rather than testing finitely many derivatives.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_monotonicity`](monotonicity.md)
- [`function_convexity`](convexity.md)
- [`function_sign`](sign.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
