"""Workflow metadata; code and assertions live in standalone example files."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Workflow:
    slug: str
    filename: str
    title: str
    scope: str


WORKFLOWS = (
    Workflow(
        "piecewise-partitions",
        "piecewise_partitions.py",
        "Piecewise partitions",
        "Reuse cells, exact images and owned seams; coverage and global order have different premises.",
    ),
    Workflow(
        "finite-metric-proofs",
        "finite_metric_proofs.py",
        "Finite metric and variation proofs",
        "Compute exact finite Lipschitz constants and jump variation, then replay their proofs.",
    ),
    Workflow(
        "algebraic-coefficients",
        "algebraic_coefficients.py",
        "Exact algebraic coefficients",
        "Use a uniquely isolated generator in a bounded real number field and retain source holes.",
    ),
    Workflow(
        "parameter-geometry",
        "parameter_geometry.py",
        "Polynomial parameter geometry",
        "Partition a bounded polynomial family by distinct real-root counts and retain unresolved regions.",
    ),
    Workflow(
        "branch-recipes",
        "branch_recipes.py",
        "Gluing local branch recipes",
        "Assemble supplied holomorphic recipes, check every overlap and distinguish disagreement from a global obstruction.",
    ),
    Workflow(
        "certified-extrema-bounds",
        "certified_extrema_bounds.py",
        "Certified extrema bounds",
        "Finite real components, implicit critical points, and separate coverage/value accuracy.",
    ),
    Workflow(
        "branch-chart-gluing",
        "branch_chart_gluing.py",
        "Finite branch-chart gluing",
        "Checked logarithm transitions and selected power branches; nontrivial cycles remain explicit.",
    ),
    Workflow(
        "implicit-common-orders",
        "implicit_common_orders.py",
        "Implicit common zeros and orders",
        "Congruence/radical identities and local orders, separately from exhaustive root coverage.",
    ),
    Workflow(
        "restricted-domains",
        "restricted_domains.py",
        "Restricted domains and held expressions",
        "Real intervals and finite domains; held syntax preserves holes.",
    ),
    Workflow(
        "guarded-piecewise",
        "guarded_piecewise.py",
        "Guarded and Piecewise results",
        "Finite real affine coefficients, supported branch coverage and singleton seams.",
    ),
    Workflow(
        "real-root-coverage",
        "real_root_coverage.py",
        "Real root coverage",
        "Compact witnesses, rational multiplicities, recognized periodic families and tails.",
    ),
    Workflow(
        "complex-isolation",
        "complex_isolation.py",
        "Complex isolation and completion",
        "Parameter-free entire grammar on rational rectangles with zero-free outer boundaries.",
    ),
    Workflow(
        "algebraic-roots",
        "algebraic_roots.py",
        "Algebraic backend roots",
        "Supported algebraic enumeration with principal-branch and raw-source filtering.",
    ),
    Workflow(
        "quotients-and-holes",
        "quotients_and_holes.py",
        "Quotients, holes and poles",
        "Certified entire quotients; shared orders require exact identities and exhaustive counts.",
    ),
    Workflow(
        "budgets-and-resume",
        "budgets_and_resume.py",
        "Budgets and resumption",
        "Checked states and same-environment trusted checkpoint transport; in-memory checkpoint contract.",
    ),
    Workflow(
        "newton-refinement",
        "newton_refinement.py",
        "Count-preserving Newton refinement",
        "A checked simple base, certified contraction and all complement strips.",
    ),
    Workflow(
        "replay",
        "replay.py",
        "Independent native replay",
        "Native witness checking without search; factory-based and algebraic backend trust differs.",
    ),
    Workflow(
        "local-branches",
        "local_branches.py",
        "Selected local branches",
        "Explicit local logarithm values; no global chart-gluing claim.",
    ),
    Workflow(
        "unsupported-and-partial",
        "unsupported_and_partial.py",
        "Unsupported and partial results",
        "Resource exhaustion and boundary obstruction do not prove exclusion.",
    ),
)
