"""Build the property reference from the canonical executable examples."""

from __future__ import annotations

import inspect
from pathlib import Path

import funcprops.api as api
from examples.property_examples import examples_for

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "properties"
REPO = "https://github.com/BhuvaneshBhatt/funcprops/blob/main"

# Page-specific mathematical content.  The surrounding sections are deliberately
# uniform so every public query answers the same user-facing questions.
INFO = {
    "function_domain": (
        "Domain",
        "The domain is the set of input values for which the expression is defined under the selected real-domain convention.",
        "A SymPy logical condition, or a stratified result when parameter cases must be separated.",
        "Expression-domain rules, algebraic constraints, radical/logarithm restrictions, denominator exclusions, and exact semialgebraic reduction.",
        "Complicated transcendental preimages and unresolved parameter relations can prevent a fully simplified condition.",
    ),
    "function_range": (
        "Range",
        "The range is the set of output values attained by the expression on the requested input constraints.",
        "A SymPy condition in the output symbol, possibly wrapped in a conditional PropertyResult for parameter strata.",
        "Semialgebraic elimination, monotone partitions, endpoint limits, extrema, structural special-function facts, and exact set reasoning.",
        "General transcendental range computation is undecidable in closed form; unsupported cases remain conservative rather than sampled.",
    ),
    "function_sign": (
        "Sign",
        "Sign classification determines whether an expression is positive, nonnegative, zero, nonpositive, negative, or sign-changing throughout a domain.",
        "A Sign value or PropertyResult containing guarded parameter cases and implied weaker sign classes.",
        "Structural sign rules, exact inequality proving, semialgebraic certification, zero geometry, special-function facts, and parameter stratification.",
        "A result of UNKNOWN means the available proof engines could not certify a uniform sign; it does not mean the sign is arbitrary.",
    ),
    "function_zeros": (
        "Zeros",
        "The zero set contains the domain points at which the expression is exactly zero.",
        "Usually a SymPy Set; return_result=True exposes structured/conditional information.",
        "Exact algebraic solving, semialgebraic reduction, monotone partitions, structural special-function rules, and guarded parameter cases.",
        "Infinite or transcendental zero sets may require structured representations, and numerical roots are opt-in rather than silently mixed with exact results.",
    ),
    "function_boundedness": (
        "Boundedness",
        "Boundedness records whether the image is bounded above, below, both, or neither on the requested domain.",
        "A Boundedness value or conditional PropertyResult.",
        "Cheap structural closure rules first, followed by range/extremum reasoning, limits, periodic structure, and parameter stratification.",
        "Failure to prove a finite extremum or range enclosure can yield UNKNOWN even when the function is mathematically bounded.",
    ),
    "function_monotonicity": (
        "Monotonicity",
        "Monotonicity classifies a function as strictly increasing/decreasing, weakly monotone, constant, non-monotone, or unknown on a domain.",
        "A Monotonicity value, PropertyResult, or interval decomposition when requested.",
        "Derivative-sign certification, shared monotone partitions, structural composition rules, theorem-backed special functions, piecewise interface checks, and parameter strata.",
        "Disconnected domains and functions with many turning points may require interval output rather than a single global class.",
    ),
    "function_convexity": (
        "Convexity",
        "Convexity classifies ordinary, strict, strong, affine, concave, log-, quasi-, and pseudo-convex/concave behavior when certifiable.",
        "A Convexity value or PropertyResult; detailed results carry a normalized ConvexityCertificate.",
        "Second-derivative/Hessian inequalities, semialgebraic certification, composition rules, strong-modulus bounds, piecewise slope-interface checks, and theorem-backed facts.",
        "Secondary notions are often certified by sufficient implications rather than complete decision procedures; nonconvex does not imply every weaker notion is absent.",
    ),
    "function_differentiability": (
        "Differentiability",
        "Differentiability asks whether derivatives exist throughout a domain, optionally through a requested finite order.",
        "A Differentiability value or PropertyResult with regularity evidence.",
        "The smoothness engine, domain-aware exceptional-locus analysis, analytic closure rules, and certified finite-order derivative checks.",
        "The bounded max_order search is a certification limit, not a claim that higher derivatives fail to exist.",
    ),
    "function_smoothness": (
        "Smoothness",
        "Smoothness records continuity, the certified differentiability order, C-infinity status, analyticity, and exceptional loci.",
        "A SmoothnessResult with regularity fields and evidence.",
        "Analytic-implies-smooth closure, structural regularity rules, branch/interface checks, and bounded derivative-order certification.",
        "Finite-order search can understate differentiability when no structural C-infinity proof is available.",
    ),
    "function_injective": (
        "Injectivity",
        "A function is injective when distinct domain points cannot have the same output.",
        "TruthValue.TRUE, FALSE, or UNKNOWN, possibly stratified by parameters.",
        "Strict monotonicity, symmetry/periodicity obstructions, affine/structural rules, shared partitions, and exact collision reasoning where available.",
        "General multivariate and transcendental injectivity are difficult; UNKNOWN is preferred to a heuristic collision claim.",
    ),
    "function_surjective": (
        "Surjectivity",
        "A function is surjective onto a codomain when every codomain value is attained by some domain point.",
        "TruthValue.TRUE, FALSE, or UNKNOWN, possibly stratified by parameters.",
        "Exact range comparison, structural mappings, monotone/range closure, and parameter stratification.",
        "The answer depends on both domain and codomain; an omitted or unsuitable codomain can change the mathematical question.",
    ),
    "function_bijective": (
        "Bijectivity",
        "A function is bijective when it is both injective on its domain and surjective onto its codomain.",
        "TruthValue.TRUE, FALSE, or UNKNOWN, possibly stratified by parameters.",
        "Composition of certified injectivity and surjectivity with shared structural shortcuts.",
        "UNKNOWN from either component generally propagates unless an independent bijection theorem applies.",
    ),
    "function_oscillation": (
        "Oscillation",
        "Oscillation distinguishes persistent oscillation, finite oscillatory behavior, and nonoscillatory behavior on the selected domain.",
        "An Oscillation classification; details can expose supporting partitions/evidence.",
        "Zeros, extrema, monotone partitions, periodic structure, asymptotic behavior, and special-function knowledge.",
        "Highly irregular or parameter-dependent oscillation can remain UNKNOWN without a certifiable infinite pattern.",
    ),
    "function_periodicity": (
        "Periodicity",
        "Periodicity detects constants, periodic functions and certified aperiodic cases; detailed results can include a period.",
        "A Periodicity value or detailed result containing the period and evidence.",
        "Structural periodic identities, affine pullbacks, compatible-period combination, parameter assumptions, and exact simplification.",
        "Failure to find a period is not by itself proof of aperiodicity; UNKNOWN is used when no aperiodicity theorem applies.",
    ),
    "function_symmetry": (
        "Symmetry",
        "Symmetry detects even, odd, both, central, neither, or unresolved symmetry relative to a chosen center.",
        "A Symmetry value or detailed result with center/evidence.",
        "Exact substitutions around the center, structural identities, domain compatibility, and simplification.",
        "Symbolic equivalence that SymPy cannot prove can leave symmetry UNKNOWN even when the identity is mathematically true.",
    ),
    "function_homogeneity": (
        "Homogeneity",
        "A function is homogeneous when a common scaling of its variables produces a fixed power of the scale; weighted homogeneity allows variable-specific weights.",
        "A Homogeneity value or detailed result containing degree/weights and parameter conditions.",
        "Polynomial weighted-degree grouping, exact scaling identities, parameter strata, and structural closure.",
        "General nonpolynomial quasi-homogeneous identities may require simplification or assumptions beyond the current proof rules.",
    ),
    "function_analytic": (
        "Analyticity",
        "Analyticity certifies local representation by convergent power series throughout the requested domain.",
        "Analyticity.ANALYTIC, NOT_ANALYTIC, or UNKNOWN; details expose evidence and exceptional loci.",
        "Singularity/branch analysis, analytic closure rules, piecewise interface checks, domain restrictions, and theorem-backed function facts.",
        "Real analyticity is stricter than smoothness; unresolved branch or singularity structure can conservatively produce UNKNOWN.",
    ),
    "function_continuous": (
        "Continuity",
        "Continuity certifies that the function has no value/limit mismatch at points of the requested domain.",
        "Continuity.CONTINUOUS, DISCONTINUOUS, or UNKNOWN; details provide evidence.",
        "Structural closure, one-sided interface limits for Piecewise expressions, singularity analysis, and domain restriction.",
        "Complicated limit problems can remain UNKNOWN rather than being decided numerically.",
    ),
    "function_discontinuities": (
        "Discontinuities",
        "Discontinuity analysis locates points or guarded loci where continuity fails.",
        "A tuple of Singularity records of kind DISCONTINUITY.",
        "Piecewise interface limits, denominator/domain failures, branch behavior, and structural singularity traversal.",
        "An empty tuple means no discontinuity was certified by the analysis, not necessarily a completeness theorem unless the associated detailed analysis is complete.",
    ),
    "function_meromorphic": (
        "Meromorphicity",
        "A meromorphic function is analytic except for isolated poles on the domain under consideration.",
        "Meromorphicity.MEROMORPHIC, NOT_MEROMORPHIC, or UNKNOWN.",
        "Structural singularity traversal, branch-point/cut exclusion, pole classification, and known meromorphic closure rules.",
        "Natural boundaries, unresolved singularity heads, or branch structure may prevent a complete classification.",
    ),
    "function_poles": (
        "Poles",
        "Pole analysis identifies isolated singularities with finite negative local order and records multiplicity when known.",
        "A tuple of Singularity records with kind POLE.",
        "Local order, rational denominator structure, special-function singularity facts, and guarded parameter analysis.",
        "Multiplicity can be unknown when local cancellation or parameter dependence cannot be resolved exactly.",
    ),
    "function_singularities": (
        "Singularities",
        "This query returns a grouped inventory of poles, removable/essential singularities, branch points, branch cuts, and definition cuts.",
        "A dictionary whose values are tuples of Singularity records or cut conditions.",
        "Shared structural singularity traversal and branch analysis, grouped by singularity kind.",
        "Use function_singularity_analysis when completeness and unknown function heads matter to a proof.",
    ),
    "function_singularity_analysis": (
        "Singularity analysis",
        "Detailed singularity analysis reports analytic obstructions together with completeness and unresolved-head information.",
        "A SingularityAnalysis object containing singularity groups, domain exterior, completeness, unknown heads, and provenance.",
        "Structural traversal, local singularity classification, branch analysis, discontinuity analysis, and domain comparison.",
        "complete=False is an explicit warning that the returned inventory is not exhaustive.",
    ),
    "function_branchpoints": (
        "Branch points",
        "Branch-point analysis identifies points around which analytic continuation can change the value of a multivalued function.",
        "A tuple of Singularity records with kind BRANCH_POINT.",
        "Known principal-branch structure, compositional preimages, algebraic/logarithmic branch rules, and assumptions.",
        "General nested transcendental preimages can be difficult to reduce to a simple exact locus.",
    ),
    "function_branchcuts": (
        "Branch cuts",
        "Branch-cut analysis returns the cuts used to make the selected principal branches single-valued.",
        "By default a tuple of logical cut conditions; alternate modes expose other supported representations.",
        "Principal-branch registry facts, compositional preimages, algebraic transformation, simplification under assumptions, and cut normalization.",
        "Branch cuts are representation/convention dependent; they are not intrinsic singularities of the underlying multivalued analytic object.",
    ),
}


PARAMETER_TEXT = {
    "expr": "SymPy expression whose global property is queried.",
    "var": "Independent symbol, or supported variable collection for multivariate queries.",
    "vars": "Variable sequence used by the multivariate structural query.",
    "y": "Output symbol used to represent the range condition.",
    "domain": "Input domain or logical condition. The default depends on the property family.",
    "constraints": "Input constraints used by range analysis.",
    "codomain": "Target set for surjectivity or bijectivity.",
    "assumptions": "Symbolic hypotheses used while proving the property.",
    "strict_inequalities": "Whether strict classifications are distinguished from their weak implications.",
    "all_properties": "Return the primary classification together with certified implied properties.",
    "details": "Return structured evidence/certificates instead of only the primary classification when supported.",
    "intervals": "Request an interval decomposition rather than only a global classification.",
    "partition": "Optional precomputed monotonic partition for exact reuse.",
    "order": "Requested differentiability order; omitted means the strongest certified regularity class.",
    "max_order": "Maximum finite derivative order tried when no structural smoothness proof is available.",
    "degree": "Requested homogeneity degree, when one is prescribed.",
    "weights": "Optional variable weights for weighted homogeneity.",
    "center": "Reflection or central-symmetry center; supported discovery modes may infer it.",
    "return_result": "Return structured zero-set evidence instead of only the set when enabled.",
    "allow_numerical": "Permit explicitly marked numerical zero information when exact analysis is unavailable.",
    "method": "Select the supported range-analysis strategy; ``auto`` chooses the normal proof cascade.",
    "mode": "Select the supported branch-cut output representation.",
    "ignore_unknown": "Allow detailed singularity analysis to omit unresolved primitive heads from completeness checks.",
}


def public_signature(func):
    sig = inspect.signature(func)
    params = [p for p in sig.parameters.values() if not p.name.startswith("_")]
    return sig.replace(parameters=params)


def parameter_table(func):
    rows = ["| Parameter | Meaning |", "| --- | --- |"]
    for param in public_signature(func).parameters.values():
        name = param.name
        text = PARAMETER_TEXT.get(
            name,
            "Public query option; see the function signature and examples for its supported use.",
        )
        rows.append(f"| `{name}` | {text} |")
    return rows


RELATED = {
    "function_domain": ["function_continuous", "function_singularities"],
    "function_range": ["function_boundedness", "function_surjective"],
    "function_sign": ["function_zeros", "function_monotonicity", "function_convexity"],
    "function_zeros": ["function_sign", "function_oscillation"],
    "function_boundedness": ["function_range", "function_oscillation"],
    "function_monotonicity": ["function_sign", "function_injective", "function_range"],
    "function_convexity": ["function_sign", "function_monotonicity"],
    "function_differentiability": [
        "function_smoothness",
        "function_continuous",
        "function_analytic",
    ],
    "function_smoothness": [
        "function_differentiability",
        "function_analytic",
        "function_continuous",
    ],
    "function_injective": [
        "function_surjective",
        "function_bijective",
        "function_monotonicity",
    ],
    "function_surjective": ["function_range", "function_bijective"],
    "function_bijective": ["function_injective", "function_surjective"],
    "function_oscillation": [
        "function_zeros",
        "function_periodicity",
        "function_boundedness",
    ],
    "function_periodicity": ["function_symmetry", "function_oscillation"],
    "function_symmetry": ["function_periodicity", "function_injective"],
    "function_homogeneity": ["function_symmetry", "function_convexity"],
    "function_analytic": [
        "function_smoothness",
        "function_meromorphic",
        "function_singularities",
    ],
    "function_continuous": ["function_discontinuities", "function_differentiability"],
    "function_discontinuities": [
        "function_continuous",
        "function_singularity_analysis",
    ],
    "function_meromorphic": [
        "function_poles",
        "function_singularity_analysis",
        "function_analytic",
    ],
    "function_poles": ["function_singularities", "function_meromorphic"],
    "function_singularities": [
        "function_singularity_analysis",
        "function_branchcuts",
        "function_poles",
    ],
    "function_singularity_analysis": [
        "function_singularities",
        "function_discontinuities",
    ],
    "function_branchpoints": ["function_branchcuts", "function_singularities"],
    "function_branchcuts": ["function_branchpoints", "function_singularity_analysis"],
}


def page_for(name: str) -> str:
    title, definition, returns, proof, limits = INFO[name]
    func = getattr(api, name)
    cases = examples_for(name)
    lines = [
        f"# {title}",
        "",
        f"`{name}`",
        "",
        "## Mathematical definition",
        "",
        definition,
        "",
        "## API and return values",
        "",
        "```python",
        f"{name}{public_signature(func)}",
        "```",
        "",
        returns,
        "",
        "## Domains, assumptions, and parameters",
        "",
        "The query is interpreted on the supplied domain rather than from the expression in isolation. "
        "When symbolic parameters change the property, funcprops preserves those cases as guarded parameter strata instead of choosing a generic value. "
        "Assumptions are proof hypotheses: they can simplify a stratum or branch condition, but they do not justify numerical guessing.",
        "",
        "## Executable examples",
        "",
    ]
    for case in cases:
        lines += [
            f"### {case.title}",
            "",
            f"<!-- example-id: {case.example_id} -->",
            "",
            "```python",
            "import sympy as sp",
            "import funcprops as fp",
            "",
            'x, y = sp.symbols("x y", real=True)',
            case.code,
            "result",
            "```",
            "",
            f"Expected: {case.expected}.",
            "",
            f"Application: {case.application}",
            "",
        ]
    lines += [
        "## Applications",
        "",
        "This property is useful whenever later mathematics depends on a global qualitative fact rather than isolated samples. "
        "Typical uses include symbolic preprocessing, theorem-hypothesis verification, optimization, inverse problems, robust numerical method selection, and simplifying downstream case analysis.",
        "",
        "## How funcprops proves it",
        "",
        proof,
        "",
        "Successful conclusions are exact symbolic claims over the stated domain and assumptions. "
        "Detailed modes expose evidence or certificates where the property API supports them.",
        "",
        "## Known limitations",
        "",
        limits,
        "",
        "`UNKNOWN` means that the available proof machinery did not certify the claim. It must not be interpreted as the negation of the property.",
        "",
        "## Related properties",
        "",
    ]
    for rel in RELATED.get(name, []):
        lines.append(f"- [`{rel}`]({rel.removeprefix('function_')}.md)")
    lines += [
        "",
        "## Source",
        "",
        f"The implementation is exposed through [`funcprops.api`]({REPO}/src/funcprops/api.py).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = list(api.__all__)
    missing = sorted(set(names) - INFO.keys())
    if missing:
        raise RuntimeError(f"missing property documentation metadata: {missing}")
    for name in names:
        (OUT / f"{name.removeprefix('function_')}.md").write_text(
            page_for(name), encoding="utf-8"
        )
    index = [
        "# Function property reference",
        "",
        "Every public `function_*` query has a canonical page below. Examples on these pages are executed by the specification test suite.",
        "",
    ]
    for name in names:
        title = INFO[name][0]
        index.append(f"- [{title}]({name.removeprefix('function_')}.md) — `{name}`")
    index += [
        "",
        "See also [domains and assumptions](../architecture.md) for the shared proof architecture.",
        "",
    ]
    (OUT / "index.md").write_text("\n".join(index), encoding="utf-8")


if __name__ == "__main__":
    main()
