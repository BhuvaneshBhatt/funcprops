# Differential proofs and transformation geometry

Derivative identities are useful for composition rules, curvature and local coordinate changes. They have two separate obligations: the formulas must differentiate the supplied source correctly, and a consuming theorem must establish the required source domain and regularity. A symmetric matrix is not evidence that it is the Hessian of a particular expression.

## Formal derivative transport

`registry_gradient`, `registry_hessian`, `registry_derivative` and `registry_chain_rule` construct formal differentiation records from registered outer derivative rules and symbolic inner derivatives. Their direct `verify` methods reconstruct and bind the source, positions, formulas, guards and nested evidence. Multivariable records retain the requested derivative order in `second_order`. Coordinates and finite constants have correctly sized gradient, Jacobian and Hessian matrices.

The check uses the current default registry, or an explicitly supplied trusted registry through `proof.verify(registry=registry)`. Custom derivative declarations are mathematical premises supplied by that registry; replay checks their application and transport. It does not independently prove arbitrary user-supplied axioms. These records currently use their direct checkers and do not have adapters in the unified `verify_certificate` registry.

Recorded outer-rule guards do not constitute an exhaustive domain or branch-regularity proof for every inner expression. Establish those premises for the requested set before using a formal derivative identity in an analytic conclusion. Differentiation of held logarithms uses the explicit logarithm quotient, including its base factor, at every order.

```python
import sympy as sp
import funcprops as fp

x = sp.Symbol("x", real=True)
source = sp.erf(sp.log(x, 2, evaluate=False), evaluate=False)
proof = fp.registry_chain_rule(source, (x,), second_order=True)
assert proof.complete and proof.verify()
assert proof.hessian[0, 0].subs(x, 1) == -2 / (sp.sqrt(sp.pi) * sp.log(2))

axis = fp.registry_chain_rule(x, (x,), second_order=True)
assert axis.gradient == sp.ImmutableMatrix([1])
assert axis.hessian == sp.zeros(1)
```

## Jacobian nonvanishing and local geometry

`determinant_nonvanishing` binds the original map, coordinates, requested domain and assumptions to its result. The supported proof requires a real C1 map on nonempty, resolved input support before a nonzero determinant can establish a positive result. A held source hole cannot disappear because differentiation cancels a factor. Infinite and undefined sources, incompatible intrinsic coordinate assumptions and unresolved regularity yield `UNKNOWN`. Empty support also yields `UNKNOWN` under this interface; no negative witness is inferred there.

```python
held = sp.Mul(x, x, sp.Pow(x, -1, evaluate=False), evaluate=False)
assert fp.determinant_nonvanishing(held, x) is fp.TruthValue.UNKNOWN
safe = fp.determinant_nonvanishing(1 / x, x, domain=sp.Interval(1, 2), return_result=True)
assert safe.classification is fp.TruthValue.TRUE and safe.verify()
assert safe.expressions == (1 / x,)
```

`local_invertibility` and `change_of_variables` use the same bound facts. A failed or unresolved premise does not prove that every possible topological inverse is absent. These results remain local; global injectivity and coverage are separate questions.

Bounded scalar sign rules can prove determinant nonvanishing before a general zero query. Both these rules and the fallback bind supplied assumptions; coordinate-only contradictions leave the support unresolved or empty and return UNKNOWN. See [specialized property rules](guides/fast-rules.md) for the exact sign and box-Hessian scopes.

See the [capability matrix](capabilities.md), [result contracts](reference/result-contracts.md) and [differential regression tests](../tests/test_differential_soundness.py).
