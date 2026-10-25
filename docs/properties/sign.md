# Sign

`sign`

## Mathematical definition

Sign classification determines whether an expression is positive, nonnegative, zero, nonpositive, negative, or sign-changing throughout a domain.

## API and return values

```text
sign(expr, variable=None, *, domain=True, strict_inequalities=True, all_properties=False, work_budget=None, assumptions=True, return_result=False)
```

A Sign value or a SymPy Piecewise for guarded parameter cases; `return_result=True` preserves the full PropertyResult, evidence, and implied weaker sign classes.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `strict_inequalities` | Whether strict classifications are distinguished from their weak implications. |
| `all_properties` | Return the primary classification together with certified implied properties. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Strict positivity

<!-- example-id: sign-positive -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.sign(x**2 + 1, x)
assert result is fp.Sign.POSITIVE
```

Expected: ``Sign.POSITIVE``.

Application: Prove denominator positivity or inequality preconditions without sampling.

## Applications

Prove an inequality under explicit input restrictions, or select regions on which a denominator stays nonzero.

## How funcprops proves it

Bounded rational Sturm sign charts, guarded monotone threshold comparisons, exact central trigonometric charts, structural closure, registry facts and general certified fallbacks.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

A result of UNKNOWN means the available proof engines could not certify a uniform sign; it does not mean the sign is arbitrary.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`zeros`](zeros.md)
- [`monotonicity`](monotonicity.md)
- [`convexity`](convexity.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.sign`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/sign.py).
