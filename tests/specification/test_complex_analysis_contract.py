from pathlib import Path

import funcprops as fp

ROOT = Path(__file__).parents[2]

PUBLIC_OPERATIONS = {
    "argument_principle",
    "classify_singularity",
    "deform_contour",
    "homotopic",
    "integrate",
    "monodromy",
    "residue",
    "winding_number",
}


def test_documented_operations_are_public():
    missing = sorted(name for name in PUBLIC_OPERATIONS if not hasattr(fp, name))
    assert missing == []


def test_capability_matrix_covers_operations():
    text = (ROOT / "docs" / "capabilities.md").read_text(encoding="utf-8").lower()
    expected_terms = {
        "argument principle",
        "contour deformation",
        "contour integration",
        "homotopy",
        "residue",
        "analytic continuation",
        "singularity classification",
        "winding number",
    }
    assert {term for term in expected_terms if term not in text} == set()


def test_readme_links_core_guides():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in (
        "certification.md",
        "mathematical_conventions.md",
        "complex_analysis.md",
        "homotopy.md",
        "capabilities.md",
        "examples.md",
    ):
        assert (
            f"https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/{name}"
            in readme
        )
