"""The documentation gates must detect broken examples and missing references."""

import json
from pathlib import Path

import pytest

from tools.check_docs import execute_document, headings, link_errors, python_blocks
from tools.check_test_matrix import matrix_text

ROOT = Path(__file__).resolve().parents[2]


def test_page_sessions_share_state_but_pages_start_fresh(tmp_path):
    first = tmp_path / "first.md"
    first.write_text(
        "# Example\n\n```python\nvalue=3\n```\n\n```python\nassert value==3\n```\n"
    )
    assert execute_document(first) == 2
    second = tmp_path / "second.md"
    second.write_text("```python\nassert value==3\n```\n")
    with pytest.raises(NameError):
        execute_document(second)


def test_executable_example_assertions(tmp_path):
    path = tmp_path / "bad.md"
    path.write_text("```python\nassert 1==2\n```\n")
    with pytest.raises(AssertionError):
        execute_document(path)


@pytest.mark.parametrize("text", ["```python\nx=1\n", "```python skip\nx=1\n```\n"])
def test_python_fences_cannot_be_silently_skipped(tmp_path, text):
    path = tmp_path / "bad.md"
    path.write_text(text)
    with pytest.raises(ValueError):
        list(python_blocks(path))


def test_long_closing_fence_and_indented_tilde_python(tmp_path):
    path = tmp_path / "valid.md"
    path.write_text(
        "   ~~~python\nassert True\n   ~~~~\n\n```text\nsignature(expr)\n```\n"
    )
    assert execute_document(path) == 1


def test_notebook_links_and_anchors(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(
        "[first](docs/guide.md#repeated) [second](docs/guide.md#repeated-1)"
    )
    guide = tmp_path / "docs/guide.md"
    guide.write_text("# Repeated\n\n# Repeated\n")
    assert {"repeated", "repeated-1"} <= headings(guide.read_text())
    notebook = {
        "cells": [{"cell_type": "markdown", "source": ["[missing](guide.md#absent)"]}]
    }
    (tmp_path / "docs/test.ipynb").write_text(json.dumps(notebook))
    assert link_errors(tmp_path) == ["docs/test.ipynb: missing anchor guide.md#absent"]
    guide.unlink()
    assert any("missing link docs/guide.md" in error for error in link_errors(tmp_path))


def test_registered_type_matrix_is_current():
    assert (ROOT / "docs/reference/testing-matrix.md").read_text() == matrix_text()


def test_repository_readme_links(tmp_path):
    (tmp_path / "docs").mkdir()
    prefix = "https://github.com/BhuvaneshBhatt/funcprops/blob/main/"
    (tmp_path / "README.md").write_text(f"[guide]({prefix}docs/guide.md#scope)")
    assert link_errors(tmp_path) == [
        f"README.md: missing link {prefix}docs/guide.md#scope"
    ]
    (tmp_path / "docs/guide.md").write_text("# Scope\n")
    assert link_errors(tmp_path) == []
