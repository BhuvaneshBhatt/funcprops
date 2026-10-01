# Certified integration and parametric contours

`funcprops.integrate` returns the mathematical value by default. Pass
`return_result=True` to obtain a replayable `IntegralResult` with method,
completeness, certification evidence, and (for validated Taylor quadrature) an
explicit error bound.

```python
import sympy as sp
import funcprops as fp
x = sp.symbols("x")
fp.integrate(x**2, (x, 0, 2))                 # 8/3
fp.integrate(x**2, (x, 0, 2), return_result=True)
```

## ParametricContour

An oriented symbolic contour retains its parameterization
geometric image:

```python
z = sp.symbols("z")
t = sp.symbols("t", real=True)
gamma = fp.ParametricContour(sp.cos(t) + sp.I*sp.sin(t), (t, 0, 2*sp.pi))
fp.integrate(1/z, (z, gamma))                 # 2*pi*I
fp.integrate(1/z, (z, gamma.reversed()))      # -2*pi*I
```

Polynomial/rational parameterizations delegate semialgebraic incidence and
nonvanishing obligations to Semialg when available. Algebraizable sine/cosine
parameterizations retain an explicit unit-circle algebraization while keeping
the original parameter interval, so orientation and multiple winding are not
lost. General analytic pullbacks use adaptive Taylor panels. Remainders are
bounded with validated interval arithmetic; inability to enclose a derivative
causes an incomplete result.

A sequence of complex points is accepted as a piecewise-linear path:

```python
square = [1+sp.I, -1+sp.I, -1-sp.I, 1-sp.I, 1+sp.I]
fp.integrate(1/z, (z, square))                # 2*pi*I
```

## Certification boundary

Exact antiderivatives are not by themselves evidence that a singular path is
valid. Rational pulled-backs are checked for denominator zeros on the parameter
interval. Unsupported path/branch geometry remains incomplete. The analytic
Taylor route certifies only when every panel receives a validated derivative
bound and the sum of remainder bounds meets the requested tolerance.
