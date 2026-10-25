"""Build task tutorials, example index and notebook from checked literate examples."""

import argparse
import ast
import inspect
import json
from pathlib import Path

import funcprops as fp
from examples.workflow_catalog import WORKFLOWS
from tools.build_tutorial_notebook import code, md
from tools.markdown import normalize_markdown

ROOT = Path(__file__).resolve().parents[1]


def workflow_sections(source):
    """Split executable Python at section markers, retaining prose beside each block."""
    tree = ast.parse(source)
    if ast.get_docstring(tree) is not None:
        source = "".join(
            source.splitlines(keepends=True)[tree.body[0].end_lineno :]
        ).lstrip()
    sections = []
    title = "Example"
    prose = []
    lines = []
    for line in source.splitlines():
        if line.startswith("# %% "):
            if any(v.strip() for v in lines):
                sections.append(
                    (title, " ".join(prose), "\n".join(lines).strip() + "\n")
                )
            title = line[5:].strip()
            prose = []
            lines = []
        elif line.startswith("#| "):
            prose.append(line[3:])
        else:
            lines.append(line)
    if any(v.strip() for v in lines):
        sections.append((title, " ".join(prose), "\n".join(lines).strip() + "\n"))
    return sections


def generated_files():
    """Assemble tutorials, indexed examples and ordered notebook sessions."""
    files = {}
    notes = json.loads((ROOT / "examples/workflow_notes.json").read_text())
    if set(notes) != {case.slug for case in WORKFLOWS}:
        raise ValueError("workflow notes must match the catalog")
    index = [
        "# Workflow tutorials",
        "",
        "Choose a task and run its checked example. Each workflow starts fresh; its sections run in order. See [result contracts](../reference/result-contracts.md).",
        "",
        "| Task | Topic | Level |",
        "| --- | --- | --- |",
    ]
    examples = [
        "# Runnable examples",
        "",
        "Install the package and run an example from the checkout root, such as `python examples/restricted_domains.py`. Each file is a self-contained session with exact mathematical assertions. The tutorials and notebook are generated from these same sources.",
        "",
        "| Task | Example | Level |",
        "| --- | --- | --- |",
    ]
    cells = [
        md(
            "# Certified workflows\n\nEach workflow is self-contained; run its sections in order. See the [tutorial index](../tutorials/index.md) and [result contracts](../reference/result-contracts.md)."
        )
    ]
    for case in sorted(
        WORKFLOWS,
        key=lambda c: (
            {"introductory": 0, "intermediate": 1, "advanced": 2}[
                notes[c.slug]["level"]
            ],
            c.title,
        ),
    ):
        info = notes[case.slug]
        sections = workflow_sections((ROOT / "examples" / case.filename).read_text())
        index.append(
            f"| [{case.title}]({case.slug}.md) | {info['topic']} | {info['level']} |"
        )
        examples.append(
            f"| {info['question']} | [{case.filename}]({case.filename}) | {info['level']} |"
        )
        intro = f"# {case.title}\n\n{info['question']}\n\n{case.scope}\n\nRun `python examples/{case.filename}` from the checkout. Each section belongs to one ordered session.\n\n<!-- workflow-id: {case.slug} -->\n"
        parts = [intro]
        cells.append(
            md(
                f"## {case.title}\n\n<!-- workflow-id: {case.slug} -->\n\n{info['question']}\n\n{case.scope}"
            )
        )
        for title, prose, source in sections:
            parts.append(f"\n## {title}\n\n{prose}\n\n```python\n{source}```\n")
            if prose:
                cells.append(md(f"### {title}\n\n{prose}"))
            cell = code(source)
            cell["metadata"]["workflow_id"] = case.slug
            cells.append(cell)
        ending = f"\n## Expected result\n\n{info['expected']}\n\n{info['interpretation']}\n\n## Scope and next steps\n\n{info['limits']} See [troubleshooting](../troubleshooting.md), [result contracts](../reference/result-contracts.md), [capabilities](../capabilities.md), and [all tutorials](index.md).\n"
        parts.append(ending)
        files[f"docs/tutorials/{case.slug}.md"] = "\n".join(parts)
        cells.append(
            md(
                f"Expected: {info['expected']}\n\n{info['interpretation']}\n\nScope: {info['limits']}"
            )
        )
    files["docs/tutorials/index.md"] = "\n".join(index) + "\n"
    examples += [
        "",
        "Edit the Python example and `workflow_notes.json`, then run `python -m tools.build_workflow_docs` to regenerate the [tutorials](../docs/tutorials/index.md) and [notebook](../docs/notebooks/certified-workflows.ipynb). Section markers keep explanations beside the corresponding source.",
        "",
        "The property reference and property tour use `property_examples.py`. See [testing](../docs/guides/testing.md) for the execution gates.",
    ]
    files["examples/README.md"] = "\n".join(examples) + "\n"
    files["docs/notebooks/certified-workflows.ipynb"] = (
        json.dumps(
            {
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
            },
            indent=1,
        )
        + "\n"
    )
    properties = {name for name, *_ in fp.properties()}
    lines = [
        "# Public helper reference",
        "",
        "Signatures and implementation docstrings are generated from exported functions. The [helper and proof contracts](helper-contracts.md) describe accepted inputs, return records, completion and replay boundaries. Read the [result contracts](result-contracts.md) before consuming a proof.",
        "",
    ]
    for name in sorted(fp.__all__):
        obj = getattr(fp, name)
        if not inspect.isfunction(obj) or name in properties:
            continue
        signature = inspect.signature(obj)
        doc = (
            inspect.getdoc(obj)
            or "See the scoped contract and implementation for this helper."
        )
        lines += [f"## {name}", "", "```text", f"{name}{signature}", "```", "", doc, ""]
    files["docs/reference/helpers.md"] = "\n".join(lines) + "\n"
    return {
        name: normalize_markdown(text) if name.endswith(".md") else text
        for name, text in files.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = generated_files()
    extra = sorted(
        str(p.relative_to(ROOT))
        for p in (ROOT / "docs/tutorials").glob("*.md")
        if str(p.relative_to(ROOT)) not in files
    )
    if extra:
        raise SystemExit(f"tutorials without a workflow source: {extra}")
    stale = []
    for name, text in files.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if stale:
        raise SystemExit(f"stale generated workflows/helpers: {stale}")


if __name__ == "__main__":
    main()
