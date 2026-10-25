"""Source zeros, extension zeros, poles and winding are different quantities."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
g = sp.exp(z) - 2
rectangle = (-1 - sp.I, 1 + sp.I)
policy = fp.EnclosurePolicy(max_cells=8192, max_depth=24, max_taylor_order=5)
held = sp.Mul(g**2, g, sp.Pow(g, -1, evaluate=False), evaluate=False)
hole = fp.certify_quotient_isolation(held, z, *rectangle, policy=policy)
assert hole.verify() and hole.complete and hole.total_count == 0
assert hole.proof.extension_zero_count == hole.proof.excluded_zero_multiplicity == 2
assert hole.proof.source.guards == (g,)
for denominator, poles in ((sp.sin(g), 0), (sp.sin(g) ** 2, 1)):
    q = fp.certify_quotient_isolation(g / denominator, z, *rectangle, policy=policy)
    assert q.verify() and q.complete and q.total_count == 0
    assert q.pole_multiplicity_count == poles
    assert q.proof.winding_count == -poles
