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

`log` and nonintegral rational powers begin on their symbolic principal branches. Analytic continuation along a supported closed contour is represented by the change accumulated along that contour. A logarithm gains

\[
2\pi i\,\operatorname{wind}(g\circ\gamma,0),
\]

when the winding of its argument is certified. A rational power `g**q` acquires the corresponding factor `exp(2*pi*I*q*w)`.

## Local orders

For meromorphic `f`, positive local order denotes a zero and negative local order denotes a pole. Multiplicity is retained in residue, divisor, branch, and monodromy calculations.

## Endpoints and singularities

A contour theorem requires its contour to avoid every singularity that the theorem excludes. Endpoint equality and path-limit endpoints are mathematical obligations, not display metadata.
