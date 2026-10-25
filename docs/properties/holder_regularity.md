# Hölder regularity

`holder_regularity`

## Mathematical definition

A Hölder bound controls |f(x)-f(y)| by C|x-y|**alpha for a supported alpha in (0,1].

## API and return values

```text
holder_regularity(expr, variable, *, domain=Reals, work_budget=None, assumptions=True, return_result=False)
```

A certified exponent or None when unresolved. return_result=True gives HolderRegularityResult with exponent, constant, optimal, domain, source and evidence. optimal refers to the supported exponent claim, not a universal claim of the best constant.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

Use variable for the real scalar coordinate, domain for its support, and assumptions for parameter guards. The public API also accepts conditional expressions and return_result=True. Natural-domain restrictions and supported branch/seam rules remain relevant. A detailed evidence record is not automatically a registered replay certificate; inspect its concrete type and result contract.

## Executable examples

### Square-root cusp exponent

<!-- example-id: holder-square-root -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.holder_regularity(sp.sqrt(x), x, domain=sp.Interval(0, 1), return_result=True)
assert result.exponent == sp.Rational(1, 2) and result.constant == 1
```

Expected: exponent 1/2 with constant 1.

Application: Describe a continuous cusp where a Lipschitz bound is unavailable.

## Applications

Obtain a supported power-law continuity exponent near a cusp where a Lipschitz bound may fail.

## How funcprops proves it

Finite-domain Lipschitz implications, supported principal power cusps near zero and interval Lipschitz proofs.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Supported sufficient rules do not discover every possible Hölder exponent. The source domain and approach to a cusp must be established.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`lipschitz`](lipschitz.md)
- [`uniformly_continuous`](uniformly_continuous.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.regularity_extensions`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/regularity_extensions.py).
