"""The tutorial notebook must stay synchronized with tested examples."""

import json
from pathlib import Path

from examples.property_examples import EXAMPLES, STATISTICAL_SPECIAL_FUNCTION_EXAMPLES

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "docs" / "notebooks" / "function-properties-tour.ipynb"


def test_notebook_contains_every_executable_documentation_example():
    data = json.loads(NOTEBOOK.read_text())
    text = "\n".join("".join(cell["source"]) for cell in data["cells"])
    for case in (*EXAMPLES, *STATISTICAL_SPECIAL_FUNCTION_EXAMPLES):
        assert f"<!-- example-id: {case.example_id} -->" in text


def test_notebook_links_each_property_to_reference_page():
    text = NOTEBOOK.read_text()
    for case in EXAMPLES:
        page = case.property_name.removeprefix("function_")
        assert f"../properties/{page}.md" in text


def test_notebook_code_cells_execute_in_order():
    data = json.loads(NOTEBOOK.read_text())
    namespace = {}
    for cell in data["cells"]:
        if cell["cell_type"] == "code":
            exec("".join(cell["source"]), namespace)
