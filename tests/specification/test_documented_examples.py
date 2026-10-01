import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
DOCS = [
    ROOT / "docs" / "complex_analysis.md",
    ROOT / "docs" / "homotopy.md",
    ROOT / "docs" / "examples.md",
]


def python_blocks(path):
    text = path.read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


@pytest.mark.parametrize(
    "path,source",
    [(path, source) for path in DOCS for source in python_blocks(path)],
    ids=lambda value: value.name if isinstance(value, Path) else None,
)
def test_examples_execute(path, source):
    namespace = {"__name__": "__documentation_example__"}
    exec(compile(source, str(path), "exec"), namespace)
