"""Canonical examples shared by the property reference, tests, and tutorial.

The examples in this module are deliberately small and deterministic.  They are
not a second test suite: each example illustrates public API behavior and is
executed by the specification tests so documentation cannot drift from code.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyExample:
    """One documented public-API example and its executable expectation."""

    example_id: str
    property_name: str
    title: str
    code: str
    check: str
    expected: str
    application: str


EXAMPLES = (
    PropertyExample(
        "domain-radical-pole",
        "function_domain",
        "Radical with an excluded pole",
        "result = fp.function_domain(sp.sqrt(x - 1) / (x - 2), x)",
        "sp.simplify(result ^ ((x >= 1) & sp.Ne(x, 2))) is sp.false",
        "``(x >= 1) & Ne(x, 2)``",
        "Validate the admissible input region before symbolic optimization or plotting.",
    ),
    PropertyExample(
        "range-restricted-quadratic",
        "function_range",
        "Range on a restricted interval",
        "result = fp.function_range(x**2, x, y, constraints=sp.And(x >= -2, x <= 3))",
        "sp.simplify(result ^ ((y >= 0) & (y <= 9))) is sp.false",
        "``(y >= 0) & (y <= 9)``",
        "Derive certified output bounds for downstream constraints.",
    ),
    PropertyExample(
        "sign-positive",
        "function_sign",
        "Strict positivity",
        "result = fp.function_sign(x**2 + 1, x)",
        "result is fp.Sign.POSITIVE",
        "``Sign.POSITIVE``",
        "Prove denominator positivity or inequality preconditions without sampling.",
    ),
    PropertyExample(
        "complex-zeros-exp",
        "function_complex_zeros",
        "Certified complex zero in a rectangle",
        "z = sp.symbols('z'); result = fp.function_complex_zeros(sp.exp(z) - 1, z, rectangle=(-1-sp.I, 1+sp.I), return_result=True)",
        "result.complete is True and result.total_count == 1 and len(result.rectangles) == 1",
        "one certified zero in the rectangle",
        "Certify contour root counts before complex continuation, inversion, or spectral calculations.",
    ),
    PropertyExample(
        "zeros-polynomial",
        "function_zeros",
        "Exact real zeros",
        "result = fp.function_zeros((x - 1) * (x + 2), x)",
        "result == sp.FiniteSet(-2, 1)",
        "``{-2, 1}``",
        "Locate exact roots used for sign partitions and critical-event analysis.",
    ),
    PropertyExample(
        "boundedness-sine",
        "function_boundedness",
        "A globally bounded function",
        "result = fp.function_boundedness(sp.sin(x), x)",
        "result is fp.Boundedness.BOUNDED",
        "``Boundedness.BOUNDED``",
        "Establish stability envelopes and safe numerical search regions.",
    ),
    PropertyExample(
        "monotonicity-exponential",
        "function_monotonicity",
        "Strict increase",
        "result = fp.function_monotonicity(sp.exp(x), x)",
        "result is fp.Monotonicity.STRICTLY_INCREASING",
        "``Monotonicity.STRICTLY_INCREASING``",
        "Certify uniqueness of inverse values and one-dimensional optimization behavior.",
    ),
    PropertyExample(
        "convexity-quadratic",
        "function_convexity",
        "Strong convexity",
        "result = fp.function_convexity(x**2, x)",
        "result is fp.Convexity.STRONGLY_CONVEX",
        "``Convexity.STRONGLY_CONVEX``",
        "Guarantee uniqueness and conditioning properties in optimization models.",
    ),
    PropertyExample(
        "complete-monotonicity-mittag-leffler",
        "function_complete_monotonicity",
        "Mittag-Leffler complete monotonicity",
        "alpha = sp.symbols('alpha', positive=True); t = sp.symbols('t', nonnegative=True); result = fp.function_complete_monotonicity(fp.MittagLefflerE(alpha, -t), t, domain=t >= 0, assumptions=alpha <= 1)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE`` for ``0 < alpha <= 1``",
        "Certify Laplace-transform and survival-kernel structure in fractional probability models.",
    ),
    PropertyExample(
        "differentiability-absolute",
        "function_differentiability",
        "A corner at the origin",
        "result = fp.function_differentiability(sp.Abs(x), x)",
        "result is fp.Differentiability.NOT_DIFFERENTIABLE",
        "``Differentiability.NOT_DIFFERENTIABLE``",
        "Check whether derivative-based solvers are valid on an entire domain.",
    ),
    PropertyExample(
        "smoothness-exponential",
        "function_smoothness",
        "Smooth entire function",
        "result = fp.function_smoothness(sp.exp(x), x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Verify regularity assumptions required by approximation and differential methods.",
    ),
    PropertyExample(
        "injective-exponential",
        "function_injective",
        "Injective exponential",
        "result = fp.function_injective(sp.exp(x), x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Establish whether a symbolic inverse is single-valued on the chosen domain.",
    ),
    PropertyExample(
        "surjective-cubic",
        "function_surjective",
        "A surjection onto the reals",
        "result = fp.function_surjective(x**3, x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Verify that every target value in a codomain is attainable.",
    ),
    PropertyExample(
        "bijective-cubic",
        "function_bijective",
        "A real bijection",
        "result = fp.function_bijective(x**3, x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Certify existence of a globally single-valued inverse between two domains.",
    ),
    PropertyExample(
        "oscillation-sine",
        "function_oscillation",
        "Persistent oscillation",
        "result = fp.function_oscillation(sp.sin(x), x)",
        "result is fp.Oscillation.OSCILLATORY",
        "``Oscillation.OSCILLATORY``",
        "Detect repeated sign/turning behavior relevant to asymptotics and root searches.",
    ),
    PropertyExample(
        "periodicity-scaled-sine",
        "function_periodicity",
        "Scaled periodic function",
        "result = fp.function_periodicity(sp.sin(3*x), x, return_result=True)",
        "result.classification is fp.Periodicity.PERIODIC and sp.simplify(result.period - 2*sp.pi/3) == 0",
        "periodic with period ``2*pi/3``",
        "Reduce analysis or integration to a fundamental period.",
    ),
    PropertyExample(
        "symmetry-cosine",
        "function_symmetry",
        "Even symmetry",
        "result = fp.function_symmetry(sp.cos(x), x)",
        "result is fp.Symmetry.EVEN",
        "``Symmetry.EVEN``",
        "Cut numerical or symbolic work in half on symmetric domains.",
    ),
    PropertyExample(
        "homogeneity-quadratic",
        "function_homogeneity",
        "Homogeneous quadratic form",
        "result = fp.function_homogeneity(x**2 + y**2, (x, y), return_result=True)",
        "result.classification is fp.Homogeneity.HOMOGENEOUS and result.degree == 2",
        "homogeneous of degree ``2``",
        "Exploit scaling laws in dimensional analysis and optimization.",
    ),
    PropertyExample(
        "analytic-exponential",
        "function_analytic",
        "Entire real restriction",
        "result = fp.function_analytic(sp.exp(x), x)",
        "result is fp.Analyticity.ANALYTIC",
        "``Analyticity.ANALYTIC``",
        "Justify convergent local power-series methods and analytic continuation steps.",
    ),
    PropertyExample(
        "continuous-absolute",
        "function_continuous",
        "Continuous but nonsmooth",
        "result = fp.function_continuous(sp.Abs(x), x)",
        "result is fp.Continuity.CONTINUOUS",
        "``Continuity.CONTINUOUS``",
        "Verify hypotheses of existence theorems and interval methods.",
    ),
    PropertyExample(
        "discontinuities-piecewise",
        "function_discontinuities",
        "Jump discontinuity",
        "f = sp.Piecewise((0, x < 0), (1, True)); result = fp.function_discontinuities(f, x)",
        "result == sp.Eq(x, 0)",
        "a discontinuity at ``x = 0``",
        "Split quadrature, plotting, and approximation domains at genuine discontinuities.",
    ),
    PropertyExample(
        "meromorphic-rational",
        "function_meromorphic",
        "Rational meromorphic function",
        "result = fp.function_meromorphic(1/x, x)",
        "result is fp.Meromorphicity.MEROMORPHIC",
        "``Meromorphicity.MEROMORPHIC``",
        "Determine whether residue and pole-based complex-analysis techniques apply.",
    ),
    PropertyExample(
        "poles-rational",
        "function_poles",
        "Simple pole",
        "result = fp.function_poles(1/x, x)",
        "result == [(sp.Integer(0), 1)]",
        "one simple pole at ``x = 0``",
        "Locate poles for contour deformation, residues, and singular quadrature.",
    ),
    PropertyExample(
        "singularities-rational",
        "function_singularities",
        "Boolean singularity locus",
        "result = fp.function_singularities(1/x, x)",
        "result == sp.Eq(x, 0)",
        "the singular locus ``x = 0``",
        "Obtain one composable Boolean locus for analytic obstructions before downstream analysis.",
    ),
    PropertyExample(
        "singularity-analysis-rational",
        "function_singularity_analysis",
        "Detailed singularity analysis",
        "result = fp.function_singularity_analysis(1/x, x)",
        "result.complete is True and len(result.poles) == 1 and result.unknown_heads == ()",
        "a complete analysis with one pole",
        "Inspect completeness and provenance when a downstream proof requires certified singularity coverage.",
    ),
    PropertyExample(
        "branchpoints-log",
        "function_branchpoints",
        "Logarithmic branch point",
        "result = fp.function_branchpoints(sp.log(x), x)",
        "result == sp.Eq(x, 0)",
        "a branch point at ``x = 0``",
        "Identify non-isolated analytic structure relevant to continuation and contour choices.",
    ),
    PropertyExample(
        "branchcuts-log",
        "function_branchcuts",
        "Principal logarithm cut",
        "result = fp.function_branchcuts(sp.log(x), x)",
        "result == (x < 0,)",
        "``(x < 0,)``",
        "Avoid crossing branch cuts in symbolic transformations and complex numerical paths.",
    ),
    PropertyExample(
        "boundary-quadratic",
        "function_boundary_behavior",
        "Quadratic escape limits",
        "result = fp.function_boundary_behavior(x**2, x)",
        "result.complete is True and all(item.value is sp.oo for item in result.limits)",
        "both real escape limits are ``+oo``",
        "Certify endpoint escape behavior before coercivity or attainment reasoning.",
    ),
    PropertyExample(
        "level-bounded-quartic",
        "function_level_boundedness",
        "Coercive quartic",
        "result = fp.function_level_boundedness(x**4 - x, x)",
        "result is fp.TruthValue.TRUE",
        "a verified level-boundedness certificate",
        "Prove bounded sublevel sets without numerical optimization.",
    ),
    PropertyExample(
        "mode-gaussian-log-density",
        "function_mode_existence",
        "Structural maximum existence",
        "result = fp.function_mode_existence(-x**2/2, x, sense='max')",
        "result is fp.TruthValue.TRUE",
        "a verified global-maximum existence certificate",
        "Establish existence of a mode from continuity, closedness, and coercivity.",
    ),
    PropertyExample(
        "geometry-quadratic",
        "function_geometry",
        "Combined function geometry",
        "result = fp.function_geometry(x**2, x)",
        "result.c2 is fp.TruthValue.TRUE and result.minimum_exists.exists is True",
        "a combined regularity, singularity, convexity, and attainment summary",
        "Collect structural facts for optimization and probability workflows in one query.",
    ),
    PropertyExample(
        "jacobian-affine",
        "function_jacobian",
        "Exact affine Jacobian",
        "result = fp.function_jacobian((2*x + y, x - y), (x, y))",
        "result == sp.ImmutableMatrix([[2, 1], [1, -1]])",
        "the exact matrix ``[[2, 1], [1, -1]]``",
        "Compute a replayable derivative matrix for a coordinate transformation.",
    ),
    PropertyExample(
        "determinant-nonvanishing-affine",
        "function_determinant_nonvanishing",
        "Nonvanishing Jacobian determinant",
        "result = fp.function_determinant_nonvanishing((2*x + y, x - y), (x, y))",
        "result is fp.TruthValue.TRUE",
        "a verified nonvanishing determinant ``-3``",
        "Check the inverse-function-theorem rank hypothesis on an entire domain.",
    ),
    PropertyExample(
        "local-invertibility-affine",
        "function_local_invertibility",
        "Local invertibility",
        "result = fp.function_local_invertibility((2*x + y, x - y), (x, y))",
        "result is fp.TruthValue.TRUE",
        "a verified local-invertibility certificate",
        "Certify local coordinate validity without claiming global injectivity.",
    ),
    PropertyExample(
        "change-variables-affine",
        "function_change_of_variables",
        "Change-of-variables volume factor",
        "result = fp.function_change_of_variables((2*x + y, x - y), (x, y))",
        "result.classification is fp.TruthValue.TRUE and result.volume_factor == 3",
        "the certified factor ``Abs(det J) = 3``",
        "Carry the correct local measure factor into transformed integrals or densities.",
    ),
    PropertyExample(
        "transformation-geometry-affine",
        "function_transformation_geometry",
        "Combined transformation geometry",
        "result = fp.function_transformation_geometry((x + y, x - y), (x, y))",
        "result.determinant == -2 and result.local_invertibility.classification is fp.TruthValue.TRUE",
        "a combined Jacobian, determinant, local-invertibility, and change-of-variables summary",
        "Inspect all transformation certificates with one query.",
    ),
)


@dataclass(frozen=True)
class StatisticalSpecialFunctionExample:
    """One executable example for the statistical special-function layer."""

    example_id: str
    title: str
    code: str
    check: str
    expected: str
    application: str


STATISTICAL_SPECIAL_FUNCTION_EXAMPLES = (
    StatisticalSpecialFunctionExample(
        "regularized-gamma-cdf",
        "Regularized gamma CDF geometry",
        "a = sp.symbols('a', positive=True); result = fp.function_monotonicity(fp.RegularizedGammaP(a, x), x, domain=x > 0)",
        "result is fp.Monotonicity.STRICTLY_INCREASING",
        "strict increase on ``x > 0`` for ``a > 0``",
        "Reason symbolically about Gamma-family CDFs without numerical sampling.",
    ),
    StatisticalSpecialFunctionExample(
        "owen-t-derivative",
        "Owen T derivative",
        "h, a = sp.symbols('h a', real=True); result = sp.diff(fp.OwenT(h, a), a)",
        "result == sp.exp(-h**2 * (1 + a**2) / 2) / (2 * sp.pi * (1 + a**2))",
        "the exact positive derivative with respect to the second argument",
        "Certify monotonicity used in skew-normal and Gaussian probability calculations.",
    ),
    StatisticalSpecialFunctionExample(
        "marcum-q-threshold",
        "Generalized Marcum Q threshold monotonicity",
        "m, a, b = sp.symbols('m a b', positive=True); result = fp.function_monotonicity(sp.marcumq(m, a, b), b, domain=b > 0)",
        "result is fp.Monotonicity.STRICTLY_DECREASING",
        "strict decrease in the positive threshold",
        "Analyze noncentral-tail probabilities and detection thresholds structurally.",
    ),
    StatisticalSpecialFunctionExample(
        "mittag-leffler-complete-monotonicity",
        "Mittag-Leffler complete monotonicity",
        "alpha = sp.symbols('alpha', positive=True); t = sp.symbols('t', nonnegative=True); result = fp.function_complete_monotonicity(fp.MittagLefflerE(alpha, -t), t, domain=t >= 0, assumptions=alpha <= 1)",
        "result is fp.TruthValue.TRUE",
        "complete monotonicity for ``0 < alpha <= 1``",
        "Certify Laplace-transform geometry in fractional stochastic and reliability models.",
    ),
    StatisticalSpecialFunctionExample(
        "bessel-ratio-geometry",
        "Modified-Bessel ratio monotonicity",
        "nu = sp.symbols('nu', nonnegative=True); t = sp.symbols('t', positive=True); ratio = sp.besseli(nu + 1, t) / sp.besseli(nu, t); result = fp.function_monotonicity(ratio, t, domain=t > 0)",
        "result is fp.Monotonicity.STRICTLY_INCREASING",
        "strict increase for nonnegative ``nu`` on ``t > 0``",
        "Support directional-statistics and noncentral-distribution parameter geometry.",
    ),
)


def examples_for(property_name: str) -> tuple[PropertyExample, ...]:
    """Return the canonical examples for one public property query."""

    return tuple(case for case in EXAMPLES if case.property_name == property_name)
