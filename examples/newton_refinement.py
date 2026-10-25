"""Refinement keeps the child, all four complements, and conserved counts."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
radius = sp.Rational(1, 10)
parent = fp.certify_analytic_contour(
    sp.exp(z) - 1, z, -radius - sp.I * radius, radius + sp.I * radius
)
assert parent.verify() and parent.zero_count == 1
refined = fp.certify_complex_refinement(parent)
assert refined is not None and refined.verify() and fp.verify_certificate(refined)
assert len(refined.regions) == 5
assert sum(c.zero_count for c in refined.regions) == 1
