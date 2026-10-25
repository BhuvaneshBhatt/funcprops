# Domain

`domain`

## Mathematical definition

The domain is the set of input values for which the expression is defined under the selected real-domain convention.

## API and return values

```text
domain(expr, variable, *, domain=Reals, stratified=False, work_budget=None, assumptions=True, return_result=False)
```

A SymPy logical condition, or a stratified result when parameter cases must be separated.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `domain` | Input domain or logical condition. The default depends on the property family. |
| `stratified` | Preserve supported guarded parameter-domain cases. |
| `work_budget` | Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain, not from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Radical with an excluded pole

<!-- example-id: domain-radical-pole -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.domain(sp.sqrt(x - 1) / (x - 2), x)
assert sp.simplify(result ^ ((x >= 1) & sp.Ne(x, 2))) is sp.false
```

Expected: ``(x >= 1) & Ne(x, 2)``.

Application: Validate the admissible input region before symbolic optimization or plotting.

## Applications

Check where a later optimization, integration or inverse query is defined before simplifying its source.

## How funcprops proves it

Expression-domain rules, algebraic constraints, radical/logarithm restrictions, denominator exclusions, and exact semialgebraic reduction.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Complicated transcendental preimages and unresolved parameter relations can prevent a fully simplified condition.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`continuous`](continuous.md)
- [`singularities`](singularities.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.real_analysis.domain`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/real_analysis/domain.py).
