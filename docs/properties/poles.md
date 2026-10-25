# Poles

`poles`

## Mathematical definition

Pole analysis identifies isolated singularities with finite negative local order and records multiplicity when known.

## API and return values

```text
poles(expr, variable, *, assumptions=True, return_result=False)
```

A list of (pole, multiplicity) pairs by default; return_result=True returns the supporting Singularity records.

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `variable` | Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |

## Domains, assumptions, and parameters

The query uses the natural source domain and the supplied assumptions. This API has no domain keyword. Parameter-dependent singularity or branch conditions remain explicit in the detailed result.

## Executable examples

### Simple pole

<!-- example-id: poles-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.poles(1 / x, x)
assert result == [(sp.Integer(0), 1)]
```

Expected: one simple pole at ``x = 0``.

Application: Locate poles for contour deformation, residues, and singular quadrature.

## Applications

Use the executable poles examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Local order, rational denominator structure, special-function singularity facts, and guarded parameter analysis.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Multiplicity can be unknown when local cancellation or parameter dependence cannot be resolved exactly.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`singularities`](singularities.md)
- [`meromorphic`](meromorphic.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.singularities.records`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/singularities/records.py).
