# Determinant nonvanishing

`determinant_nonvanishing`

## Mathematical definition

For a square coordinate map, determinant nonvanishing asks whether det J is nonzero everywhere on the requested domain.

## API and return values

```python
determinant_nonvanishing(expressions, variables, *, domain=Reals, assumptions=True, return_result=False)
```

TruthValue.TRUE, FALSE, or UNKNOWN by default; return_result=True returns the determinant-nonvanishing certificate and evidence.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Nonvanishing Jacobian determinant

<!-- example-id: determinant-nonvanishing-affine -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.determinant_nonvanishing((2*x + y, x - y), (x, y))
result
```

Expected: a verified nonvanishing determinant ``-3``.

Application: Check the inverse-function-theorem rank hypothesis on an entire domain.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact, not isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Exact determinant simplification, assumptions, sign/nonzero reasoning, and semialgebraic zero-set certification where applicable.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Nonsquare maps and determinant zero sets outside the supported symbolic/semialgebraic proof routes remain UNKNOWN unless a witness or theorem is available.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`jacobian`](jacobian.md)
- [`local_invertibility`](local_invertibility.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
