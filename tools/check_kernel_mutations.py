"""Require selected regression sentinels to kill removed checker obligations.

Each mutant runs in a temporary source copy. A baseline must pass; collection or
import errors are not accepted as killing a mutant. Production files are untouched.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "omitted-domain": (
        "coverage_checker.py",
        "tests/certificates/test_kernel_obligations.py::test_omitted_domain_is_rejected_even_with_recomputed_totals",
        "omitted-domain-cells",
    ),
    "overlapping-domain": (
        "coverage_checker.py",
        "tests/certificates/test_kernel_obligations.py::test_duplicate_domain_is_rejected_even_with_recomputed_totals",
        "overlapping-or-duplicated-cells",
    ),
    "source-context": (
        "coverage_checker.py",
        "tests/certificates/test_kernel_obligations.py::test_changed_source_syntax_cannot_rebind_every_leaf",
        None,
    ),
    "coefficient-embedding": (
        "algebraic_coefficients.py",
        "tests/test_proof_obligations.py::test_unique_coefficient_root",
        "coefficient-embedding",
    ),
    "owned-value": (
        "metric_proofs.py",
        "tests/test_proof_obligations.py::test_owned_value_with_consistent_total",
        "owned-value",
    ),
    "parameter-premise": (
        "parameter_geometry.py",
        "tests/test_proof_obligations.py::test_parameter_premise",
        "parameter-premise",
    ),
    "geometry-source": (
        "parameter_geometry.py",
        "tests/test_proof_obligations.py::test_geometry_source_events",
        "geometry-source",
    ),
    "overlap-identity": (
        "branch_gluing.py",
        "tests/test_proof_obligations.py::test_anchor_is_not_identity",
        "overlap-identity",
    ),
    "held-transport": (
        "work_budget.py",
        "tests/test_source_transport.py::test_worker_domain_hole",
        "held-transport",
    ),
}


def mutate(source, reason):
    tree = ast.parse(source)
    if reason in {
        "coefficient-embedding",
        "owned-value",
        "parameter-premise",
        "geometry-source",
        "overlap-identity",
        "held-transport",
    }:
        return mutate_extension(tree, reason)
    changed = 0
    for node in ast.walk(tree):
        if (
            reason is None
            and isinstance(node, ast.FunctionDef)
            and node.name == "_context_status"
        ):
            node.body = [ast.Return(value=ast.Constant(value=None))]
            changed += 1
        if (
            reason
            and isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Constant) and child.value == reason
                for statement in node.body
                for child in ast.walk(statement)
            )
        ):
            # Select the innermost guard whose direct rejection carries this reason.
            if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
                node.test = ast.Constant(value=False)
                changed += 1
    if changed != 1:
        raise RuntimeError(f"expected one mutation site, found {changed}: {reason}")
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"


def mutate_extension(tree, mode):
    """Remove one named extension premise; syntax/import failures cannot kill it."""
    changed = 0
    for node in ast.walk(tree):
        if (
            mode == "coefficient-embedding"
            and isinstance(node, ast.Compare)
            and any(
                isinstance(n, ast.Attribute) and n.attr == "count_roots"
                for n in ast.walk(node)
            )
        ):
            node.left = ast.Constant(value=1)
            changed += 1
        elif (
            mode == "owned-value"
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "same_data"
            and node.args
            and isinstance(node.args[0], ast.Attribute)
            and node.args[0].attr == "points"
        ):
            node.func = ast.Name(id="bool", ctx=ast.Load())
            node.args = [ast.Constant(value=True)]
            changed += 1
        elif (
            mode == "geometry-source"
            and isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Attribute)
            and node.test.left.attr == "events"
        ):
            node.test = ast.Constant(value=False)
            changed += 1
        elif (
            mode == "overlap-identity"
            and isinstance(node, ast.FunctionDef)
            and node.name == "_derivative_identity"
        ):
            statement = next(n for n in node.body if isinstance(n, ast.Return))
            statement.value = statement.value.values[-1]
            changed += 1
        elif (
            mode == "parameter-premise"
            and isinstance(node, ast.FunctionDef)
            and node.name == "specialize"
        ):
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "coordinate_domain_compatible"
                ):
                    call.func = ast.Name(id="bool", ctx=ast.Load())
                    call.args = [ast.Constant(value=True)]
                    changed += 1
        elif (
            mode == "held-transport"
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_dumps"
        ):
            node.func = ast.Attribute(
                value=ast.Name(id="pickle", ctx=ast.Load()),
                attr="dumps",
                ctx=ast.Load(),
            )
            changed += 1
    expected = 3 if mode == "held-transport" else 1
    if changed != expected:
        raise RuntimeError(
            f"expected {expected} mutation sites, found {changed}: {mode}"
        )
    return ast.unparse(ast.fix_missing_locations(tree)) + "\n"


def run_probe(source, name, output):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(source), str(ROOT)])
    xml = output / f"{name}.xml"
    node = CASES[name][1]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", node, "--junitxml=" + str(xml)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    (output / f"{name}.log").write_text(proc.stdout + proc.stderr)
    suites = list(ET.parse(xml).getroot().iter("testsuite"))
    return proc.returncode, {
        k: sum(int(s.get(k, 0)) for s in suites)
        for k in ("tests", "failures", "errors", "skipped")
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("validation/kernel-mutations.json")
    )
    args = parser.parse_args()
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    output = args.report.parent / "kernel-mutants"
    output.mkdir(exist_ok=True)
    baseline = []
    for name in CASES:
        code, counts = run_probe(ROOT / "src", name, output)
        if code or counts != {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}:
            raise SystemExit(f"mutation baseline failed: {name}")
        baseline.append(name)
    results = []
    for name, (module, _, reason) in CASES.items():
        with tempfile.TemporaryDirectory(prefix="funcprops-mutant-") as directory:
            source = Path(directory) / "src"
            shutil.copytree(
                ROOT / "src",
                source,
                ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
            )
            checker = source / "funcprops" / module
            checker.write_text(mutate(checker.read_text(), reason))
            code, counts = run_probe(source, name, output)
            killed = code == 1 and counts == {
                "tests": 1,
                "failures": 1,
                "errors": 0,
                "skipped": 0,
            }
            results.append({"mutant": name, "killed": killed, **counts})
    args.report.write_text(
        json.dumps({"baseline_passed": baseline, "mutants": results}, indent=2) + "\n"
    )
    print(json.dumps(results))
    if not all(r["killed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
