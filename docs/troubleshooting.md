# Interpreting an unfinished answer

Start with the result's concrete type, source domain and theorem scope. Use the [result contracts](reference/result-contracts.md) and [helper field reference](reference/helper-contracts.md) to decide which conclusion is established.

| Observation | Meaning | Useful next step |
| --- | --- | --- |
| A compact property is UNKNOWN | The available rules did not decide it | Make parameter hypotheses explicit, supply an exact restricted domain, and request detailed results where supported |
| verify() succeeds but complete is false | The supplied local/partial evidence is valid | Inspect unresolved regions, clusters and the relevant per-conclusion completion fields |
| verify_certificate returns false | Evidence is unsupported or rejected; this does not negate the mathematical proposition | Inspect replay_status, check the concrete record type and retain the original source/coordinate/domain |
| certified is None in replay_status | Unified replay is unavailble for this object | Use its documented route; do not treat an arbitrary verify method as a certificate |
| A wall budget expires | Work ended without the requested theorem | Retain a supported checkpoint and resume, or choose a narrower domain or larger budget |
| A coefficient route declines | The exact field, embedding or expression grammar is outside that adapter | Keep exact SymPy constants and allow native routes; check the field-degree and parameter limits |
| A branch assembly reports disagreement | The supplied selected charts differ | Inspect sheet choices and overlaps; disagreement alone does not prove every possible global branch impossible |
| A native contour boundary contains a zero | The contour theorem's nonvanishing premise fails | Choose a rational rectangle whose boundary is clear, retaining all regions of the original root question |

## A valid partial result

```python
import sympy as sp
import funcprops as fp

x, a = sp.symbols("x a", real=True)
partial = fp.certify_parameter_geometry(x*x-a, x, (a,), max_cells=0)
assert partial.verify() and not partial.complete
assert partial.specialize({a: 1}) is None
complete = fp.resume_parameter_geometry(partial, max_cells=100)
assert complete.verify() and complete.specialize({a: 1}) == 2
```

The missing count was unresolved, not zero. Increased effort can complete this example; it does not supply a termination theorem for arbitrary inputs.

## Preserve the question

An expression simplified before the query may no longer contain its original holes. Build held operations before evaluation when source definition matters. A positive Symbol also carries premises that cannot be removed by a later domain argument. Finite metric queries use their source-defined effective points, while jump-variation proofs require coverage of their stated interval.

Use exact rationals for certified rectangle corners and exact parameter substitutions. Higher numerical precision can help outward enclosures separate zero, but cannot replace a source-definition proof, an identity or a missing region of the cover.

## Reproduce a failure

Keep the raw source construction, coordinate assumptions, requested domain, policy/budget, concrete result type and dependency versions. A minimal exact example is more useful than a decimal approximation alone. See [testing](guides/testing.md), [source semantics](source-semantics.md) and [budgets](guides/budgets-and-resume.md).
