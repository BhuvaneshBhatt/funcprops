# Working with results, assumptions, certificates, and caches

## Why would I use this?

Many symbolic questions have more than one mathematically valid answer because a
parameter has not been fixed. `funcprops` keeps those cases explicit instead of
choosing one silently. It also exposes replayable certificates for proofs that
need to be inspected, logged, or rechecked later.

## Resolving parameter-dependent results

Pass assumptions directly to public property queries when a parameter regime is
known:

```python
import sympy as sp
import funcprops as fp

a, x = sp.symbols("a x", real=True)
fp.function_monotonicity(a*x, x, assumptions=a > 0)
# Monotonicity.STRICTLY_INCREASING
```

Without sufficient assumptions, a query may return `PropertyResult` with guarded
cases. The `.resolved` property returns an unconditional compact value when one is
available.

## A common detailed view

`as_detailed_result()` projects compact enums, sets, conditional results, and
certificate objects onto `DetailedPropertyResult` without changing the default
return types of the public APIs.

```python
result = fp.function_change_of_variables((2*x,), x)
detail = fp.as_detailed_result(result)
print(detail.primary)
print(detail.certificate)
```

`explain_result()` gives a concise summary of the classification, proof route,
domain, and certificate when those fields are available.

```python
fp.explain_result(result)
```

This helper is for inspection and presentation. `verify_certificate()` remains
the API for independent certificate replay.

## Replaying a certificate

```python
fp.verify_certificate(result)
# True
```

Some certificate families need the original expression or variable during replay;
`verify_certificate()` reports that requirement with a `ValueError` rather than
guessing context.

## Managing caches

Long-lived notebooks, services, and benchmarks can inspect or reset every bounded
package cache through one public surface:

```python
fp.cache_info()
fp.clear_caches()
```

`cache_info()` returns the standard `functools` cache statistics for each named
cache. Clearing caches changes performance state only; it does not change symbolic
results.
