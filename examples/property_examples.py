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
        "domain",
        "Radical with an excluded pole",
        "result = fp.domain(sp.sqrt(x - 1) / (x - 2), x)",
        "sp.simplify(result ^ ((x >= 1) & sp.Ne(x, 2))) is sp.false",
        "``(x >= 1) & Ne(x, 2)``",
        "Validate the admissible input region before symbolic optimization or plotting.",
    ),
    PropertyExample(
        "range-restricted-quadratic",
        "range",
        "Range on a restricted interval",
        "result = fp.range(x**2, x, y, constraints=sp.And(x >= -2, x <= 3))",
        "sp.simplify(result ^ ((y >= 0) & (y <= 9))) is sp.false",
        "``(y >= 0) & (y <= 9)``",
        "Derive certified output bounds for downstream constraints.",
    ),
    PropertyExample(
        "sign-positive",
        "sign",
        "Strict positivity",
        "result = fp.sign(x**2 + 1, x)",
        "result is fp.Sign.POSITIVE",
        "``Sign.POSITIVE``",
        "Prove denominator positivity or inequality preconditions without sampling.",
    ),
    PropertyExample(
        "complex-zeros-exp",
        "complex_zeros",
        "Certified complex zero in a rectangle",
        "z = sp.symbols('z'); result = fp.complex_zeros(sp.exp(z) - 1, z, rectangle=(-1-sp.I, 1+sp.I), return_result=True)",
        "result.complete is True and result.total_count == 1 and len(result.rectangles) == 1",
        "one certified zero in the rectangle",
        "Certify contour root counts before complex continuation, inversion, or spectral calculations.",
    ),
    PropertyExample(
        "zeros-polynomial",
        "zeros",
        "Exact real zeros",
        "result = fp.zeros((x - 1) * (x + 2), x)",
        "result == sp.FiniteSet(-2, 1)",
        "``{-2, 1}``",
        "Locate exact roots used for sign partitions and critical-event analysis.",
    ),
    PropertyExample(
        "boundedness-sine",
        "boundedness",
        "A globally bounded function",
        "result = fp.boundedness(sp.sin(x), x)",
        "result is fp.Boundedness.BOUNDED",
        "``Boundedness.BOUNDED``",
        "Establish stability envelopes and safe numerical search regions.",
    ),
    PropertyExample(
        "monotonicity-exponential",
        "monotonicity",
        "Strict increase",
        "result = fp.monotonicity(sp.exp(x), x)",
        "result is fp.Monotonicity.STRICTLY_INCREASING",
        "``Monotonicity.STRICTLY_INCREASING``",
        "Certify uniqueness of inverse values and one-dimensional optimization behavior.",
    ),
    PropertyExample(
        "convexity-quadratic",
        "convexity",
        "Strong convexity",
        "result = fp.convexity(x**2, x)",
        "result is fp.Convexity.STRONGLY_CONVEX",
        "``Convexity.STRONGLY_CONVEX``",
        "Guarantee uniqueness and conditioning properties in optimization models.",
    ),
    PropertyExample(
        "complete-monotonicity-mittag-leffler",
        "complete_monotonicity",
        "Mittag-Leffler complete monotonicity",
        "alpha = sp.symbols('alpha', positive=True); t = sp.symbols('t', nonnegative=True); result = fp.complete_monotonicity(fp.MittagLefflerE(alpha, -t), t, domain=t >= 0, assumptions=alpha <= 1)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE`` for ``0 < alpha <= 1``",
        "Certify Laplace-transform and survival-kernel structure in fractional probability models.",
    ),
    PropertyExample(
        "differentiability-absolute",
        "differentiability",
        "A corner at the origin",
        "result = fp.differentiability(sp.Abs(x), x)",
        "result is fp.Differentiability.NOT_DIFFERENTIABLE",
        "``Differentiability.NOT_DIFFERENTIABLE``",
        "Check whether derivative-based solvers are valid on an entire domain.",
    ),
    PropertyExample(
        "smoothness-exponential",
        "smoothness",
        "Smooth entire function",
        "result = fp.smoothness(sp.exp(x), x)",
        "result is sp.oo",
        "``oo`` (C-infinity)",
        "Verify regularity assumptions required by approximation and differential methods.",
    ),
    PropertyExample(
        "injective-exponential",
        "injective",
        "Injective exponential",
        "result = fp.injective(sp.exp(x), x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Establish whether a symbolic inverse is single-valued on the chosen domain.",
    ),
    PropertyExample(
        "surjective-cubic",
        "surjective",
        "A surjection onto the reals",
        "result = fp.surjective(x**3, x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Verify that every target value in a codomain is attainable.",
    ),
    PropertyExample(
        "bijective-cubic",
        "bijective",
        "A real bijection",
        "result = fp.bijective(x**3, x)",
        "result is fp.TruthValue.TRUE",
        "``TruthValue.TRUE``",
        "Certify existence of a globally single-valued inverse between two domains.",
    ),
    PropertyExample(
        "oscillation-sine",
        "oscillation",
        "Persistent oscillation",
        "result = fp.oscillation(sp.sin(x), x)",
        "result is fp.Oscillation.OSCILLATORY",
        "``Oscillation.OSCILLATORY``",
        "Detect repeated sign/turning behavior relevant to asymptotics and root searches.",
    ),
    PropertyExample(
        "periodicity-scaled-sine",
        "periodicity",
        "Scaled periodic function",
        "result = fp.periodicity(sp.sin(3*x), x, return_result=True)",
        "result.classification is fp.Periodicity.PERIODIC and sp.simplify(result.period - 2*sp.pi/3) == 0",
        "periodic with period ``2*pi/3``",
        "Reduce analysis or integration to a fundamental period.",
    ),
    PropertyExample(
        "symmetry-cosine",
        "symmetry",
        "Even symmetry",
        "result = fp.symmetry(sp.cos(x), x)",
        "result is fp.Symmetry.EVEN",
        "``Symmetry.EVEN``",
        "Cut numerical or symbolic work in half on symmetric domains.",
    ),
    PropertyExample(
        "homogeneity-quadratic",
        "homogeneity",
        "Homogeneous quadratic form",
        "result = fp.homogeneity(x**2 + y**2, (x, y), return_result=True)",
        "result.classification is fp.Homogeneity.HOMOGENEOUS and result.degree == 2",
        "homogeneous of degree ``2``",
        "Exploit scaling laws in dimensional analysis and optimization.",
    ),
    PropertyExample(
        "analytic-exponential",
        "analytic",
        "Entire real restriction",
        "result = fp.analytic(sp.exp(x), x)",
        "result is fp.Analyticity.ANALYTIC",
        "``Analyticity.ANALYTIC``",
        "Justify convergent local power-series methods and analytic continuation steps.",
    ),
    PropertyExample(
        "continuous-absolute",
        "continuous",
        "Continuous but nonsmooth",
        "result = fp.continuous(sp.Abs(x), x)",
        "result is fp.Continuity.CONTINUOUS",
        "``Continuity.CONTINUOUS``",
        "Verify hypotheses of existence theorems and interval methods.",
    ),
    PropertyExample(
        "discontinuities-piecewise",
        "discontinuities",
        "Jump discontinuity",
        "f = sp.Piecewise((0, x < 0), (1, True)); result = fp.discontinuities(f, x)",
        "result == sp.Eq(x, 0)",
        "a discontinuity at ``x = 0``",
        "Split quadrature, plotting, and approximation domains at genuine discontinuities.",
    ),
    PropertyExample(
        "meromorphic-rational",
        "meromorphic",
        "Rational meromorphic function",
        "result = fp.meromorphic(1/x, x)",
        "result is fp.Meromorphicity.MEROMORPHIC",
        "``Meromorphicity.MEROMORPHIC``",
        "Determine whether residue and pole-based complex-analysis techniques apply.",
    ),
    PropertyExample(
        "poles-rational",
        "poles",
        "Simple pole",
        "result = fp.poles(1/x, x)",
        "result == [(sp.Integer(0), 1)]",
        "one simple pole at ``x = 0``",
        "Locate poles for contour deformation, residues, and singular quadrature.",
    ),
    PropertyExample(
        "singularities-rational",
        "singularities",
        "Boolean singularity locus",
        "result = fp.singularities(1/x, x)",
        "result == sp.Eq(x, 0)",
        "the singular locus ``x = 0``",
        "Obtain one composable Boolean locus for analytic obstructions before downstream analysis.",
    ),
    PropertyExample(
        "singularity-analysis-rational",
        "singularity_analysis",
        "Detailed singularity analysis",
        "result = fp.singularity_analysis(1/x, x)",
        "result.complete is True and len(result.poles) == 1 and result.unknown_heads == ()",
        "a complete analysis with one pole",
        "Inspect completeness and provenance when a downstream proof requires certified singularity coverage.",
    ),
    PropertyExample(
        "branchpoints-log",
        "branch_points",
        "Logarithmic branch point",
        "result = fp.branch_points(sp.log(x), x)",
        "result == sp.Eq(x, 0)",
        "a branch point at ``x = 0``",
        "Identify non-isolated analytic structure relevant to continuation and contour choices.",
    ),
    PropertyExample(
        "branchcuts-log",
        "branch_cuts",
        "Principal logarithm cut",
        "result = fp.branch_cuts(sp.log(x), x)",
        "result == (x < 0,)",
        "``(x < 0,)``",
        "Avoid crossing branch cuts in symbolic transformations and complex numerical paths.",
    ),
    PropertyExample(
        "boundary-quadratic",
        "boundary_behavior",
        "Quadratic escape limits",
        "result = fp.boundary_behavior(x**2, x)",
        "result.complete is True and all(item.value is sp.oo for item in result.limits)",
        "both real escape limits are ``+oo``",
        "Certify endpoint escape behavior before coercivity or attainment reasoning.",
    ),
    PropertyExample(
        "level-bounded-quartic",
        "level_boundedness",
        "Coercive quartic",
        "result = fp.level_boundedness(x**4 - x, x)",
        "result is fp.TruthValue.TRUE",
        "a verified level-boundedness certificate",
        "Prove bounded sublevel sets without numerical optimization.",
    ),
    PropertyExample(
        "mode-gaussian-log-density",
        "mode_existence",
        "Structural maximum existence",
        "result = fp.mode_existence(-x**2/2, x, sense='max')",
        "result is fp.TruthValue.TRUE",
        "a verified global-maximum existence certificate",
        "Establish existence of a mode from continuity, closedness, and coercivity.",
    ),
    PropertyExample(
        "geometry-quadratic",
        "geometry",
        "Combined function geometry",
        "result = fp.geometry(x**2, x)",
        "result.c2 is fp.TruthValue.TRUE and result.minimum_exists.exists is True",
        "a combined regularity, singularity, convexity, and attainment summary",
        "Collect structural facts for optimization and probability workflows in one query.",
    ),
    PropertyExample(
        "jacobian-affine",
        "jacobian",
        "Exact affine Jacobian",
        "result = fp.jacobian((2*x + y, x - y), (x, y))",
        "result == sp.ImmutableMatrix([[2, 1], [1, -1]])",
        "the exact matrix ``[[2, 1], [1, -1]]``",
        "Compute a replayable derivative matrix for a coordinate transformation.",
    ),
    PropertyExample(
        "determinant-nonvanishing-affine",
        "determinant_nonvanishing",
        "Nonvanishing Jacobian determinant",
        "result = fp.determinant_nonvanishing((2*x + y, x - y), (x, y))",
        "result is fp.TruthValue.TRUE",
        "a verified nonvanishing determinant ``-3``",
        "Check the inverse-function-theorem rank hypothesis on an entire domain.",
    ),
    PropertyExample(
        "local-invertibility-affine",
        "local_invertibility",
        "Local invertibility",
        "result = fp.local_invertibility((2*x + y, x - y), (x, y))",
        "result is fp.TruthValue.TRUE",
        "a verified local-invertibility certificate",
        "Certify local coordinate validity without claiming global injectivity.",
    ),
    PropertyExample(
        "change-variables-affine",
        "change_of_variables",
        "Change-of-variables volume factor",
        "result = fp.change_of_variables((2*x + y, x - y), (x, y))",
        "result.classification is fp.TruthValue.TRUE and result.volume_factor == 3",
        "the certified factor ``Abs(det J) = 3``",
        "Carry the correct local measure factor into transformed integrals or densities.",
    ),
    PropertyExample(
        "transformation-geometry-affine",
        "transformation_geometry",
        "Combined transformation geometry",
        "result = fp.transformation_geometry((x + y, x - y), (x, y))",
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
        "a = sp.symbols('a', positive=True); result = fp.monotonicity(fp.RegularizedGammaP(a, x), x, domain=x > 0)",
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
        "m, a, b = sp.symbols('m a b', positive=True); result = fp.monotonicity(sp.marcumq(m, a, b), b, domain=b > 0)",
        "result is fp.Monotonicity.STRICTLY_DECREASING",
        "strict decrease in the positive threshold",
        "Analyze noncentral-tail probabilities and detection thresholds structurally.",
    ),
    StatisticalSpecialFunctionExample(
        "mittag-leffler-complete-monotonicity",
        "Mittag-Leffler complete monotonicity",
        "alpha = sp.symbols('alpha', positive=True); t = sp.symbols('t', nonnegative=True); result = fp.complete_monotonicity(fp.MittagLefflerE(alpha, -t), t, domain=t >= 0, assumptions=alpha <= 1)",
        "result is fp.TruthValue.TRUE",
        "complete monotonicity for ``0 < alpha <= 1``",
        "Certify Laplace-transform geometry in fractional stochastic and reliability models.",
    ),
    StatisticalSpecialFunctionExample(
        "bessel-ratio-geometry",
        "Modified-Bessel ratio monotonicity",
        "nu = sp.symbols('nu', nonnegative=True); t = sp.symbols('t', positive=True); ratio = sp.besseli(nu + 1, t) / sp.besseli(nu, t); result = fp.monotonicity(ratio, t, domain=t > 0)",
        "result is fp.Monotonicity.STRICTLY_INCREASING",
        "strict increase for nonnegative ``nu`` on ``t > 0``",
        "Support directional-statistics and noncentral-distribution parameter geometry.",
    ),
)


def examples_for(property_name: str) -> tuple[PropertyExample, ...]:
    """Return the canonical examples for one public property query."""

    return tuple(case for case in EXAMPLES if case.property_name == property_name)
