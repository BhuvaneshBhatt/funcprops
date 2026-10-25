"""Run repository-contained validation profiles and retain precise results."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from tools.test_selections import QUICK

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", choices=("quick", "full", "package"), default="quick"
    )
    parser.add_argument("--report-dir", type=Path, default=Path("validation/latest"))
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error("validation requires assertions enabled (no -O)")
    output = args.report_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "src"), str(ROOT)])
    steps = []

    def run(name, command, timeout=1200):
        start = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            status = "passed" if proc.returncode == 0 else "failed"
            (output / (name + ".log")).write_text(proc.stdout + proc.stderr)
            code = proc.returncode
        except subprocess.TimeoutExpired as error:
            status = "timeout"
            code = None
            value = error.stdout or ""
            (output / (name + ".log")).write_text(
                value.decode(errors="replace") if isinstance(value, bytes) else value
            )
        steps.append(
            {
                "step": name,
                "status": status,
                "exit_code": code,
                "seconds": round(time.monotonic() - start, 3),
            }
        )
        (output / "steps.json").write_text(json.dumps(steps, indent=2) + "\n")
        print(name, status, flush=True)
        return status == "passed"

    python = [sys.executable]
    ruff = [*python, "-m", "ruff"]
    if args.profile != "package":
        for module in (
            "build_property_docs",
            "build_tutorial_notebook",
            "build_workflow_docs",
            "check_test_matrix",
            "update_proof_inventory",
            "check_ci",
            "build_helper_docs",
        ):
            run(module, [*python, "-m", "tools." + module, "--check"])
        run("style", [*python, "-m", "tools.check_style"])
        run("links", [*python, "-m", "tools.check_docs", "--links-only"])
        run(
            "registry-coverage",
            [
                *python,
                str(ROOT / "tools/registry_coverage/coverage_matrix.py"),
                "--check",
            ],
        )
        run(
            "lint",
            [*ruff, "check", "src", "tests", "tools", "examples", "docs/notebooks"],
        )
        run(
            "format",
            [
                *ruff,
                "format",
                "--check",
                "src",
                "tests",
                "tools",
                "examples",
            ],
        )
        run(
            "compilation",
            [*python, "-m", "compileall", "-q", "src", "tests", "tools", "examples"],
        )
        if args.profile == "quick":
            run(
                "contracts",
                [
                    *python,
                    "-m",
                    "pytest",
                    "-q",
                    *QUICK,
                    "--junitxml=" + str(output / "contracts.xml"),
                ],
            )
        else:
            run(
                "documentation",
                [
                    *python,
                    "-m",
                    "tools.check_docs",
                    "--report",
                    str(output / "docs.json"),
                ],
            )
            run(
                "source",
                [
                    *python,
                    "-m",
                    "tools.run_test_corpus",
                    "--evidence",
                    "--require-replay-types",
                    "--report-dir",
                    str(output / "source"),
                ],
                timeout=7200,
            )
            for seed in ("3", "17"):
                env["PYTHONHASHSEED"] = seed
                run(
                    "warm-" + seed,
                    [
                        *python,
                        "-m",
                        "tools.run_selected_tests",
                        "warm",
                        "--junitxml=" + str(output / ("warm-" + seed + ".xml")),
                    ],
                )
            run(
                "kernel-mutations",
                [
                    *python,
                    "-m",
                    "tools.check_kernel_mutations",
                    "--report",
                    str(output / "kernel-mutations.json"),
                ],
            )
            run(
                "proof-performance",
                [
                    *python,
                    "-m",
                    "tools.benchmark_proofs",
                    "--report",
                    str(output / "proof-performance.json"),
                ],
            )
            run(
                "root-benchmark",
                [
                    *python,
                    "-m",
                    "tools.benchmark_roots",
                    "--report",
                    str(output / "root-benchmarks.json"),
                ],
            )
    if args.profile in ("full", "package"):
        run(
            "distributions",
            [
                *python,
                "-m",
                "tools.check_distributions",
                "--report-dir",
                str(output / "package"),
            ],
            timeout=3600,
        )
    versions = {}
    for name in (
        "sympy",
        "mpmath",
        "semialg",
        "algroots",
        "exprtest",
        "pytest",
        "hypothesis",
        "ruff",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    summary = {
        "profile": args.profile,
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": versions,
        "steps": steps,
        "passed": all(s["status"] == "passed" for s in steps),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
