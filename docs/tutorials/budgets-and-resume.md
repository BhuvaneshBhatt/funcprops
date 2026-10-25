# Budgets and resumption

What can I retain when a bounded search stops?

Checked states and same-environment trusted checkpoint transport; in-memory checkpoint contract.

Run `python examples/budgets_and_resume.py` from the checkout. Each section belongs to one ordered session.

<!-- workflow-id: budgets-and-resume -->

## Example

```python
import pickle
from dataclasses import replace

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
policy = fp.EnclosurePolicy(max_cells=400, max_depth=9)
seed = fp.adaptive_root_coverage(
    sp.exp(x) - 2, x, sp.Interval(0, 1), policy=replace(policy, max_cells=0)
)
assert seed.verify() and not seed.complete and seed.root_count is None
assert seed.state.exhaustion == "cell-budget"
state = pickle.loads(pickle.dumps(seed.state))  # trusted, same-environment transport
resumed = fp.resume_root_coverage(state, policy=policy)
assert resumed.verify() and resumed.complete and resumed.root_count == 1
z = sp.Symbol("z")
run = fp.adaptive_quotient_isolation(
    1 / (sp.exp(z) - 2), z, -1 - sp.I, 1 + sp.I, stages=0
)
assert run.verify() and not run.complete and run.state.unresolved
assert run.termination_contract.verify() and run.termination_contract.complete is False


unfinished = fp.domain(x ** sp.sqrt(2), x, work_budget=1e-6)
assert unfinished.complete is False and unfinished.certified is False
assert unfinished.operation == "domain" and unfinished.source == "work-budget-exhausted"
known = fp.track_domain(x ** sp.sqrt(2), x, sp.Interval(0, 1), work_budget=10)
assert known.verify() and known.effective == sp.Interval(0, 1)
```

## Expected result

An unresolved real seed resumes to one root; the cofinal quotient seed retains its unresolved region.

A resource limit stops a search without proving exclusion.

## Scope and next steps

Checkpoints are trusted same-environment records, not a durable untrusted-file format. See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).
