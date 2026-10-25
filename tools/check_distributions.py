"""Build and exercise wheel/sdist artifacts in temporary external harnesses.

Dependencies come from the invoking interpreter; --no-deps makes that choice
explicit. This validates the exact existing dist artifacts when --dist-dir is
passed. It does not publish or rebuild between validation and release upload.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from tools.test_selections import DISTRIBUTION as SUITES

ROOT = Path(__file__).resolve().parents[1]


def run(command, *, cwd, env, log):
    proc = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    log.write_text(proc.stdout + proc.stderr)
    if proc.returncode:
        raise RuntimeError(f"distribution check failed; see {log}")


def source_files(folder):
    return {
        str(p.relative_to(folder)): p.read_bytes()
        for p in folder.rglob("*")
        if p.is_file() and p.suffix in (".py", ".json") and "__pycache__" not in p.parts
    }


def validate_distributions(dist, report_dir):
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("expected exactly one wheel and one source archive")
    artifacts = [wheels[0], sdists[0]]
    summary = []
    for artifact in artifacts:
        names = (
            zipfile.ZipFile(artifact).namelist()
            if artifact.suffix == ".whl"
            else tarfile.open(artifact).getnames()
        )
        if any(
            "__pycache__" in n
            or n.endswith((".pyc", ".DS_Store"))
            or "/validation/" in n
            for n in names
        ):
            raise ValueError(f"unclean distribution: {artifact}")
        if any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
            raise ValueError("unsafe archive member")
        with tempfile.TemporaryDirectory(prefix="funcprops-distribution-") as directory:
            temporary = Path(directory)
            wheel = artifact
            if artifact.suffix != ".whl":
                with tarfile.open(artifact) as archive:
                    if any(not (m.isfile() or m.isdir()) for m in archive.getmembers()):
                        raise ValueError("source archive contains nonregular members")
                    archive.extractall(temporary / "source")
                projects = list((temporary / "source").iterdir())
                if len(projects) != 1:
                    raise ValueError("source archive must have one project root")
                project = projects[0]
                for name in (
                    "README.md",
                    "tools/check_docs.py",
                    "tests/replay_matrix.json",
                    "docs/index.md",
                    "examples/workflow_catalog.py",
                ):
                    if not (project / name).is_file():
                        raise ValueError(f"source archive omitted {name}")
                run(
                    [
                        sys.executable,
                        "-m",
                        "build",
                        "--wheel",
                        "--no-isolation",
                        "--outdir",
                        str(temporary / "built"),
                        str(project),
                    ],
                    cwd=temporary,
                    env=os.environ.copy(),
                    log=report_dir / "sdist-build.log",
                )
                wheel = next((temporary / "built").glob("*.whl"))
            installed = temporary / "installed"
            run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "--no-compile",
                    "--target",
                    str(installed),
                    str(wheel),
                ],
                cwd=temporary,
                env=os.environ.copy(),
                log=report_dir / (artifact.suffix + "-install.log"),
            )
            if source_files(ROOT / "src/funcprops") != source_files(
                installed / "funcprops"
            ):
                raise ValueError("installed module/resource bytes differ from source")
            harness = temporary / "harness"
            harness.mkdir()
            # Source and CI files are link targets only. PYTHONPATH below selects
            # the installed package, and the plugin checks that import location.
            for name in ("tests", "tools", "examples", "docs", "src", ".github"):
                shutil.copytree(
                    ROOT / name,
                    harness / name,
                    ignore=shutil.ignore_patterns("__pycache__", ".hypothesis"),
                )
            shutil.copy2(ROOT / "README.md", harness / "README.md")
            shutil.copy2(ROOT / "LICENSE", harness / "LICENSE")
            env = os.environ.copy()
            env["PYTHONPATH"] = os.pathsep.join([str(installed), str(harness)])
            env["FUNCPROPS_EXPECTED_PACKAGE_ROOT"] = str(installed)
            env.pop("FUNCPROPS_REPLAY_EVIDENCE", None)
            xml = report_dir / (artifact.suffix + "-behavior.xml")
            run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "tools.replay_evidence",
                    *SUITES,
                    "--junitxml=" + str(xml),
                ],
                cwd=harness,
                env=env,
                log=report_dir / (artifact.suffix + "-behavior.log"),
            )
            summary.append(
                {
                    "artifact": artifact.name,
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    "behavior": "passed",
                    "external_harness": True,
                    "source_resource_identity": True,
                }
            )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", type=Path, default=Path("validation/package"))
    parser.add_argument("--dist-dir", type=Path)
    args = parser.parse_args()
    output = args.report_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    dist = args.dist_dir.resolve() if args.dist_dir else output / "dist"
    if args.dist_dir is None:
        if dist.exists():
            shutil.rmtree(dist)
        run(
            [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(dist)],
            cwd=ROOT,
            env=os.environ.copy(),
            log=output / "build.log",
        )
    run(
        [
            sys.executable,
            "-m",
            "twine",
            "check",
            *[str(p) for p in sorted(dist.iterdir())],
        ],
        cwd=ROOT,
        env=os.environ.copy(),
        log=output / "metadata.log",
    )
    results = validate_distributions(dist, output)
    (output / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results))


if __name__ == "__main__":
    main()
