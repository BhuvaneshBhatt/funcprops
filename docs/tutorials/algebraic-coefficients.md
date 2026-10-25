# Exact algebraic coefficients

How do I keep an algebraic coefficient on its intended real conjugate?

Use a uniquely isolated generator in a bounded real number field and retain source holes.

Run `python examples/algebraic_coefficients.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: algebraic-coefficients -->

## Represent an exact coefficient field

An isolating interval selects sqrt(2) from the two roots of a rational polynomial. The generator guard prevents its negative conjugate from entering the query.

```python
import sympy as sp

import funcprops as fp

x, y = sp.symbols("x y", real=True)
field = fp.encode_algebraic_coefficients((sp.sqrt(2) * x, x < sp.sqrt(2)), (x,))
assert field.verify() and sp.degree(field.polynomial, field.generator) == 2
image = fp.range(sp.sqrt(2) * x, x, y, constraints=(x > 0) & (x < 1))
assert sp.simplify(image ^ ((y > 0) & (y < sp.sqrt(2)))) is sp.S.false
```

## Preserve an original hole

The held quotient agrees with 1 wherever it is defined. Its range at the excluded point sqrt(2) is empty.

```python
base = x - sp.sqrt(2)
raw = sp.Mul(base, sp.Pow(base, -1, evaluate=False), evaluate=False)
assert fp.range(raw, x, y, constraints=sp.Eq(x, sp.sqrt(2))) is sp.S.false
```

## Recognize the field boundary

The supported compositum has degree at most four and at most four nonrational constants. Larger fields decline this encoding; other property routes may still apply.

```python
assert (
    fp.encode_algebraic_coefficients((sp.sqrt(2) + sp.sqrt(3) + sp.sqrt(5),), (x,))
    is None
)
```

## Expected result

The image is (0,sqrt(2)); a canceled source hole has empty image at its excluded point.

The rational generator guard selects a unique real embedding.

## Scope and next steps

The compositum degree is at most four, with at most four nonrational constants and no extra coefficient parameters in the lift. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
