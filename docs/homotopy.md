# Homotopy and contour deformation

For a finite puncture set `P`, based loops in `C \\ P` form a free group. With at least two punctures this group is nonabelian, so the order in which a loop passes generators matters.

A loop with word

\[
aba^{-1}b^{-1}
\]

has winding zero about both punctures but is not null-homotopic. This is why a winding vector cannot certify general multi-puncture homotopy.

Funcprops chooses a certified system of pairwise-disjoint parallel cuts from punctures to infinity, solves all contour/cut intersections exactly, orders the signed crossings along the contour, and freely reduces the resulting word. Two supported based loops are homotopic exactly when their reduced words agree.

```python
import sympy as sp
import funcprops as fp

t = sp.symbols("t", real=True)
first = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
second = fp.ParametricContour(3 * (sp.cos(t) + sp.I * sp.sin(t)), (t, 0, 2 * sp.pi))
certificate = fp.homotopic(first, second, punctures=(-1, 1), return_certificate=True)
assert certificate.verify()
assert len(certificate.reduced_word) == 2
```

## Certification boundary

The cut construction requires exact, transverse intersection geometry. A contour through a puncture, a tangent cut contact, an unresolved symbolic intersection, or a basepoint on a cut does not produce a homotopy certificate.

Contour deformation adds every pole forced by a rational integrand to the obstacle set. User-supplied punctures add obstacles; they cannot remove poles from the theorem domain.
