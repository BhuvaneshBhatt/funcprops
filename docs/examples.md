# Worked examples and certification failures

## Winding is not multi-puncture homotopy

The winding vector forgets generator order. The reduced free-group word retains it, so commutators remain visible even when every winding number is zero. See [Homotopy and contour deformation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/homotopy.md) for the geometric construction.

## Deforming around several poles

```python
import sympy as sp
import funcprops as fp

t, z = sp.symbols("t z", real=True)
first = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
second = fp.ParametricContour(3 * (sp.cos(t) + sp.I * sp.sin(t)), (t, 0, 2 * sp.pi))
certificate = fp.deform_contour(1 / ((z - 1) * (z + 1)), z, first, second, return_certificate=True)
assert certificate.verify()
assert set(certificate.punctures) == {-1, 1}
```

## A deformation that fails

```python
import sympy as sp
import funcprops as fp

t, z = sp.symbols("t z", real=True)
outer = fp.ParametricContour(2 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
inner = fp.ParametricContour(sp.Rational(1, 2) * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
assert fp.deform_contour(1 / (z - 1), z, outer, inner) is False
```

The pole at `z = 1` lies in different homotopy regions for the two loops.

## A proof boundary

```python
import sympy as sp
import funcprops as fp

t, z = sp.symbols("t z")
contour = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
assert fp.argument_principle(sp.exp(1 / z), z, contour) is None
```

The essential singularity violates the meromorphic divisor route used by the certified argument-principle implementation.
