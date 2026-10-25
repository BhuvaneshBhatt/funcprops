# Algebraic complex-root backend integration

Python blocks on this page form one ordered session, executed from a fresh namespace.

The algebraic route uses algroots for exact enumeration and funcprops for source, domain and principal-branch filtering.

## Public behavior

`isolate_complex_roots()` and `complex_zeros()` automatically route the supported exact algebraic class to algroots. Supported transcendental inputs use native contour isolation. The adapted proof is also available directly:

```python
import sympy as s
import funcprops as fp
z = s.Symbol('z')
rectangle = (-2-2*s.I, 2+2*s.I)
r = fp.complex_zeros((z-1)**3, z, rectangle=rectangle, return_result=True)
assert r.complete and r.isolation_complete
assert r.distinct_root_count == 1 and r.multiplicity_count == 3
assert r.verify() and fp.verify_certificate(r, expr=(z-1)**3, var=z)
p = r.algebraic_certificate
assert fp.replay_status(p).complete is True
```

`certify_algebraic_complex_roots(expr, var, rectangle, domain=Complexes, condition=True)` returns `AlgebraicComplexRootProof`. `check_algebraic_complex_roots()` returns the common `CheckResult` vocabulary. Both the proof and adapted `ComplexRootIsolationResult` support `verify_certificate()` and `replay_status()`. Compact complete exact results are FiniteSet/EmptySet; detailed results retain the adapted proof.

## Supported class

- One unconstrained complex Symbol, exact algebraic coefficients, arithmetic and constant rational exponents, with no free parameters or floating literals.
- Exact rational rectangle corners. Source-defined zeros on its closed boundary are included; this root-set theorem does not require a zero-free contour.
- A zero-dimensional augmented system that algroots' exact RUR backend can enumerate and certify. Unresolved algebraic arithmetic is not a numerical proof.
- Set restrictions: Complexes, Reals, EmptySet, finite algebraic sets, real intervals with algebraic/infinite endpoints, and finite unions, intersections and complements. Candidate membership must be decided exactly. Arbitrary ConditionSet/ImageSet domains decline.
- Raw algebraic Eq/Ne guards and And/Or/Not combinations. Public assumptions and nested ConditionalExpression guards are retained together. Free parameters, ordering guards and arbitrary planar restrictions remain outside this facade.

Other exact routes expose their own declared replay contracts.

## Source, branch and domain obligations

The adapter sends the original expression to algroots' public algebraization API. Denominator saturation and rational-power auxiliaries provide an algebraic superset. It then uses the public exact rational-univariate enumeration. Numerical solver coordinates and small residuals are not certificates.

Every enumerated augmented point receives an explicit decision. Rectangle and requested-domain membership are checked, as are raw guards, the original source equation and each principal auxiliary lift. Raw arithmetic is evaluated from children upward: a zero factor cannot erase an undefined denominator. Negating an undefined guard does not make it true. An auxiliary branch rejected by the principal-power convention cannot enter the source root set.

Held z*z/z does not acquire a root at zero. For sqrt(z)+1 the algebraized candidate z=1 is rejected, while sqrt(z)-1 retains z=1. Source holes in held conditional guards survive the public facade too.

Unresolved values, branch equalities, memberships or projections retain obligations and prevent completeness. Exact accepted roots can still be exposed in a checked partial record. Whole-query counts remain None until every candidate is accounted for. A pending decision may remain pending on replay even if additional backend work could decide it; replay never upgrades the record.

## Count and status contract

| Field | Meaning |
| --- | --- |
| `roots` | Exact accepted source locations, potentially partial |
| `root_count` / `distinct_root_count` | Distinct count only after complete filtering |
| `multiplicities` | Source orders aligned with roots; entries may be None |
| `total_count` / `multiplicity_count` | Sum only after coverage and all orders are proved |
| `complete` / `coverage_complete` | All exhaustive algebraic candidates accounted for |
| `isolation_complete` | The finite root set is fully located on this exact route |
| `certified` | Replay validates local evidence/status; does not imply complete |

Rational-source orders are proved using the normalized numerator at a point where the original source and denominator are defined and nonzero as required. An augmented-system multiplicity is not automatically a principal-source order. Radical sources retain unknown multiplicity: sqrt(z) has a located root at zero, without an asserted holomorphic order. Empty complete root sets have both counts zero. Accepted points retain algroots' IsolatedRootCertificate and its augmented-system data separately from source-order claims.

## Replay and trust boundary

The immutable proof binds the original expression/srepr, coordinate assumptions, rectangle, domain, raw condition, augmented system, RUR, all decisions and local certificates. Replay rebuilds backend algebraization/exhaustive enumeration, checks source filters and verifies accepted certificates. Altered, omitted or duplicate candidates, root lists, counts, sources, restrictions and fake self-attesting certificates are rejected. The funcprops proposing entry point is not called during replay.

This is **declared exact-backend replay**, not an independent native interval kernel. The inventory labels the proof `backend-adapter`, with replay mode `algroots-exact-backend-replay`. ReplayStatus retains `factory_replay=True` to make that distinction visible, while using common complete/local/unsupported/rejected outcomes. SymPy arithmetic, algroots enumeration/certification and declared equality oracles remain trusted. Backend recomputation is not formal verification.

## Limits

The default auxiliary cap is 8 (configurable from 0 to 16), and the quotient/degree bound cap is 256 (configurable from 1 to 256). A raw operation cap of 100 and scoped source/augmented Bezout bounds decline larger work before enumeration. These are not wall-time guarantees. Replay supports wall budgets; algebraic enumeration has no query checkpoint/resume interface.

Identically zero or other positive-dimensional systems remain incomplete here. Arbitrary free parameters, Piecewise systems, chart gluing and general transcendental isolation are outside this adapter. Exact enumeration may also be expensive or unsupported over particular coefficient fields.

Native transcendental isolation, subdivision, refinement and conditional completion have separate [contracts](native-complex-isolation.md).
