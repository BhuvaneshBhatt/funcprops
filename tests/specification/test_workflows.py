"""Standalone workflows and generated tutorial artifacts share one source."""

import json
import runpy
from pathlib import Path

import pytest

from examples.workflow_catalog import WORKFLOWS
from tools.build_workflow_docs import generated_files, workflow_sections

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case", WORKFLOWS, ids=lambda c: c.slug)
def test_standalone_workflow(case):
    runpy.run_path(str(ROOT / "examples" / case.filename), run_name="__main__")


def test_workflow_docs_and_helper_signatures_are_current():
    files = generated_files()
    assert {path.name for path in (ROOT / "docs/tutorials").glob("*.md")} == {
        Path(name).name for name in files if name.startswith("docs/tutorials/")
    }
    for name, text in files.items():
        assert (ROOT / name).read_text() == text, name


def test_workflow_notebook_is_clean_and_checked():
    path = ROOT / "docs/notebooks/certified-workflows.ipynb"
    data = json.loads(path.read_text())
    assert all(
        not cell.get("outputs") and cell.get("execution_count") is None
        for cell in data["cells"]
        if cell["cell_type"] == "code"
    )
    cells = [cell for cell in data["cells"] if cell["cell_type"] == "code"]
    assert len(cells) == sum(
        len(workflow_sections((ROOT / "examples" / case.filename).read_text()))
        for case in WORKFLOWS
    )
    assert {cell["metadata"]["workflow_id"] for cell in cells} == {
        case.slug for case in WORKFLOWS
    }
    namespace = {}
    previous = None
    for cell in cells:
        workflow = cell["metadata"]["workflow_id"]
        if workflow != previous:
            namespace = {"__name__": "__workflow_cell__"}
            previous = workflow
        exec(
            compile("".join(cell["source"]), str(path), "exec"),
            namespace,
        )
