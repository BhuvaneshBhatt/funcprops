# Determinant nonvanishing

`determinant_nonvanishing`

## Mathematical definition

For a square real C1 map, determinant nonvanishing asks whether det J is nonzero everywhere on the requested domain.

## API and return values

```text
determinant_nonvanishing(expressions, variables, *, domain=Reals, assumptions=True, return_result=False, work_budget=None)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the determinant-nonvanishing certificate and evidence.

| Parameter | Meaning |
| --- | --- |
| `expressions` | Ordered expression sequence defining a coordinate transformation. |
| `variables` | Independent symbol or ordered variable sequence for multivariate geometry. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |

## Domains, assumptions, and parameters

The original map must be defined and C1 throughout nonempty, resolved real input support. Coordinate assumptions, raw source exclusions and parameter hypotheses remain premises. Empty or unresolved support and unproved regularity return UNKNOWN.

## Executable examples

### Nonvanishing Jacobian determinant

<!-- example-id: determinant-nonvanishing-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.determinant_nonvanishing((2 * x + y, x - y), (x, y))
assert result is fp.TruthValue.TRUE
```

Expected: a verified nonvanishing determinant ``-3``.

Application: Check the inverse-function-theorem rank hypothesis on an entire domain.

## Applications

Use the executable determinant nonvanishing examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Source-bound domain and C1 checks, exact Jacobian reconstruction, assumptions and semialgebraic zero-set decisions. An inconclusive backend cannot establish exclusion.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Nonsquare maps and determinant zero sets outside the supported symbolic/semialgebraic proof routes remain UNKNOWN unless a witness or theorem is available.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`jacobian`](jacobian.md)
- [`local_invertibility`](local_invertibility.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
