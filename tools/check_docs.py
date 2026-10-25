"""Execute every Python fence and notebook; validate local links and anchors.

Each Markdown page is an ordered session in a fresh namespace/process.
Use text fences for signatures or pseudocode. No Python fences are skipped.
Remote links are not fetched. Run as python -m tools.check_docs from a checkout.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^(`{3,}|~{3,})([^\n]*)\n(.*?)^\1\s*$", re.M | re.S)
REPOSITORY_PATH = "/BhuvaneshBhatt/funcprops/blob/main/"


def documents(root=ROOT):
    return [root / "README.md", *sorted((root / "docs").rglob("*.md"))]


def python_blocks(path):
    text = path.read_text(encoding="utf-8")
    opening = None
    source = []
    for line, value in enumerate(text.splitlines(keepends=True), 1):
        if opening is None:
            match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\n]*)", value)
            if match:
                opening = (match[1], match[2].strip(), line + 1)
                source = []
        elif re.fullmatch(
            r" {0,3}"
            + re.escape(opening[0][0])
            + "{"
            + str(len(opening[0]))
            + r",}\s*",
            value,
        ):
            _, language, start = opening
            if language.split()[:1] in (["python"], ["py"]):
                if language not in ("python", "py"):
                    raise ValueError(f"{path}: unsupported Python fence: {language}")
                yield start, "".join(source)
            opening = None
        else:
            source.append(value)
    if opening is not None:
        raise ValueError(f"{path}: unclosed fence starting at line {opening[2] - 1}")


def execute_document(path):
    if sys.flags.optimize:
        raise RuntimeError("documentation checks require assertions enabled")
    namespace = {"__name__": "__documentation_example__"}
    blocks = list(python_blocks(path))
    with contextlib.redirect_stdout(io.StringIO()):
        for line, source in blocks:
            tree = ast.parse("\n" * (line - 1) + source, filename=str(path))
            exec(compile(tree, str(path), "exec"), namespace)
    return len(blocks)


def execute_notebook(path):
    if sys.flags.optimize:
        raise RuntimeError("notebook checks require assertions enabled")
    namespace = {"__name__": "__documentation_example__"}
    count = 0
    with contextlib.redirect_stdout(io.StringIO()):
        for cell in json.loads(path.read_text())["cells"]:
            if cell["cell_type"] == "code":
                exec(compile("".join(cell["source"]), str(path), "exec"), namespace)
                count += 1
    return count


def headings(text):
    text = FENCE.sub("", text)
    used = {}
    anchors = set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        title = re.sub(r"<[^>]+>", "", match[1]).lower()
        slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        index = used.get(slug, 0)
        used[slug] = index + 1
        anchors.add(slug if not index else f"{slug}-{index}")
    return anchors


def link_errors(root=ROOT):
    errors = []
    paths = documents(root) + sorted((root / "docs").rglob("*.ipynb"))
    for path in paths:
        text = path.read_text()
        if path.suffix == ".ipynb":
            text = "\n".join(
                "".join(c["source"])
                for c in json.loads(text)["cells"]
                if c["cell_type"] == "markdown"
            )
        text = FENCE.sub("", text)
        links = re.findall(r"\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", text)
        links += re.findall(r"^\[[^\]]+\]:\s*(\S+)", text, re.M)
        for raw in links:
            url = urlsplit(raw.strip("<>"))
            if url.netloc == "github.com" and url.path.startswith(REPOSITORY_PATH):
                target = root / unquote(url.path.removeprefix(REPOSITORY_PATH))
            elif url.scheme or url.netloc:
                continue
            else:
                target = (
                    (path.parent / unquote(url.path)).resolve() if url.path else path
                )
            if not target.exists():
                errors.append(f"{path.relative_to(root)}: missing link {raw}")
            elif url.fragment and target.suffix == ".md":
                if unquote(url.fragment) not in headings(target.read_text()):
                    errors.append(f"{path.relative_to(root)}: missing anchor {raw}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--links-only", action="store_true")
    parser.add_argument("--document", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.document:
        run = execute_notebook if args.document.suffix == ".ipynb" else execute_document
        print(run(args.document))
        return
    errors = link_errors()
    results = []
    if not args.links_only:
        paths = [p for p in documents() if list(python_blocks(p))]
        paths += sorted((ROOT / "docs").rglob("*.ipynb"))
        for path in paths:
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "tools.check_docs", "--document", str(path)],
                    cwd=ROOT,
                    env=os.environ.copy(),
                    capture_output=True,
                    text=True,
                    timeout=args.timeout,
                    check=False,
                )
                ok = proc.returncode == 0
                blocks = int(proc.stdout.strip()) if ok else 0
                if not ok:
                    errors.append(f"{path.relative_to(ROOT)}:\n{proc.stderr}")
                results.append(
                    {
                        "path": str(path.relative_to(ROOT)),
                        "blocks": blocks,
                        "passed": ok,
                    }
                )
            except subprocess.TimeoutExpired:
                errors.append(f"{path.relative_to(ROOT)}: timeout")
                results.append({"path": str(path.relative_to(ROOT)), "passed": False})
    summary = {
        "documents": results,
        "errors": errors,
        "checked_blocks": sum(r.get("blocks", 0) for r in results),
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
