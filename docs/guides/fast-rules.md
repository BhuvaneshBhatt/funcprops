# Specialized property rules

Property queries often need less work than a general elimination or calculus problem. Exact structural rules can return the same mathematical image from a few endpoint values, while retaining the source definition and requested domain.

## Quadratic interval images

Automatic range dispatch recognizes rational quadratics on intervals with rational or infinite endpoints. It evaluates the two endpoint limits and the vertex when the vertex belongs to the effective domain. An image endpoint is included if any contributing input attains it. This handles a shared endpoint value when one input endpoint is open and the other is closed.

```python
import sympy as sp
import funcprops as fp
from funcprops.real_analysis.common import condition_to_set

x, y = sp.symbols("x y", real=True)
source = sp.Interval.Lopen(-sp.Rational(5, 2), sp.Rational(3, 2))
image = fp.range(-3*x**2 - 3*x - 5, x, y, domain=source)
assert condition_to_set(image, y) == sp.Interval(-sp.Rational(65, 4), -sp.Rational(17, 4))
assert image.subs(y, -sp.Rational(65, 4)) is sp.S.true
```

The rule maps disconnected components separately, including isolated rational points, then takes their exact union. Input holes come from the original source before any arithmetic cancellation. For example, canceling a factor at the vertex can remove the only input attaining the minimum.

```python
q = x*x + 2*x + 3
held = sp.Mul(q, x + 1, sp.Pow(x + 1, -1, evaluate=False), evaluate=False)
image = fp.range(held, x, y, domain=sp.Interval(-2, 0))
assert condition_to_set(image, y) == sp.Interval.Lopen(2, 3)
```

Dispatch accepts at most 64 source nodes, 16 components, and 16 points in each finite component. Degree is checked before polynomial expansion, so a large unsupported power cannot trigger expansion in this rule. The source set must respect the coordinate's intrinsic assumptions. Symbolic or algebraic coefficients, nonrational finite endpoints, unresolved sets and larger inputs continue through the existing routes. The automatic rule runs when the current query uses `method="auto"` and has no additional backend options. Recursive structural subqueries retain their own method defaults.

## Rational signs and monotone comparisons

The scalar sign engine tries exact rational rules before registry analysis and general elimination. Exact Sturm counts distinguish absent zeros, odd interior crossings and attained even or endpoint zeros. Rational denominator exclusions and canceled source holes stay in the effective domain. Connected components are checked separately.

```python
polynomial = sp.expand((x*x - x + 1)**3)
assert fp.sign(polynomial, x, domain=sp.Interval(0, 1)) is fp.Sign.POSITIVE
assert fp.sign((x - 1)**3 / (x + 2), x, domain=sp.Interval(0, 2)) is fp.Sign.SIGN_CHANGING
assert fp.sign(sp.log(x*x + 1) - sp.log(2), x, domain=sp.Interval.open(-1, 1)) is fp.Sign.NEGATIVE
```

For a real polynomial inner expression and c > 0, comparing exp(g(x)) with c is equivalent to comparing g(x) with log(c). Comparing log(g(x)) with a real c uses g(x) versus exp(c), with the original positive-logarithm domain retained. Exact affine/quadratic images preserve endpoint ownership. Nonrational thresholds use outward enclosures; an unresolved comparison declines the rule. Rational central sine/cosine charts also avoid root search, using the exact bounds 3 < pi < 4.

These sign rules accept a bounded rational grammar of at most 96 nodes, numerator/denominator degrees at most 12, at most eight rational components and 512-bit rational constants/endpoints. Threshold comparisons accept rational constants and rational multiples of E, pi, or one logarithm of a positive rational; the transformed exponent in a logarithm comparison is bounded to absolute value 128. Explicit parameters, inexact coefficients, unsupported sets and larger formulas continue through existing routes. The rules can improve several consumers without invoking a second general sign search.

## Shared Jacobian facts

Scalar Jacobian analysis uses the same bounded sign rules after proving real source definition, coordinate compatibility and C1 regularity. A strict sign proves nonvanishing. Positive and negative values on disconnected components do not establish a zero between those components. The general zero search also retains supplied assumptions in its query.

```python
proof = fp.determinant_nonvanishing(sp.sin(x), x, domain=sp.Interval(-1, 1), return_result=True)
assert proof.classification is fp.TruthValue.TRUE and proof.verify()
guarded = fp.determinant_nonvanishing(x**3/3 - x*x/2, x, assumptions=x > 2)
assert guarded is fp.TruthValue.TRUE
```

## Curvature on rational boxes

For a supported real C2 expression on a rational box, outward Hessian entry bounds can establish strict diagonal dominance. A positive lower bound for each diagonal minus its off-diagonal absolute row sum gives a uniform strong-convexity modulus. Applying the same test to the negative Hessian proves strong concavity.

The source C2 check establishes equality of mixed partials before the proof shares symmetric Hessian entries. Each row margin is still bounded separately, and replay reconstructs every stored entry and margin from the source.

```python
u, v = sp.symbols("u v", real=True)
expression = u**4 + v**4 + 2*u*u + 2*v*v + u*v
box = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
result = fp.convexity(expression, (u, v), domain=box, return_result=True)
certificate = result.evidence[0]
assert result.primary is fp.Convexity.STRONGLY_CONVEX
assert certificate.modulus == 3
assert fp.verify_certificate(certificate, expr=expression, var=(u, v))
```

The box rule supports two to four coordinates and a bounded raw-source grammar of rational arithmetic, integer powers and single-argument exp/log/sin/cos. Every operation must be real and C2 on the closure of the box. Abs, Piecewise, free parameters, source poles and unsupported branches decline. Primitive argument bounds are limited to absolute value 128; interval arithmetic is bounded to 4096-bit rationals. Source nodes and derivative entries are bounded to 96 nodes. Certificate replay reconstructs the source premises, entry bounds and margin without calling the certificate proposer or the general convexity query.

Known signs of off-diagonal entries allow the row-margin formulas to retain common terms: (exp(u+v)+2)-abs(exp(u+v)) reduces to 2. Strict diagonal dominance remains a sufficient rule and can fail to prove positive curvature. A structural exponential-Hessian bound supplements it for quadratic exponents, while an exact interior Hessian section can disprove both convexity and concavity. See [bounded property proofs](bounded-proofs.md) for these rules, scalar Jacobian zero witnesses, relative seam continuity, excluded-seam metric counterexamples and entire square-root cancellations.

## Measuring dispatch changes

Run `python -m tools.benchmark_routing --report validation/routing.json` from a checkout. It checks 25 fixed-answer queries, including 15 supported quadratic cases and 10 fallback controls. Each case records cleared-cache and warm-cache samples and medians. Untimed instrumentation counts semialg range calls and general calculus calls separately.

For a comparison, run the same harness and dependency environment against each source tree. Repeat with reversed execution order, compare fallback controls as well as successful dispatches, and retain the raw samples. Interpreter imports and answer validation are outside the timed region. Clearing funcprops and SymPy caches does not make a measurement equivalent to restarting every dependency. Timing reports are advisory; mathematical assertions and independently checked query answers determine correctness.

The tests also compare generated rational quadratics with direct existential quantifier elimination. They check source holes, tied endpoints, negative leading coefficients, finite unions, unsupported inputs and execution with general range routes disabled. A higher-level range routine is not an independent oracle when it uses the same endpoint aggregation as the route being tested.

`python -m tools.benchmark_sign_routes --report validation/sign-routing.json` checks fixed polynomial/rational signs, threshold comparisons, Jacobians and coupled Hessians, plus fallback controls. It records answers as well as elapsed time: proving a result where the preceding tree returned UNKNOWN is a capability gain, not a speedup over an equivalent completed proof. Use `--groups` for selected families and `--disable` to measure one rule's contribution through benchmark-only instrumentation. Production dispatch has no benchmark switches. Warm public sign timings include the existing result cache.
