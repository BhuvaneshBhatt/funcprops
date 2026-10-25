# Complex zeros

`complex_zeros`

## Mathematical definition

Complex-zero isolation finds and certifies zeros inside a finite complex rectangle.

## API and return values

```text
complex_zeros(expr, *args, assumptions=True, return_result=False, **kwargs)
```

An exact finite set when available, or a ComplexRootIsolationResult containing certified rectangles, counts, and route-specific evidence. Native entire/quotient routes use complete = coverage_complete and isolation_complete and accuracy_complete. Algebraic/exact routes have their own contracts; consult [result contracts](../reference/result-contracts.md). Counts distinguish source zeros, extension zeros and poles. Request rectangle=(lower_left, upper_right), an EnclosurePolicy, and positive max_box_width/max_box_diameter targets when needed; see the [isolation tutorial](../tutorials/complex-isolation.md).

| Parameter | Meaning |
| --- | --- |
| `expr` | SymPy expression whose global property is queried. |
| `args` | Positional coordinate and rectangle forms accepted by this wrapper; prefer the explicit tutorial call. |
| `assumptions` | Symbolic hypotheses used while proving the property. |
| `return_result` | Return structured metadata, certificates, or diagnostics. |
| `kwargs` | Operation-specific options, including supported budgets and native isolation policy/accuracy targets; see the linked guide. |

## Domains, assumptions, and parameters

Native entire/quotient isolation requires an unconstrained Symbol, rational rectangle corners, no free parameters and zero-free outer boundaries for the required source components. Boundary zeros remain unresolved there. The algebraic adapter can own exact boundary roots and retains raw source holes, principal-power branches, supported exact set domains and algebraic Eq/Ne guards. Unsupported planar guards, free parameters, branch or membership uncertainty prevent an unconditional completion claim. See [result contracts](../reference/result-contracts.md).

## Executable examples

### Certified complex zero in a rectangle

<!-- example-id: complex-zeros-exp -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
z = sp.symbols("z")
result = fp.complex_zeros(
    sp.exp(z) - 1, z, rectangle=(-1 - sp.I, 1 + sp.I), return_result=True
)
assert result.complete is True and result.total_count == 1 and len(result.rectangles) == 1
```

Expected: one certified zero in the rectangle.

Application: Certify contour root counts before complex continuation, inversion, or spectral calculations.

## Applications

Use the executable complex zeros examples to check the corresponding source, domain and branch premises before consuming the result in a larger analysis.

## How funcprops proves it

Algebraic inputs use the algroots adapter when supported. Native entire and certified-quotient inputs use replayable contour counts, exact rectangle covers, shared-zero/order witnesses and optional Newton refinement. Original source restrictions survive cancellation.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

General holomorphy and boundary nonvanishing may remain uncertified; numerical winding estimates never upgrade an incomplete result to a proof.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`zeros`](zeros.md)
- [`analytic`](analytic.md)

## Source

The callable is exported through funcprops; its implementation module is [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
