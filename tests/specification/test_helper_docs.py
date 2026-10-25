"""Helper contracts and every registered concrete record remain documented."""

from pathlib import Path

from funcprops.verification import _certificate_verifiers
from tools.build_helper_docs import reference_text

ROOT = Path(__file__).resolve().parents[2]


def test_reference_matches_exports():
    text = reference_text()
    assert (ROOT / "docs/reference/helper-contracts.md").read_text() == text
    for cls, _ in _certificate_verifiers():
        assert "### " + cls.__module__ + "." + cls.__name__ in text


def test_metric_contract_fields():
    text = reference_text()
    for section in (
        "### certify_finite_lipschitz",
        "### certify_jump_variation",
        "### certify_parameter_geometry",
        "### glue_branch_charts",
    ):
        assert section in text
    for name in (
        "VariationMotion",
        "ParameterGeometryRegion",
        "ParameterGeometryCell",
        "BranchOverlapProof",
    ):
        assert name in text
    assert "| `proof` |" in text and "| `parameter_domain` |" in text
