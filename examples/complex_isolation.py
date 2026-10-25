"""Coverage, individual isolation and requested accuracy are separate claims."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
sine = fp.certify_complex_isolation(sp.sin(z), z, -4 - sp.I, 4 + sp.I)
assert sine.verify() and sine.complete and sine.root_count == 3
nonreal = fp.complex_zeros(
    sp.exp(z) + 1, z, rectangle=(-1 - 4 * sp.I, 1 + 4 * sp.I), return_result=True
)
assert nonreal.verify() and nonreal.root_count == nonreal.multiplicity_count == 2
cluster = fp.certify_complex_isolation(
    sp.sin(z) ** 2,
    z,
    -1 - sp.I,
    1 + sp.I,
    policy=fp.EnclosurePolicy(max_depth=0),
    use_multiple=False,
)
assert cluster.verify() and cluster.coverage_complete and not cluster.complete
assert cluster.multiplicity_count == 2 and cluster.root_count is None
assert not cluster.isolation_complete and not cluster.accuracy_complete
accurate = fp.certify_complex_isolation(
    sp.exp(z) - 1,
    z,
    -sp.Rational(1, 10) - sp.I / 10,
    sp.Rational(1, 10) + sp.I / 10,
    max_box_diameter=sp.Rational(1, 1000),
    policy=fp.EnclosurePolicy(max_depth=32, max_cells=1024),
)
assert accurate.verify() and accurate.complete and accurate.accuracy_complete
