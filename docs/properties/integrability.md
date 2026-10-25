# Integrability

`integrability`

## Mathematical definition

Integrability separates Riemann, local, absolute and improper integral notions on the declared domain.

## API and return values

```text
integrability(expr, variable, *, domain=Reals, work_budget=None, assumptions=True, return_result=False)
```

IntegrabilityResult in both compact and detailed modes, with independent riemann, locally_integrable, absolutely_integrable and improper_integrable TruthValue fields, optional integral/absolute_integral, domain, exceptional_loci and evidence.

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

### Separate integrability notions

<!-- example-id: integrability-compact-polynomial -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.integrability(x**2, x, domain=sp.Interval(-1, 1))
assert result.riemann is fp.TruthValue.TRUE and result.absolutely_integrable is fp.TruthValue.TRUE and result.integral == sp.Rational(2, 3)
```

Expected: Riemann and absolute integrability with integral 2/3.

Application: Check integral hypotheses without conflating local, absolute and improper convergence.

## Applications

Separate ordinary, local, absolute and improper integrability; a principal value does not establish the ordinary integral.

## How funcprops proves it

Continuity on compact intervals, supported source-domain checks and exact convergence/evaluation of symbolic integrals.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

A successful principal-value calculation is not a proof of ordinary improper integrability. Unresolved symbolic integrals retain UNKNOWN fields; different integrability notions must not be conflated.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`variation`](variation.md)
- [`continuous`](continuous.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.integrability`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/integrability.py).
