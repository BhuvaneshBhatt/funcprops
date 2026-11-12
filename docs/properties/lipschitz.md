# Lipschitz continuity

`lipschitz`

## Mathematical definition

A Lipschitz bound L controls |f(x)-f(y)| <= L|x-y| for all pairs of source-defined points in the requested domain.

## API and return values

```text
lipschitz(expr, variable, *, domain=Reals, work_budget=None, assumptions=True, return_result=False)
```

A certified constant when available, otherwise a TruthValue. return_result=True returns LipschitzResult with value, constant, optimal, domain, source, evidence and optional proof. Finite-domain results expose standalone verify(), complete, certified and source-binding fields. Other routes can give proved values without standalone replay. Affine interval constants are optimal when the real affine premises hold.

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

### Exact finite-domain Lipschitz constant

<!-- example-id: lipschitz-finite-optimum -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.lipschitz(x**2, x, domain=sp.FiniteSet(0, 1, 2), return_result=True)
assert result.constant == 3 and result.value is fp.TruthValue.TRUE and result.optimal is fp.TruthValue.TRUE and result.verify()
```

Expected: the optimal constant 3 on {0, 1, 2}.

Application: Bound distances in a finite sample without assuming its ambient interval is the domain.

## Applications

Certify a global distance bound on an interval or an exact finite source set, and inspect its optimality separately from replay support.

## How funcprops proves it

Exact finite-domain secant maxima, constant functions, continuity obstructions and sufficient derivative bounds on intervals.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Disconnected domains cannot inherit a global pairwise bound merely from derivative bounds on their separate components. Symbolic point collisions and unresolved bounds remain UNKNOWN.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`uniformly_continuous`](uniformly_continuous.md)
- [`holder_regularity`](holder_regularity.md)
- [`variation`](variation.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.regularity_extensions`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/regularity_extensions.py).
