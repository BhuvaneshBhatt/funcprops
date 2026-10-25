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
    import re
    from urllib.parse import urlsplit

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    prefix = "https://github.com/BhuvaneshBhatt/funcprops/blob/main/"
    assert f"]({prefix}docs/index.md)" in readme
    reachable = set()
    for page in (ROOT / "README.md", ROOT / "docs/index.md"):
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", page.read_text()):
            url = urlsplit(link)
            if link.startswith(prefix):
                reachable.add((ROOT / url.path.split("/blob/main/", 1)[1]).resolve())
            elif not url.scheme:
                reachable.add((page.parent / url.path).resolve())
    for name in (
        "certification.md",
        "mathematical-conventions.md",
        "complex-analysis.md",
        "homotopy.md",
        "capabilities.md",
        "examples.md",
    ):
        target = ROOT / "docs" / name
        assert target in reachable and target.is_file()
