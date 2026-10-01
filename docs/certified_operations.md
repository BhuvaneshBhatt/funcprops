# Certified high-level operations

Funcprops exposes replayable operations that consume the package's property,
singularity, contour, and exactness machinery
a proof.

## Package boundary

Certified limit computation belongs to the `asymptotic` package. Funcprops supplies
property facts, exactness predicates, and `ParametricContour` geometry that asymptotic
can consume for one-sided and path limits. This keeps proof-engine ownership and limit
status semantics in one package.

## Inverses and equations

`fp.inverse()` returns a symbolic inverse only when the implemented injectivity check
and composition replay support it. `fp.solve()` returns SymPy's exact solution set;
`EquationSolutionCertificate.complete` is false for unresolved `ConditionSet`s.

## Laurent data, residues, and singularities

`fp.laurent_series()`, `fp.residue()`, and `fp.classify_singularity()` provide
replayable local complex-analysis results. Classification distinguishes regular
points, zeros, poles, explicit logarithmic/algebraic branch points, and supported
essential singularities such as `exp(1/z)`.

## Argument principle and winding

`fp.winding_number(contour, point)` preserves the supplied parameter orientation and
multiple winding. Exact exponential-circle phase parameterizations are certified from
their phase increment. `fp.argument_principle()` counts the exact rational divisor by
oriented winding, avoiding principal-antiderivative branch loss.

## Deformation, continuation, and monodromy

`fp.homotopic()` certifies based closed-loop homotopy in a finitely punctured
plane.  For zero or one puncture it uses the complete winding-number invariant.
For two or more punctures it chooses a certified system of pairwise-disjoint parallel
cuts from the punctures to infinity, proves all contour/cut intersections exact and
transverse, records their ordered signed generator crossings, and freely reduces the
resulting word in the free group `pi_1(C \ P)`.  Equality of reduced words is the
nonabelian homotopy certificate; matching winding vectors alone are never promoted
to a proof.  Symbolic contours whose complete crossing geometry cannot be solved
exactly return an inconclusive result.

`fp.deform_contour()` can therefore certify rational meromorphic deformations around
multiple poles whenever this free-word geometry is certified. `fp.analytic_continue()` / `fp.monodromy()` track explicit logarithms and
rational powers around certified closed contours; for example a positive loop around
zero sends `log(z)` to `log(z)+2*pi*I` and `sqrt(z)` to `-sqrt(z)`.

All certificate objects in this subsystem participate in `fp.verify_certificate()`.
Unsupported geometry returns an inconclusive result.
