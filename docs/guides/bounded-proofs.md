# Bounded proofs for regularity and curvature

Use these rules when a property query would otherwise need a general symbolic search. A checked zero or an interior Hessian section can disprove a global hypothesis. A positive regularity or curvature claim needs coverage of the requested domain. The rules below preserve the raw source and expose replayable evidence through detailed results.

```python
import sympy as sp
import funcprops as fp

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")
box = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
punctured = sp.S.Reals - sp.FiniteSet(0)
```

## A zero disproves Jacobian nonvanishing

```python
jacobian = fp.determinant_nonvanishing(sp.sin(x), x, domain=sp.Interval(0, 2), return_result=True)
assert jacobian.classification is fp.TruthValue.FALSE
assert jacobian.witness == sp.pi/2
assert fp.verify_certificate(jacobian)
```

The scalar rule reuses finite affine sine/cosine zero sets after proving that the original map is real and C1 throughout the requested support. Search is restricted to finite intervals with phase width at most 32. The stored point is checked directly during replay, without repeating root discovery. A zero outside the support, including an excluded endpoint, cannot be a witness. Mixed determinant signs on disconnected components do not imply a zero.

## Relative continuity and limiting gaps

```python
continuity = fp.continuous(sp.sin(x)*sp.sign(x), x, return_result=True)
assert continuity.primary is fp.Continuity.CONTINUOUS
assert fp.verify_certificate(continuity.evidence[0])
step = sp.Piecewise((0, x < 0), (1, True))
assert fp.continuous(step, x, domain=punctured) is fp.Continuity.CONTINUOUS
```

Assembly rewrites supported affine sign arguments into exact real branches, checks first-match coverage, proves each selected branch smooth on its source-defined cell, and checks its relative seam limits. An included seam also needs its actual value to match every accumulating side. An excluded seam imposes no continuity condition at that point.

Uniform continuity can still fail across an excluded seam. Two intervals approaching a common point have arbitrarily close pairs of inputs. Finite unequal limiting values keep their output differences away from zero, disproving uniform continuity and Lipschitz regularity simultaneously.

```python
metric = fp.lipschitz(sp.atan(1/x), x, domain=punctured, return_result=True)
uniform = fp.uniformly_continuous(sp.atan(1/x), x, domain=punctured, return_result=True)
assert metric.value is uniform.primary is fp.TruthValue.FALSE
assert metric.proof.seams[0][3] == (-sp.pi/2, sp.pi/2)
assert metric.verify() and fp.verify_certificate(uniform.evidence[0])
```

A negative Lipschitz result alone does not disprove uniform continuity. This route uses the stronger limiting-gap proof. Separated components with positive distance between them do not supply such a witness.

## Positive curvature and an interior counterexample

```python
expression = sp.exp(x*y) + 2*x*x + 2*y*y
curvature = fp.convexity(expression, (x, y), domain=box, return_result=True)
certificate = curvature.evidence[0]
assert curvature.primary is fp.Convexity.STRONGLY_CONVEX
assert certificate.modulus == 4-sp.E
assert fp.verify_certificate(certificate, expr=expression, var=(x, y))

expression = x**4 + y**4 + 10*x*y
curvature = fp.convexity(expression, (x, y), domain=box, return_result=True)
assert curvature.primary is fp.Convexity.NEITHER
assert curvature.evidence[0].proof[3] == (0, 0)
assert fp.verify_certificate(curvature.evidence[0], expr=expression, var=(x, y))
```

For a positive multiple of exp(g), the Hessian is exp(g) times Hess(g) plus the positive semidefinite outer product of grad(g) with itself. The supported rule combines constant Hessian lower bounds for quadratic forms with outward bounds on g. Here Hess(g) has lower bound -1 and g lies in [-1,1], giving the exact modulus 4-e. This supplements the diagonal-dominance rule when entry bounds lose too much correlation.

For a polynomial source, a negative two-coordinate principal Hessian determinant at the rational box midpoint proves positive and negative directional curvature at an interior point. This disproves both convexity and concavity. A failed midpoint check is inconclusive; it is not a proof of curvature elsewhere.

Both rules require the existing bounded raw-source C2 grammar on a rational box in two to four variables. The exponential rule supports a rational quadratic remainder plus positive rational multiples of exponentials of rational quadratic forms. Parameters, Piecewise seams, inexact coefficients, poles and unsupported source operations decline these routes.

## Canceling a square-root branch

```python
for expression in (sp.cos(sp.sqrt(z)), sp.sin(sp.sqrt(z))**2):
    result = fp.meromorphic(expression, z, return_result=True)
    assert result.primary is fp.Meromorphicity.MEROMORPHIC
    assert fp.verify_certificate(result.evidence[0])
    assert fp.analytic(expression, z, domain=sp.S.Complexes) is fp.Analyticity.ANALYTIC
    assert fp.domain(expression, z, domain=sp.S.Complexes) is sp.S.true
    assert fp.branch_points(expression, z) is sp.S.false
    assert fp.branch_cuts(expression, z) == ()
```

The even power series of cos(sqrt(w)) and cosh(sqrt(w)) converge for every complex w and contain only integer powers of w. The squared sine and hyperbolic-sine templates follow from double-angle identities. Composing these templates with a source already proved entire yields an entire function, including across the inner square-root cut and at its zeros. The analytic, meromorphic, complex-domain and branch-locus helpers share this theorem. Cut-jump propagation also removes the canceled inner cut. The natural real domain is all reals when the entire inner map is provably real on real inputs. Cuts of an outer logarithm or other uncanceled branch remain relevant.

The theorem does not apply to sin(sqrt(z)), an arbitrary fractional power, or an inner logarithm or pole. It cannot fill a canceled source hole. It accepts exact expressions of at most 96 nodes with no free parameters beyond the coordinate.

## Scope and measurement

Seam assembly accepts at most 80 source nodes and twelve exact interval/finite cells, rational seams, rational polynomial guards and affine rational sign arguments. Its real smooth grammar contains rational arithmetic, bounded integer powers, sin, cos, exp, log and atan. Each primitive retains its source definition on the selected support. Unsupported guards, unresolved limits and mismatched point values decline the rule.

`SeamRegularityProof` and `EntireCancellationProof` have standalone replay through `verify_certificate`. The Hessian methods and scalar zero-witness route also replay without their proposing functions. The supporting symbolic arithmetic, domain primitives and exact limits remain trusted; replay is not a separate formal proof assistant.

Run `python -m tools.benchmark_practical --report validation/practical.json` to measure these cases alongside prior sign, Hessian and Jacobian controls. Compare the same harness and environment against each tree, including reversed execution order and unsupported cases. An UNKNOWN attempt and a completed proof are different outcomes, even when their elapsed times are similar.
