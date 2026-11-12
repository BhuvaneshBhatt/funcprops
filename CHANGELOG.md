# Changelog

## 0.5.0

### Real-Function Ranges

- New `real_images` subsystem for certified real-function range analysis, supporting exact images, partial inner and outer bounds.
- Add incremental range refinement with checkpoint/resume support, allowing unresolved critical-point isolation to continue under larger budgets.
- Improve range analysis over disconnected, open, closed, and unbounded domains, including handling of excluded points, endpoint attainment, and one-sided limits.
- Expand support for nonsmooth expressions, including selected piecewise functions, absolute values, and minimum/maximum constructions.

### Transcendental and Oscillatory Functions

- Add range methods for unbounded monotone and nonmonotone tails, combining derivative-sign proofs, asymptotic behavior, and bounded oscillatory remainders.
- Improve analysis of damped oscillations and functions with infinitely many critical points, including selected sinc-type expressions and oscillatory functions with unbounded amplitude.
- Add exact range proofs for selected incommensurate trig sums, using phase-density arguments while distinguishing attainable extrema from limiting values.
- Extend exact-image rules for elementary functions, including inverse trig and hyperbolic functions, quadratic transformations, and monotone compositions, as well as error functions.
- Improve periodic-function analysis by reducing supported infinite-domain range problems to certified fundamental-period calculations.

### Parameter-Dependent Analysis

- Add `analyze_parameter_range` and `parameter_range` for exact condition-dependent range analysis of supported polynomial families through degree-3.
- Account for parameter-dependent critical points, degree changes, endpoint inclusion, and transitions between distinct range configurations.
- Support selected compositions with invertible elementary functions, including exponential transformations of parametrised polynomials.
- Extend parametrised root-count analysis with strongly convex level-set witnesses, distinguishing zero, one, or two roots under certified conditions.

### Analysis APIs and Reusable Infrastructure

- Add `analyze_range`, `refine_range`, and `RangeAnalysis` for structured range computation, refinement, and verification.
- Introduce reusable interfaces for function-cell decomposition, domain-aware derivatives, numerical value enclosures, and tail-range bounds.
- Expand certificate metadata and verification contracts to support independent checking and integration with other symbolic math packages.
- Improve modular separation between function-property analysis, algebraic root isolation, and semialgebraic reasoning.

### Documentation & Testing

- Expand mathematical documentation with dedicated guides for real-image analysis, exact critical values, parameterized ranges, proof verification, and the new analysis interfaces.
- Add 27 test modules covering implicit critical roots, oscillatory ranges, parameter-dependent images, algebraic coefficient fields, domain restrictions, and certificate integrity.
- Strengthen adversarial and mutation testing to detect invalid certificates, incomplete root coverage, incorrect endpoint handling, and unsound transformations.

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
