# Working with results, assumptions, certificates, and caches

## Why would I use this?

Many symbolic questions have more than one mathematically valid answer because a parameter has not been fixed. `funcprops` keeps those cases explicit instead of choosing one without evidence. It also exposes replayable certificates for proofs that need to be inspected, logged, or rechecked later.

## Resolving parameter-dependent results

Pass assumptions directly to public property queries when a parameter regime is known:

```python
import sympy as sp
import funcprops as fp

a, x = sp.symbols("a x", real=True)
assert fp.monotonicity(a*x, x, assumptions=a > 0) is fp.Monotonicity.STRICTLY_INCREASING
```

Without sufficient assumptions, a property query may have several guarded cases. The root API projects a fully or partially stratified `PropertyResult` to a SymPy `Piecewise` by default. Any uncovered region receives an explicit symbolic `unknown` fallback instead of being interpreted as false.

```python
fp.injective(a*x, x)
# Piecewise((True, Ne(a, 0)), (False, True))

result = fp.injective(a*x, x, return_result=True)
result.cases
# certified guarded cases with evidence/provenance retained
```

For a rich `PropertyResult`, `.resolved` returns an unconditional compact value when one is available, and `.as_piecewise()` performs the same compact projection used by the public API.

## A common detailed view

`as_detailed_result()` projects compact enums, sets, conditional results, and certificate objects onto `DetailedPropertyResult` without changing the default return types of the public APIs.

```python
result = fp.change_of_variables((2*x,), x)
detail = fp.as_detailed_result(result)
print(detail.primary)
print(detail.certificate)
```

`explain_result()` gives a concise summary of the classification, proof route, domain, and certificate when those fields are available.

```python
fp.explain_result(result)
```

This helper is for inspection and presentation. `verify_certificate()` remains the replay API. Native witness kernels, declared algebraic backends, and factory-based theorem-factory replay have different trust boundaries; see [certification](certification.md).

## Replaying a certificate

```python
assert fp.verify_certificate(result)
```

Some certificate families need the original expression or variable during replay; `verify_certificate()` reports that requirement with a `ValueError` instead of guessing context.

## Managing caches

Long-lived notebooks, services, and benchmarks can inspect or reset every bounded package cache through one public surface:

```python
fp.cache_info()
fp.clear_caches()
```

`cache_info()` returns the standard `functools` cache statistics for each named cache. Clearing caches changes performance state only; it does not change symbolic results.

## Completion, partial evidence and budgets

Read the [route-specific contract table](reference/result-contracts.md) before using a global count. Native complex isolation distinguishes coverage, individual isolation and requested accuracy. Quotient ledgers also distinguish source zeros, extension zeros and poles. A partial proof may replay successfully.

Use [budgets and resumption](guides/budgets-and-resume.md) to interpret exhausted work and checked checkpoints. Conditional cofinal guarantees do not supply a finite-time completion oracle. Runnable examples are in the [workflow tutorials](tutorials/index.md).
