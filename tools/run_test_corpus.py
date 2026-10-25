"""Run bounded fresh-process test files, preserving logs and replay observations."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_file(path, output, *, timeout, package_root, evidence, seed):
    relative = path.relative_to(ROOT)
    stem = str(relative).replace("/", "__")
    xml = output / (stem + ".xml")
    observed = output / (stem + ".replay.json")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(package_root), str(ROOT)])
    env["PYTHONHASHSEED"] = seed
    env["FUNCPROPS_EXPECTED_PACKAGE_ROOT"] = str(package_root)
    if evidence:
        env["FUNCPROPS_REPLAY_EVIDENCE"] = str(observed)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        str(relative),
        "--junitxml=" + str(xml),
    ]
    if evidence:
        command += ["-p", "tools.replay_evidence"]
    start = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        log = proc.stdout + proc.stderr
        result = {
            "file": str(relative),
            "status": "passed" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
        }
        if xml.exists():
            suites = list(ET.parse(xml).getroot().iter("testsuite"))
            result.update(
                {
                    key: sum(int(s.get(key, 0)) for s in suites)
                    for key in ("tests", "failures", "errors", "skipped")
                }
            )
    except subprocess.TimeoutExpired as error:
        result = {"file": str(relative), "status": "timeout"}
        log = error.stdout or ""
        if isinstance(log, bytes):
            log = log.decode(errors="replace")
    (output / (stem + ".log")).write_text(log)
    result["seconds"] = round(time.monotonic() - start, 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--report-dir", type=Path, default=Path("validation/source"))
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--package-root", type=Path, default=ROOT / "src")
    parser.add_argument("--evidence", action="store_true")
    parser.add_argument("--require-replay-types", action="store_true")
    parser.add_argument("--seed", default="3")
    args = parser.parse_args()
    if args.require_replay_types and not args.evidence:
        parser.error("--require-replay-types requires --evidence")
    if args.workers < 1 or args.timeout <= 0:
        parser.error("workers and timeout must be positive")
    output = args.report_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    paths = [p.resolve() for p in args.files] or sorted(
        (ROOT / "tests").rglob("test_*.py")
    )
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                run_file,
                p,
                output,
                timeout=args.timeout,
                package_root=args.package_root.resolve(),
                evidence=args.evidence,
                seed=args.seed,
            )
            for p in paths
        ]
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            print(row["status"], row["file"], row.get("tests", 0), flush=True)
            (output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    totals = {
        key: sum(r.get(key, 0) for r in results)
        for key in ("tests", "failures", "errors", "skipped")
    }
    totals.update(
        files=len(results),
        timeouts=sum(r["status"] == "timeout" for r in results),
        failed_files=sum(r["status"] != "passed" for r in results),
    )
    totals["passed"] = (
        totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    )
    (output / "summary.json").write_text(json.dumps(totals, indent=2) + "\n")
    if args.evidence:
        observed = {}
        for path in output.glob("*.replay.json"):
            for name, row in json.loads(path.read_text()).items():
                target = observed.setdefault(
                    name, {"accepted": set(), "rejected": set()}
                )
                for key in target:
                    target[key].update(row[key])
        report = {
            name: {k: sorted(v) for k, v in row.items()}
            for name, row in sorted(observed.items())
        }
        (output / "replay-observations.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        gaps = {
            name: [k for k, v in row.items() if not v]
            for name, row in report.items()
            if any(not v for v in row.values())
        }
        (output / "replay-observation-gaps.json").write_text(
            json.dumps(gaps, indent=2) + "\n"
        )
    print(json.dumps(totals), flush=True)
    if totals["failed_files"] or (args.require_replay_types and gaps):
        if args.require_replay_types and gaps:
            print("missing accepted/rejected replay fixtures:", sorted(gaps))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
