"""Generic congruence and local orders at a non-rational isolated root."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
g = sp.exp(z) - 2
rectangle = (sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100)
policy = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=192
)
base = fp.certify_analytic_contour(g, z, *rectangle, policy=policy)
f = sp.sin(g) + z * (sp.exp(g) - 1)
h = sp.sin(g) ** 2 + z * (sp.exp(g) - 1) ** 2
common = fp.certify_common_zero((f, h), base, max_order=3, policy=policy)
assert common.verify() and common.common_zero_status is fp.TruthValue.TRUE
assert common.orders_complete and common.multiplicities == (1, 2)
assert not common.coverage_complete and not common.complete
assert fp.verify_certificate(common)
# Exact local order does not exclude other zeros elsewhere in the rectangle.
