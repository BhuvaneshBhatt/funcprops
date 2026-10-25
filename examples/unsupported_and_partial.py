"""Unproved boundaries and unsupported grammar retain honest incomplete results."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
seed = fp.certify_complex_isolation(
    sp.sin(z), z, -4 - sp.I, 4 + sp.I, policy=fp.EnclosurePolicy(max_cells=0)
)
assert seed.verify() and seed.unresolved and not seed.coverage_complete
assert seed.total_count is None and not seed.complete
boundary = fp.certify_complex_isolation(
    sp.exp(z) - 1,
    z,
    -sp.I,
    1 + sp.I,
    policy=fp.EnclosurePolicy(max_cells=32, max_depth=1),
    max_boundary_depth=1,
)
assert boundary.verify() and not boundary.complete and boundary.total_count is None
unsupported = fp.certify_complex_isolation(sp.log(z), z, -1 - sp.I, 1 + sp.I)
assert not unsupported.complete
