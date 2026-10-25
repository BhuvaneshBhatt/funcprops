"""Exact backend enumeration preserves principal branches and source holes."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
rectangle = (-2 - 2 * sp.I, 2 + 2 * sp.I)
r = fp.complex_zeros((z - 1) ** 3, z, rectangle=rectangle, return_result=True)
assert r.verify() and r.complete and r.algebraic_certificate is not None
assert r.root_count == 1 and r.total_count == 3
held = sp.Mul(z**2, sp.Pow(z, -1, evaluate=False), evaluate=False)
hole = fp.isolate_complex_roots(held, z, rectangle)
assert hole.verify() and hole.complete and hole.roots == () and hole.total_count == 0
radical = fp.certify_algebraic_complex_roots(sp.sqrt(z), z, rectangle)
assert radical.verify() and radical.complete and radical.roots == (0,)
assert radical.root_count == 1 and radical.multiplicity_count is None
