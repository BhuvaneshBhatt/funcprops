# Independent native replay

Can I check a native proof with its proposer disabled?

Native witness checking without search; factory-based and algebraic backend trust differs.

Run `python examples/replay.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: replay -->

## Example

```python
from dataclasses import replace
from unittest.mock import patch

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
proof = fp.prove_root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 1))
assert proof.verify() and proof.complete


def forbidden(*args, **kwargs):
    raise AssertionError("replay invoked proposing search")


with patch("funcprops.coverage_search.propose_leaf", forbidden):
    assert fp.verify_certificate(proof)
assert not fp.verify_certificate(replace(proof, root_count=77))
assert not fp.verify_certificate(proof, expr=sp.exp(x) - 3, var=x)
assert fp.replay_status(proof).outcome == "complete-coverage"
assert fp.replay_status(object()).certified is None
```

## Expected result

The original proof replays; the altered total and foreign source fail.

Registered concrete proof types bind the theorem to its original context.

## Scope and next steps

Factory-based and algebraic routes have their own declared replay dependencies. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
