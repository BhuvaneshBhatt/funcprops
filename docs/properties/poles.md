# Poles

`function_poles`

## Mathematical definition

Pole analysis identifies isolated singularities with finite negative local order and records multiplicity when known.

## API and return values

```python
function_poles(expr, var, *, assumptions=True, return_result=False)
```

A list of (pole, multiplicity) pairs by default; return_result=True returns the supporting Singularity records.

## Domains, assumptions, and parameters

The query is interpreted on the supplied domain rather than from the expression in isolation. When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.

## Executable examples

### Simple pole

<!-- example-id: poles-rational -->

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
result = fp.function_poles(1/x, x)
result
```

Expected: one simple pole at ``x = 0``.

Application: Locate poles for contour deformation, residues, and singular quadrature.

## Applications

This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.

## How funcprops proves it

Local order, rational denominator structure, special-function singularity facts, and guarded parameter analysis.

Successful conclusions are exact symbolic claims over the stated domain and assumptions. Detailed modes expose evidence or certificates where the property API supports them.

## Known limitations

Multiplicity can be unknown when local cancellation or parameter dependence cannot be resolved exactly.

`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.

## Related properties

- [`function_singularities`](singularities.md)
- [`function_meromorphic`](meromorphic.md)

## Source

The implementation is exposed through [`funcprops.api`](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/funcprops/api.py).
