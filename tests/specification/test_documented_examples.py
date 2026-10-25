"""All Python documentation fences are executable ordered page sessions."""

import pytest

from tools.check_docs import documents, execute_document, link_errors, python_blocks


@pytest.mark.parametrize(
    "path", [p for p in documents() if list(python_blocks(p))], ids=lambda p: p.stem
)
def test_examples_execute(path):
    assert execute_document(path) > 0


def test_local_documentation_links_and_anchors():
    assert link_errors() == []
