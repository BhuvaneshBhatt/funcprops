"""Keep parameter strata and singleton Piecewise values in downstream proofs."""

import sympy as sp

import funcprops as fp

x, a, b = sp.symbols("x a b", real=True)
cases = fp.solve(a * x + b, x, domain=sp.S.Reals, guarded=True, return_certificate=True)
assert cases.verify() and cases.complete and len(cases.cases) == 3
assert cases.specialize(sp.Ne(a, 0)).root_count == 1
assert (
    fp.monotonicity(a * x, x, assumptions=a > 0) is fp.Monotonicity.STRICTLY_INCREASING
)
f = sp.Piecewise((x, x < 0), (100, sp.Eq(x, 0)), (x + 10, True))
proof = fp.certify_property_coverage(f, x, sp.Interval(-1, 1))
assert proof.verify() and proof.complete
assert proof.conclusion("maximum").value == (100, sp.FiniteSet(0))
image = proof.conclusion("range").value.doit()
assert image.contains(100) is sp.true and image.contains(0) is sp.false
