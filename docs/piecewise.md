# Certified Piecewise analysis

funcprops treats a finite `sympy.Piecewise` as an ordered decision list, not as independent overlapping conditions. `piecewise_decomposition(expr, var, domain)` turns the expression into effective, non-overlapping connected real branch cells. Each `PiecewiseBranch` records its original arm, effective condition, and domain.

Finite seams are represented by `PiecewiseBoundary`. Its `owner_branch` records which Piecewise arm supplies the value at the seam, independently of the branches that approach from the left and right. This matters for isolated override values.

`certify_piecewise_boundaries(...)` evaluates one-sided limits on the branch expressions themselves. It never asks SymPy to take a limit of the enclosing Piecewise expression. The resulting `PiecewiseBoundaryCertificate` records the selected value, one-sided limits, derivative-limit pairs, continuity, and the highest certified matching derivative order.

Property engines reuse ordinary branch analysis on those effective domains and then merge only after the required seam conditions are certified. Current merging covers sign, boundedness, zeros, range, continuity/discontinuities, differentiability/smoothness, monotonicity, and convexity. Unknown branch domains or unresolved seam comparisons remain unknown compatible.
