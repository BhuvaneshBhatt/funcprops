"""Build the tutorial notebook from the executable documentation examples."""

from __future__ import annotations

import json
from pathlib import Path

from examples.property_examples import EXAMPLES, STATISTICAL_SPECIAL_FUNCTION_EXAMPLES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "notebooks" / "function-properties-tour.ipynb"

GROUPS = [
    (
        "Domains and values",
        {
            "function_domain",
            "function_range",
            "function_sign",
            "function_zeros",
            "function_boundedness",
        },
    ),
    (
        "Shape and variation",
        {
            "function_monotonicity",
            "function_convexity",
            "function_complete_monotonicity",
            "function_oscillation",
        },
    ),
    (
        "Regularity",
        {
            "function_continuous",
            "function_differentiability",
            "function_smoothness",
            "function_analytic",
        },
    ),
    (
        "Mapping properties",
        {"function_injective", "function_surjective", "function_bijective"},
    ),
    (
        "Structural properties",
        {"function_periodicity", "function_symmetry", "function_homogeneity"},
    ),
    (
        "Complex analytic structure",
        {
            "function_complex_zeros",
            "function_meromorphic",
            "function_discontinuities",
            "function_poles",
            "function_branchpoints",
            "function_branchcuts",
            "function_singularities",
            "function_singularity_analysis",
        },
    ),
    (
        "Optimization and function geometry",
        {
            "function_boundary_behavior",
            "function_level_boundedness",
            "function_mode_existence",
            "function_geometry",
        },
    ),
    (
        "Transformation geometry",
        {
            "function_jacobian",
            "function_determinant_nonvanishing",
            "function_local_invertibility",
            "function_change_of_variables",
            "function_transformation_geometry",
        },
    ),
]


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.splitlines()],
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.splitlines()],
    }


def main() -> None:
    cells = [
        md(
            "# A tour of function properties\n\nThis notebook is a guided introduction to `funcprops`. Every property example below is drawn from the same executable example corpus used by the specification tests, so the tutorial and reference documentation cannot silently drift apart.\n\nThe package answers symbolic global questions over explicit domains and assumptions. `UNKNOWN` means that no available proof route certified a conclusion; it does not mean the property is false."
        ),
        code(
            'import sympy as sp\n\nimport funcprops as fp\n\nx, y = sp.symbols("x y", real=True)'
        ),
        md(
            "## How to read results\n\nSimple queries return enums, SymPy sets/conditions, or structured results. Parameter-dependent questions may return guarded cases. Detailed modes expose evidence and certificates. The Markdown property reference is authoritative for definitions, return contracts, supported proof strategies, and limitations."
        ),
    ]
    by_name = {}
    for case in EXAMPLES:
        by_name.setdefault(case.property_name, []).append(case)
    for heading, names in GROUPS:
        cells.append(md(f"## {heading}"))
        for name in sorted(names):
            for case in by_name[name]:
                page = name.removeprefix("function_")
                cells.append(
                    md(
                        f"### `{name}` — {case.title}\n\n<!-- example-id: {case.example_id} -->\n\n"
                        f"**Application.** {case.application}\n\n"
                        f"Expected result: {case.expected}. See [`{page}.md`](../properties/{page}.md) for the full mathematical definition, options, proof strategies, and limitations."
                    )
                )
                cells.append(code(case.code + "\nresult"))
    cells.append(md("## Statistical special functions"))
    cells.append(
        md(
            "These examples exercise the theorem-backed statistical function layer. "
            "See [Statistical special functions](../statistical_special_functions.md) "
            "for supported families, parameter guards, and provenance."
        )
    )
    for case in STATISTICAL_SPECIAL_FUNCTION_EXAMPLES:
        cells.append(
            md(
                f"### {case.title}\n\n<!-- example-id: {case.example_id} -->\n\n"
                f"**Application.** {case.application}\n\n"
                f"Expected result: {case.expected}."
            )
        )
        cells.append(code(case.code + "\nresult"))
    cells.append(
        md(
            "## Where to go next\n\nUse the [property reference](../properties/index.md) for comprehensive documentation. For parameterized functions, try the same query both without assumptions and after imposing a parameter guard; for piecewise functions, inspect how branch properties and interface conditions combine. Detailed result modes are especially useful when a downstream proof needs replayable evidence rather than only a classification."
        )
    )
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
