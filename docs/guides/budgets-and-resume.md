# Budgets, interruption and resumption

EnclosurePolicy controls bounded precision refinement, series/Taylor effort, cell/depth caps and optional seconds for supported coverage/isolation APIs. Precision caps bound refinement, not the complexity of arbitrary symbolic work. Without a wall budget, a cell cap is not a wall-time guarantee.

Domain, boundedness, continuity, differentiability, smoothness, analytic and meromorphic classification, metric regularity, variation, integrability, injectivity, surjectivity and bijectivity accept `work_budget` in seconds. Jacobian and transformation helpers, `track_domain`, range, sign, monotonicity, convexity and the certified search helpers also accept it; consult [helper signatures](../reference/helpers.md) and the operation's guide. Expiry returns unknown/incomplete evidence, not a negative mathematical answer. Ordinary transported query errors retain their documented exception behavior.

Supported adaptive real, native complex and quotient searches expose checked states and resume functions. Every installed replacement cover is atomic; unprocessed regions remain explicit. A checkpoint describes already completed work and pending tasks, not a proof that the future search terminates. See the [executable budget/resume workflow](../tutorials/budgets-and-resume.md).

Wall-budget workers involve startup, serialization and recovery overhead; the worker timeout is not an exact process-wide latency bound. POSIX cleanup kills a worker process group, while other platforms kill the direct worker. Inputs and transported states must be pickle-compatible. This is process isolation for resource control, not an untrusted-code sandbox.

In-memory states, and same-environment pickle round trips exercised in tests, describe in-memory state, not a durable storage format. Never unpickle untrusted files. Persist the source, policy, dependency metadata and validation results if maintaining a trusted local checkpoint workflow.

Cofinal scheduling increases effort fairly under its stated hypotheses. Its conditional guarantee always remains incomplete as a theorem instance, even when a particular search result completes. See [result contracts](../reference/result-contracts.md) and [the design](../quotient-search.md).

Property and transformation queries other than range, sign, monotonicity and convexity return a `BudgetedResult` on exhaustion, including when `return_result=False`. It retains the operation, original query, reason, and `complete=False`/`certified=False`; its `primary` is an unknown classification where one exists. A successful query keeps its usual mathematical return value. `track_domain` returns an incomplete `DomainRecord` with unresolved natural/effective sets and the exhaustion reason. The range/sign/monotonicity/convexity APIs retain their compact unknown defaults; use `return_result=True` to keep exhaustion metadata.
