"""Check registered-type assignments and render a navigable test-obligation matrix.

Assignments are not claims that static API calls establish semantic coverage.
The replay-evidence plugin separately records actual accepted/rejected examples.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from funcprops.verification import _certificate_verifiers
from tools.check_kernel_mutations import CASES
from tools.markdown import normalize_markdown

ROOT = Path(__file__).resolve().parents[1]


def matrix_text():
    data = json.loads((ROOT / "tests/replay_matrix.json").read_text())
    families = data["families"]
    assignments = {}
    for cls, _ in _certificate_verifiers():
        matches = [row for row in families if cls.__module__ in row["modules"]]
        if len(matches) != 1:
            raise ValueError(
                f"expected one matrix assignment for {cls}: {len(matches)}"
            )
        assignments[cls.__module__ + "." + cls.__name__] = matches[0]
    for row in families:
        for selector in row["suites"] + row["shared_contract_suites"]:
            if not (ROOT / selector).is_file():
                raise ValueError(f"missing suite: {selector}")
    lines = [
        "# Replay and consumer test matrix",
        "",
        f"All {len(assignments)} registered concrete replay types have an assigned family.",
        "These assignments locate maintained tests and their intended obligations; they",
        "are not an assertion of complete semantic coverage. The replay-evidence plugin",
        "reports actual accepted/rejected examples by type and test node. Missing",
        "observations remain explicit gaps, distinct from these static assignments.",
        "",
        "## Family obligations",
        "",
        "| Family | Replay | Obligation suites |",
        "| --- | --- | --- |",
    ]
    for row in families:
        links = ", ".join(f"[{Path(p).name}](../../{p})" for p in row["suites"])
        replay = (
            "Independent native witness replay"
            if row["independent_native_replay"]
            else "Declared factory/backend or route-dependent replay"
        )
        lines.append(f"| {row['family']} | {replay} | {links} |")
    lines += [
        "",
        "Each family tracks valid evidence, violated premises or honest decline, source/domain",
        "binding, theorem-relevant field mutations, and its declared replay route. The shared",
        "[result contracts](../../tests/specification/test_result_contracts.py) and",
        "[registered-type rejection tests](../../tests/test_quotient_soundness_audit.py) cover",
        "status semantics and self-attesting subclasses. Cluster/unresolved/accuracy cases",
        "apply to isolation families; not every factory-based record has these fields.",
        "",
        "## Concrete registered types",
        "",
        "| Type | Assigned family |",
        "| --- | --- |",
    ]
    lines += [
        f"| `{name}` | {row['family']} |" for name, row in sorted(assignments.items())
    ]
    lines += [
        "",
        "## Additional coverage dimensions",
        "",
        "The constructed-root tests compare prescribed exact roots, orders and held holes",
        "across real and algebraic routes. Consumer tests check restricted images and",
        "guarded/Piecewise assembly. Kernel mutation probes remove selected source/cover",
        "checks in temporary copies. CI adds cold/warm state, hash seeds, platforms,",
        "dependencies and installed archives. See [testing](../guides/testing.md).",
        "",
    ]
    lines += [
        "",
        "## Executed premise mutation sentinels",
        "",
        "Each baseline must pass; removing its named premise must produce one assertion failure, not a collection or import error. These are selected theorem obligations, not an exhaustive mutation proof.",
        "",
        "| Obligation | Owning module | Sentinel |",
        "| --- | --- | --- |",
    ]
    for name, (module, selector, _mode) in CASES.items():
        path, node = selector.split("::")
        if not (ROOT / path).is_file():
            raise ValueError(f"missing mutation sentinel: {selector}")
        lines.append(f"| {name} | `{module}` | [{node}](../../{path}) |")
    return normalize_markdown("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = matrix_text()
    path = ROOT / "docs/reference/testing-matrix.md"
    if args.check:
        if not path.exists() or path.read_text() != text:
            raise SystemExit(
                "stale testing matrix; run python -m tools.check_test_matrix"
            )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


if __name__ == "__main__":
    main()
