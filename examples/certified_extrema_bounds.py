"""Certified bounds with an implicit stationary coordinate."""

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
policy = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=160, max_depth=7
)
proof = fp.certify_extrema_bounds(
    sp.exp(x) + x * x,
    x,
    sp.Interval(-1, 1),
    tolerance=sp.Rational(1, 10000),
    policy=policy,
)
assert proof.verify() and proof.complete
assert proof.coverage_complete and proof.accuracy_complete
assert proof.minimum_bounds[1] - proof.minimum_bounds[0] <= proof.tolerance
assert proof.maximum_bounds[1] - proof.maximum_bounds[0] <= proof.tolerance
assert not proof.exact_complete
assert fp.verify_certificate(proof)
