"""Check logarithm transitions and preserve a global obstruction."""

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
regions = (
    fp.CoverageRectangle(-2 - sp.I / 4, 2 - sp.I / 8),
    fp.CoverageRectangle(-2 + sp.I / 8, 2 + sp.I / 4),
    fp.CoverageRectangle(-2 - sp.I / 4, -sp.Rational(7, 4) + sp.I / 4),
    fp.CoverageRectangle(sp.Rational(7, 4) - sp.I / 4, 2 + sp.I / 4),
)
policy = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=160, max_depth=8
)
logarithm = fp.certify_log_atlas(z, z, regions, policy=policy)
assert logarithm.verify() and logarithm.coverage_complete
assert logarithm.obstructions and not logarithm.complete
square_log = fp.certify_log_atlas(z * z, z, regions, policy=policy)
power = fp.GluedPowerProof(square_log, sp.S.Half)
assert power.verify() and power.complete
assert fp.verify_certificate(power)
# This selects a glued square root; it does not redefine principal sqrt(z**2).
