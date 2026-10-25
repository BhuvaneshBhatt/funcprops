"""Build the property reference from the canonical executable examples."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

import funcprops as api
from examples.property_examples import (
    STATISTICAL_SPECIAL_FUNCTION_EXAMPLES,
    examples_for,
)
from tools.markdown import normalize_markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "properties"
PUBLIC_QUERIES = tuple(name for name, *_ in api.properties())
REPO = "https://github.com/BhuvaneshBhatt/funcprops/blob/main"

# Page-specific mathematical content.  The surrounding sections are consistently
# uniform so every public query answers the same user-facing questions.
METADATA = json.loads((ROOT / "tools/property_reference.json").read_text())
INFO = {
    name: tuple(
        data[key] for key in ("title", "definition", "returns", "proof", "limits")
    )
    for name, data in METADATA.items()
}


PARAMETER_TEXT = {
    "work_budget": "Optional positive wall budget in seconds; exhaustion follows the operation-specific incomplete/unknown contract.",
    "expr": "SymPy expression whose global property is queried.",
    "variable": "Independent scalar coordinate. Real and native complex routes have different assumption requirements; see result contracts.",
    "args": "Positional coordinate and rectangle forms accepted by this wrapper; prefer the explicit tutorial call.",
    "kwargs": "Operation-specific options, including supported budgets and native isolation policy/accuracy targets; see the linked guide.",
    "stratified": "Preserve supported guarded parameter-domain cases.",
    "var": "Independent symbol, or supported variable collection for multivariate queries.",
    "vars": "Variable sequence used by the multivariate structural query.",
    "variables": "Independent symbol or ordered variable sequence for multivariate geometry.",
    "expressions": "Ordered expression sequence defining a coordinate transformation.",
    "sense": "Optimization sense, either ``min`` or ``max`` for structural attainment analysis.",
    "y": "Output symbol used to represent the range condition.",
    "domain": "Input domain or logical condition. The default depends on the property family.",
    "constraints": "Input constraints used by range analysis.",
    "codomain": "Target set for surjectivity or bijectivity.",
    "assumptions": "Symbolic hypotheses used while proving the property.",
    "strict_inequalities": "Whether strict classifications are distinguished from their weak implications.",
    "all_properties": "Return the primary classification together with certified implied properties.",
    "intervals": "Request an interval decomposition.",
    "partition": "Optional precomputed monotonic partition for exact reuse.",
    "order": "Requested differentiability order; omitted means the strongest certified regularity class.",
    "max_order": "Maximum finite derivative order tried when no structural smoothness proof is available.",
    "degree": "Requested homogeneity degree, when one is prescribed.",
    "weights": "Optional variable weights for weighted homogeneity.",
    "center": "Reflection or central-symmetry center; supported discovery modes may infer it.",
    "return_result": "Return structured metadata, certificates, or diagnostics.",
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
    "lipschitz": ["uniformly_continuous", "holder_regularity", "variation"],
    "uniformly_continuous": ["lipschitz", "continuous"],
    "holder_regularity": ["lipschitz", "uniformly_continuous"],
    "variation": ["monotonicity", "integrability"],
    "integrability": ["variation", "continuous"],
    "domain": ["continuous", "singularities"],
    "range": ["boundedness", "surjective"],
    "sign": ["zeros", "monotonicity", "convexity"],
    "zeros": ["sign", "oscillation"],
    "boundedness": ["range", "oscillation"],
    "monotonicity": ["sign", "injective", "range"],
    "convexity": ["sign", "monotonicity"],
    "differentiability": [
        "smoothness",
        "continuous",
        "analytic",
    ],
    "smoothness": [
        "differentiability",
        "analytic",
        "continuous",
    ],
    "injective": [
        "surjective",
        "bijective",
        "monotonicity",
    ],
    "surjective": ["range", "bijective"],
    "bijective": ["injective", "surjective"],
    "oscillation": [
        "zeros",
        "periodicity",
        "boundedness",
    ],
    "periodicity": ["symmetry", "oscillation"],
    "symmetry": ["periodicity", "injective"],
    "homogeneity": ["symmetry", "convexity"],
    "analytic": [
        "smoothness",
        "meromorphic",
        "singularities",
    ],
    "continuous": ["discontinuities", "differentiability"],
    "discontinuities": [
        "continuous",
        "singularity_analysis",
    ],
    "meromorphic": [
        "poles",
        "singularity_analysis",
        "analytic",
    ],
    "poles": ["singularities", "meromorphic"],
    "singularities": [
        "singularity_analysis",
        "branch_cuts",
        "poles",
    ],
    "singularity_analysis": [
        "singularities",
        "discontinuities",
    ],
    "branch_points": ["branch_cuts", "singularities"],
    "branch_cuts": ["branch_points", "singularity_analysis"],
    "complex_zeros": ["zeros", "analytic"],
    "complete_monotonicity": [
        "monotonicity",
        "convexity",
        "sign",
    ],
    "boundary_behavior": ["level_boundedness", "geometry"],
    "level_boundedness": [
        "boundary_behavior",
        "mode_existence",
        "geometry",
    ],
    "mode_existence": ["level_boundedness", "geometry"],
    "geometry": [
        "convexity",
        "singularities",
        "mode_existence",
    ],
    "jacobian": [
        "determinant_nonvanishing",
        "transformation_geometry",
    ],
    "determinant_nonvanishing": [
        "jacobian",
        "local_invertibility",
    ],
    "local_invertibility": [
        "determinant_nonvanishing",
        "change_of_variables",
    ],
    "change_of_variables": [
        "local_invertibility",
        "transformation_geometry",
    ],
    "transformation_geometry": [
        "jacobian",
        "change_of_variables",
    ],
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
        "```text",
        f"{name}{public_signature(func)}",
        "```",
        "",
        returns,
        "",
        *parameter_table(func),
        "",
        "## Domains, assumptions, and parameters",
        "",
        METADATA[name]["domain"],
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
            f"assert {case.check}",
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
        METADATA[name]["applications"],
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
    ]
    if RELATED.get(name):
        lines += ["## Related properties", ""]
    for rel in RELATED.get(name, []):
        lines.append(f"- [`{rel}`]({rel.removeprefix('')}.md)")
    lines += [
        "",
        "## Source",
        "",
        f"The callable is exported through funcprops; its implementation module is [`{inspect.unwrap(func).__module__}`]({REPO}/src/{inspect.unwrap(func).__module__.replace(chr(46), chr(47))}.py).",
        "",
    ]
    return "\n".join(lines)


def statistical_page():
    metadata = json.loads((ROOT / "tools/statistical_reference.json").read_text())
    lines = [metadata["introduction"], "", "## Executable examples", ""]
    for case in STATISTICAL_SPECIAL_FUNCTION_EXAMPLES:
        lines += [
            f"### {case.title}",
            "",
            f"<!-- example-id: {case.example_id} -->",
            "",
            f"Application: {case.application}",
            "",
            "```python",
            "import sympy as sp",
            "import funcprops as fp",
            'x = sp.Symbol("x", real=True)',
            case.code,
            f"assert {case.check}",
            "```",
            "",
            f"Expected: {case.expected}.",
            "",
        ]
    lines += [metadata["provenance"], ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    names = list(PUBLIC_QUERIES)
    missing = sorted(set(names) - INFO.keys())
    if missing:
        raise RuntimeError(f"missing property documentation metadata: {missing}")
    expected = {f"{name}.md": page_for(name) for name in names}
    index = [
        "# Function property reference",
        "",
        "Every public `root-level property` query has a canonical page below. Examples on these pages are executed by the specification test suite.",
        "",
    ]
    for name in names:
        title = INFO[name][0]
        index.append(f"- [{title}]({name.removeprefix('')}.md): `{name}`")
    index += [
        "",
        "See also [domains and assumptions](../architecture.md) for the shared proof architecture.",
        "",
    ]
    expected["index.md"] = "\n".join(index)
    expected["../statistical-special-functions.md"] = statistical_page()
    expected = {name: normalize_markdown(text) for name, text in expected.items()}
    if args.check:
        stale = sorted(
            name
            for name, text in expected.items()
            if not (OUT / name).exists() or (OUT / name).read_text() != text
        )
        extra = sorted(p.name for p in OUT.glob("*.md") if p.name not in expected)
        if stale or extra:
            raise SystemExit(f"stale property docs: {stale}; extra pages: {extra}")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, text in expected.items():
            (OUT / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
