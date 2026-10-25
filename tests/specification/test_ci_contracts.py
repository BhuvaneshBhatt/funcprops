"""CI selectors and local profiles share a checked test catalog."""

from pathlib import Path

from tools.check_ci import selection_errors
from tools.test_selections import GROUPS, PLATFORM, WARM


def test_catalog():
    assert selection_errors() == []
    for name in (
        "tests/test_source_transport.py",
        "tests/test_metric_replay.py",
        "tests/test_branch_gluing.py",
        "tests/test_parameter_geometry.py",
    ):
        assert name in PLATFORM and name in WARM


def test_missing_selector(tmp_path):
    assert selection_errors(tmp_path, {"test": ("tests/missing.py",)}) == [
        "test: missing selector tests/missing.py"
    ]


def test_workflow_typos(tmp_path):
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "run: python -m pytest tests/test_bad-name.py\nrun: python -m tools.run_selected_tests unknown\n"
    )
    assert selection_errors(tmp_path, {}) == [
        "ci.yml: missing selector tests/test_bad-name.py",
        "ci.yml: unknown test group unknown",
    ]


def test_selections_are_files():
    root = Path(__file__).resolve().parents[2]
    for selectors in GROUPS.values():
        assert all((root / selector).is_file() for selector in selectors)
