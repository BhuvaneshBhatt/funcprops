# Domain provenance, replay status and component minima

Python blocks on this page form one ordered session, executed from a fresh namespace.

`track_domain(f, x, requested)` returns a source-bound `DomainRecord` with `requested`, `natural`, `effective`, `exclusions`, `complete` and `reason`. The effective set intersects the requested restriction with the original expression's definition domain. Source inspection runs before cancellation. Replay permits alpha-renaming of bound indices in periodic exclusion sets.

The exact domain route supports continuous real arithmetic with integer powers, real finite coefficients, exp/sin/cos/tan/cot/hyperbolic heads and Abs. It declines logs, noninteger powers, Piecewise/discrete heads and unresolved source/parameter predicates. Complex intermediate branches require more than intersecting real operand domains; no exact natural-domain claim is made for those unsupported families. `complete=False` leaves natural/effective unknown. The older domain engine retains its broader capabilities.

Detailed range, sign, monotonicity, convexity and supported regularity wrappers record the original expression and the combined restriction before local simplification. Existing compact return values are unchanged. The record is metadata, not a replacement for those engines' own proof premises. Specialized native result types outside PropertyResult/DetailedPropertyResult have not all migrated. PropertyProofContext exposes `domain_record()` and combines its domain and assumptions. RootIsolationResult also retains source-domain provenance; an unknown natural-domain record does not invalidate an independently supported root-family theorem.

```python
from sympy import Symbol, Interval, Union
from funcprops import track_domain, finite_component_minimum, replay_status
x = Symbol('x', real=True)
r = track_domain(1/x, x, Interval(-2, 3))
assert r.effective == Interval(-2, 3) - {0}

m = finite_component_minimum(x**2, x,
    Union(Interval(-3, -2), Interval(1, 2)))
assert m.infimum == 1 and m.unique
assert replay_status(m).certified
```

`finite_component_minimum` supports parameter-free rational functions and a finite union of intervals/finite sets. It records all closed endpoints, open or infinite endpoint limits, and a complete exact finite derivative-root set. Constants retain whole minimizing intervals. Source poles split the effective domain before differentiation. Exact symbolic comparisons must resolve; Float coefficients/endpoints, incomplete root sets or unsupported geometry decline.

`ComponentMinimumResult` distinguishes infimum, minimizers, attained, unique, candidates, complete, certified and reason. An empty effective domain has infimum +oo and no minimizers. A function unbounded below has infimum -oo and no minimum. Open-endpoint infima are not turned into attained minima.

`certify_global_minimum` uses this route when possible, including endpoint and nonunique minima, then a guarded C2 convex-stationary route. The certificate's `domain` remains the effective set; `requested_domain` and `domain_record` preserve the original request. A disconnected domain is never treated as one convex interval. The curvature helper declines inexact Float data.

`verify_certificate` recognizes DomainRecord, ComponentMinimumResult, GlobalMinimumCertificate, RootIsolationResult and RealRootInterval. These records bind replay to the expression/variable when supplied. Their `certified` field/property means supported replay succeeds, not that a pointer exists. `replay_status` gives a consistent view across the verifier registry:

- unsupported replay: supported=False, certified=None, complete=None;
- failed replay: supported=True, certified=False, complete=False;
- successful replay: certified=True, complete is the verified record's declared coverage if it reports coverage, otherwise None.

Partial root data can be certified with complete=False. Local count completion is scoped to its interval, not all real numbers. The scope field describes that boundary. Existing factory-based records are not all source-bound or coverage-aware; the adapter does not invent missing claims. Replay uses the same audited proof routes, not an independent formal proof kernel.
