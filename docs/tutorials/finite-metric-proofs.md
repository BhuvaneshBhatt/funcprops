# Finite metric and variation proofs

Can I certify an optimal finite bound and a total variation?

Compute exact finite Lipschitz constants and jump variation, then replay their proofs.

Run `python examples/finite_metric_proofs.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: finite-metric-proofs -->

## Certify a finite Lipschitz constant

A finite domain needs all pairwise slopes. The constant below is 2 on {-1,0,2}; it is not the interval derivative bound on [-1,2].

```python
from dataclasses import replace

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
metric = fp.lipschitz(x * x, x, domain=sp.FiniteSet(-1, 0, 2), return_result=True)
assert metric.constant == 2 and metric.optimal is fp.TruthValue.TRUE
assert metric.verify() and fp.verify_certificate(metric.proof)
```

## Replay total variation

The quadratic contributes motion 2, and the value 10 at zero contributes two excursions of size 10. Total variation is 22.

```python
spike = sp.Piecewise((10, sp.Eq(x, 0)), (x * x, True))
variation = fp.variation(spike, x, domain=sp.Interval(-1, 1), return_result=True)
assert variation.total_variation == 22 and variation.verify()
assert not fp.verify_certificate(
    replace(variation.proof, total_variation=sp.Integer(2))
)
```

## Separate a proved value from replay support

An affine interval query has optimal constant 3. This route carries no standalone finite-domain replay proof; a useful mathematical answer and supported replay are separate questions.

```python
affine = fp.lipschitz(3 * x + 2, x, return_result=True)
assert affine.constant == 3 and affine.optimal is fp.TruthValue.TRUE
assert affine.proof is None and affine.verify() is False
```

## Expected result

The finite constant is 2, the spike variation is 22, and both supplied proofs replay.

All finite pairs and all owned excursions contribute. A changed total is rejected.

## Scope and next steps

Interval derivative bounds can be useful without the finite replay contract. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
