# Certified complex analysis

## Why would I use this?

Complex symbolic calculations are sensitive to orientation, branch choice, multiplicity, and whether a contour crosses a singularity. Funcprops connects these obligations across winding numbers, homotopy, contour deformation, residues, singularity classification, the argument principle, and supported analytic continuation.

The main topology flow is

\[
\text{contour geometry}\to\text{winding/cut crossings}\to\text{homotopy}\to\text{deformation}.
\]

The local analytic flow is

\[
\text{local order}\to\text{singularity/residue data}\to\text{argument principle and monodromy}.
\]

## Example

```python
import sympy as sp
import funcprops as fp

t, z = sp.symbols("t z", real=True)
contour = fp.ParametricContour(2 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
assert fp.winding_number(contour, 0) == 1
assert fp.argument_principle((z - 1) / (z - 3), z, contour) == 1
assert fp.residue(1 / z, z, 0) == 1
```

## Scope

Rational meromorphic functions have the strongest global contour support because their finite divisors can be certified exactly. Transcendental argument-principle evaluation currently requires stronger meromorphicity/divisor machinery than the package provides in general. Analytic continuation covers structural logarithmic and rational-power cases; it is not a universal germ-continuation engine.
