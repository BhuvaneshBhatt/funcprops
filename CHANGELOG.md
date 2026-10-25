# Changelog

## 0.4.0

### More reliable domains, ranges, and assumptions

- Fix "algebraization" transformations that could discard an input restriction, e.g. the range of `exp(x)` for `0 < x < 1` is now correctly restricted to `1 < y < E`. Open and closed endpoints, unbounded intervals, and disconnected domains receive more consistent treatment.
- Preserve excluded points through algebraic simplification. A held expression such as `x/x` still excludes zero, even when its computational formula simplifies to `1`. Related fixes cover logarithms, powers, radicals, and cancelled quotient factors.
- Improve checks on trig substitutions, compositions, and coefficient assumptions. A transformation that cannot preserve the original domain/branch now leaves that route unresolved.

### Stronger root isolation and pole accounting

- Add `algroots` backend for supported exact algebraic complex-root problems, retaining funcprops' original expression, domain, and branch restrictions.
- Add explicit root-coverage proofs: every region must contain certified roots or have a proof that no roots occur there.
- Expand real and complex isolation with selected multiple-root proofs, adaptive subdivision, bounded precision refinement, certified Newton refinement, and checkpoint/resume support
- Add joint zero-and-pole accounting for supported transcendental quotients. Common-zero and multiplicity proofs can distinguish poles from removable singularities while preserving holes in the original expression.

### Better regularity, curvature, and optimization

- Add exact optimal Lipschitz constants on finite domains, e.g. `x**2` on `{0, 1, 2}` has optimal constant `3`
- Improve Piecewise continuity, monotonic partitions, and total variation, including jumps and isolated point values
- Add proofs that disprove Lipschitz and uniform continuity across excluded seams.
- Expand guarded polynomial parity and periodicity reasoning, basic `Abs` homogenity rules, and real-coefficient checks for affine maps.
- Add stronger multivariable curvature tests. On the unit square, `exp(x*y) + 2*x**2 + 2*y**2` has certified strong-convexity modulus `4 - E`, exact interior Hessian witnesses can also disprove both convexity and concavity.
- Add certified lower and upper bounds for extrema, including supported problems whose critical points lack closed-form coordinates, and improve optimization over finite collections of domain components.

### Real algebraic coefficients, parameter families, and branch cancellations

- Add a bounded class of exact real algebraic coefficients, such as `sqrt(2)`, for selected domain, range, sign and shape queries.
- Add root-count geometry for supported polynomial parameter families, including repeated roots, degree changes, parameter assumptions.
- Recognize entire branch cancellations such as `cos(sqrt(z))` and `sin(sqrt(z))**2`. Analyticity, meromorphicity, domain, branch-point, and branch-cut helpers now share that conclusion.

### Documentation & testing

- Rework README
- Expand task-based tutorials, executable examples, notebooks, capability and limitation tables, troubleshooting, and API/proof-field references.
- Expand regression, adversarial, replay-mutation, cache-state, and installed-package tests. Local validation passed 12,810 source tests.

## 0.3.0

- Added certified real and complex zero isolation, root counting, indexed zeros, zero ordering, and interlacing.
- Added injectivity, surjectivity, bijectivity, periodicity, symmetry, homogeneity, boundedness, variation, integrability, smoothness, Hölder/Lipschitz, oscillation, and complete-monotonicity analysis.
- Added substantially stronger transcendental-function analysis, including exponential/Fourier forms, extrema, periodic structure, and analytic neighbourhoods.
- Added parameter-dependent analysis with conditional results, parameter stratification, and assumption reasoning.
- Added stronger semialgebraic analysis through the `semialg` package.
- Expanded monotonicity and convexity certification, including multivariate cases.
- Added multivariate function analysis with gradients, Hessians, Jacobians, singularity loci, and local invertibility.
- Added transformation geometry and property propagation through compositions and coordinate transformations.
- Expanded singularity, pole, discontinuity, analyticity, meromorphicity, domain, range, and branch-cut analysis.
- Added stronger piecewise-function and boundary/interface reasoning.
- Expanded special-function support, including Airy, Bessel, orthogonal-polynomial, and statistical-function families.
- Added proof certificates, provenance, certificate verification, proof caching, and cross-property consistency checks.
- Added extensive adversarial, metamorphic, parameter-specialization, rewrite-invariance, and mathematical soundness testing, and expanded the test suite to roughly 9,962 tests across 67 test modules.
- Expanded mathematical documentation, examples, certification conventions, and capability/limitation documentation.