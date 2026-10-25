"""Check local holomorphic recipes and every required overlap."""

# %% Select local solutions
#| Give formulas for (w-z)**2=z on a rectangle away from zero. Logarithm sheets 0 and 2 produce the same selected square root.
from dataclasses import replace

import sympy as sp

import funcprops as fp

z, w, u = sp.symbols("z w u")
rectangle = fp.CoverageRectangle(1 - sp.I / 4, 2 + sp.I / 4)
logarithm = fp.certify_log_atlas(z, z, (rectangle,)).charts[0]
relation = (w - z) ** 2 - z
left = fp.certify_branch_chart(
    relation, z, w, rectangle, z + sp.exp(u / 2), logarithms=((u, logarithm),)
)
right = fp.certify_branch_chart(
    relation,
    z,
    w,
    rectangle,
    z + sp.exp(u / 2),
    logarithms=((u, replace(logarithm, sheet=2)),),
)
glued = fp.glue_branch_charts((left, right))
assert glued.verify() and glued.coverage_complete and glued.gluing_complete

# %% Interpret disagreement correctly
#| Sheet 1 selects the opposite square root. The supplied charts disagree. This does not prove that every possible choice of local branches fails to glue on this rectangle.
opposite = replace(right, logarithms=((u, replace(logarithm, sheet=1)),))
disagreement = fp.glue_branch_charts((left, opposite))
assert disagreement.verify() and not disagreement.complete and disagreement.obstructions

# %% An anchor alone is insufficient
#| Two solutions of an implicit equation can meet at an isolated point. The formulas z and -z both satisfy w**2=z**2 and agree at zero, yet their derivatives differ, so the gluing checker keeps this overlap unresolved.
box = fp.CoverageRectangle(-1 - sp.I, 1 + sp.I)
a = fp.certify_branch_chart(w * w - z * z, z, w, box, z)
b = fp.certify_branch_chart(w * w - z * z, z, w, box, -z)
crossing = fp.glue_branch_charts((a, b))
assert crossing.verify() and not crossing.complete and crossing.unresolved_overlaps
