# Mathematical conventions

## Contour orientation

A `ParametricContour(gamma, (t, a, b))` is oriented by increasing parameter from `a` to `b`. Reversing the bounds reverses orientation. Positive winding is counterclockwise.

For a closed contour `gamma` avoiding `p`,

\[
\operatorname{wind}(\gamma,p)=\frac{1}{2\pi i}\oint_\gamma\frac{dz}{z-p}.
\]

## Based loops and punctures

Homotopy certificates compare closed loops with the same basepoint in the plane with the stated punctures removed. For two or more punctures, Funcprops uses ordered signed cut crossings and free-group reduction. Winding vectors alone are not a complete invariant.

Generator labels follow puncture order. A positive letter denotes a positive crossing of that generator's cut; a negative letter denotes the reverse crossing. Adjacent inverse letters cancel.

## Branches

`log` and nonintegeral rational powers begin on their symbolic principal branches. Analytic continuation along a supported closed contour is represented by the change accumulated along that contour. A logarithm gains

\[
2\pi i\,\operatorname{wind}(g\circ\gamma,0),
\]

when the winding of its argument is certified. A rational power `g**q` acquires the corresponding factor `exp(2*pi*I*q*w)`.

Real-domain analysis and real algebraization follow SymPy's ordinary `Pow` semantics: for a real base, a noninteger rational exponent, including one with an odd denominator, requires a nonnegative base (strictly positive for negative exponents). Use `real_root` when a real odd root of a negative base is intended. Auxiliary charts retain these branch conditions before cancellation. Powers outside the supported rational vocabulary cause algebraization to decline, even if they would disappear in the simplified auxiliary expression.

## Local orders

For meromorphic `f`, positive local order denotes a zero and negative local order denotes a pole. Multiplicity is retained in residue, divisor, branch, and monodromy calculations.

## Endpoints and singularities

A contour theorem requires its contour to avoid every singularity that the theorem excludes. Endpoint equality and path-limit endpoints are mathematical obligations, not display metadata.

## Real proofs and disconnected domains

Real-property proofs distinguish real output from complex intermediate values. For supported explicit complex expressions, a real-domain query includes the condition that the entire expression has zero imaginary part. Zero and identity certification require both real and imaginary parts to vanish.

A derivative sign proves monotonicity on a connected interval. Equal local monotonic directions across several intervals require additional ordering of one-sided seam values before they imply global monotonicity or injectivity. Compact monotonic partitions returned by the package remain tuple-compatible and retain their rich certificate; manually constructed tuples with multiple cells cannot provide missing seam evidence.

Strict curvature of an outer function alone does not make a composition strict. The composition must also satisfy the inner-curvature/order or injectivity hypotheses. A flat inner segment cannot become strictly convex through exponentiation.

Complete real-root families require real formula values and real affine phases. A parameter-only expression is root-free only after it is proved nonzero.
