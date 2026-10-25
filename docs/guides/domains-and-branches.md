# Source domains, assumptions and branches

SymPy may simplify x/x to 1 before funcprops receives it. Retain source syntax with evaluate=False on the relevant Mul/Pow nodes, or supply an explicit domain restriction where the public API accepts one. Holding an outer node cannot undo simplification that already happened in its arguments. See the executable [restricted-domain tutorial](../tutorials/restricted-domains.md).

Funcprops tracks raw source restrictions before normalization. Calculation formulas can simplify; original denominator holes and natural-domain guards must remain in theorem contexts and consumer conclusions. Requested and effective domains differ when natural-domain intersection removes points.

Assumptions are hypotheses, not sampled parameter values. Guarded answers retain which case each conclusion belongs to. Specialization must retain the parent's premises and reject unsupported substitutions. See [guarded and Piecewise results](../tutorials/guarded-piecewise.md).

Principal powers and logarithms keep their branch conventions. An expression that has a complex intermediate value cannot be analyzed by changing it to a real-root convention. Explicit LocalBranchContext values select supported local germs; they do not glue a global multi-chart contour or restore a source hole. See [local branches](../tutorials/local-branches.md).

Real and complex coordinate policies differ. Native complex isolation uses an unconstrained commutative Symbol and rational rectangles. The algebraic adapter has separate restriction support. Unsupported domains, guards or branches keep results partial or cause the documented decline; see [result contracts](../reference/result-contracts.md).

Source-bound domain records reuse structural real-domain guards for finite constant real powers. Positive nonrational exponents retain a zero base, while negative exponents exclude it. A positive symbolic exponent can prove coverage of a requested nonnegative set without claiming its entire natural domain. Piecewise records retain both guard-definition holes and active branch holes; later branches cannot fill a point at which an evaluated guard was undefined. Unsupported guard languages remain unresolved.

Held two-argument logarithms use `log(argument)/log(base)` for continuity and derivative calculations after checking the original source domain. Shared domain caches include the raw expression, coordinate assumptions and requested restriction. Equal effective sets with different requested restrictions still have distinct provenance.

Reusable monotonic partitions bind the original expression, coordinate and domain. Consumers compare supplied cell, derivative and endpoint data with the cached source construction; a foreign or altered partition is recomputed or declined. A supplied partition can define the scope of the direct partition-image and inverse helpers when their domain argument is omitted. An explicit domain always controls the query. This replay route uses the partition constructor; it is separate from the independent coverage checkers.

Nested Piecewise expressions use branch formulas and owned value/slope seams for scalar order, curvature and variation. Derivatives of the individual formulas do not describe jumps. An unresolved seam cannot be bypassed by a derivative or Hessian rule. Multivariate separable expressions can reuse scalar conclusions; coupled Piecewise curvature remains unresolved. Supported monotonic partitions now assemble branch and seam evidence, retain jumps and singleton values, and distinguish cell coverage from global order.

The exact symbolic-extrema helper requires the entire requested interval to lie in the original source domain and verifies interior regularity before using a finite list of derivative zeros. A pole inside a requested interval prevents that route. Split the domain into supported components or use the root-coverage and extrema-bound interfaces for their documented scopes.
