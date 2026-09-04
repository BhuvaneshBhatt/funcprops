# Complex zeros

`function_complex_zeros`

## Mathematical definition

For a closed axis-aligned rectangle in the complex plane, the query returns the zeros of a univariate complex function that lie in that rectangle. Root counts from the argument principle count multiplicity. A certified one-root rectangle therefore contains exactly one simple zero; a certified rectangle with count greater than one represents either a multiple root or an unresolved cluster with that total multiplicity.

## API and return values

```python
function_complex_zeros(
    expr,
    var,
    *,
    rectangle,
    return_result=False,
    precision=60,
    max_boundary_depth=14,
    max_isolation_depth=10,
)
```

When exact finite roots are available, the default call returns a SymPy `FiniteSet`. A certified empty rectangle returns `EmptySet`. Otherwise it returns a `ComplexRootIsolationResult` so isolating rectangles and their mathematical root counts are not discarded. `return_result=True` always preserves the structured result and certificates.

## Domains, assumptions, and parameters

`rectangle=(a, b)` denotes the closed axis-aligned rectangle whose opposite corners are `a` and `b`. The current certified argument-principle backend requires exact real rectangle bounds and a proof that the principal-branch expression is holomorphic on the closed rectangle. Parameter-dependent or unresolved branch geometry is not guessed.

## Executable examples

### Certified complex zero in a rectangle

<!-- example-id: complex-zeros-exp -->

```python
import sympy as sp
import funcprops as fp

z = sp.symbols("z")
result = fp.function_complex_zeros(
    sp.exp(z) - 1,
    z,
    rectangle=(-1 - sp.I, 1 + sp.I),
    return_result=True,
)
result.total_count
```

Expected: one certified zero in the rectangle.

Application: Certify contour root counts before complex continuation, inversion, or spectral calculations.

## Applications

Complex root isolation is useful for contour methods, stability and spectral calculations, inverse-function analysis, special-function studies, and verifying that numerical root searches have found every zero in a bounded region.

## How funcprops proves it

Exact finite complex solves are tried first. Otherwise funcprops proves holomorphy on the closed rectangle using its structural complex-domain analysis. The boundary is traversed counterclockwise and adaptively subdivided. Each boundary segment is evaluated with complex interval arithmetic until its entire image provably excludes zero. Since that interval image is convex and zero-free, the true image of the segment is homotopic to the corresponding endpoint chord without crossing zero. The winding number of the resulting boundary polygon is therefore the argument-principle zero count.

For a rectangle containing more than one zero, funcprops tries several exact rational subdivision lines. Child rectangles are accepted only when every child has a certified argument-principle count and those counts sum exactly to the parent count. Rectangles with count one are isolated immediately; unresolved multiple-root clusters remain as certified higher-count rectangles rather than being split heuristically.

Successful conclusions are certified mathematical claims. Numerical contour sampling is retained only as diagnostic evidence when interval validation or holomorphy certification fails; it never changes `complete` to true.

## Known limitations

The current certified path handles holomorphic principal-branch expressions supported by the structural holomorphy and interval-evaluation backends. General meromorphic zero-minus-pole counting, arbitrary branch-cut crossings, unsupported special functions, roots lying on the requested rectangle boundary, and difficult interval dependency can leave the result uncertified. Multiple roots can be counted exactly but may remain inside a higher-count rectangle rather than being represented by a point.

`UNKNOWN` or an uncertified result means that the available proof machinery did not certify the contour or completeness. It does not mean that the rectangle has no zeros.

## Related properties

- [`function_zeros`](zeros.md)
- [`function_analytic`](analytic.md)
- [`function_meromorphic`](meromorphic.md)
- [`function_poles`](poles.md)
- [`function_singularity_analysis`](singularity_analysis.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
