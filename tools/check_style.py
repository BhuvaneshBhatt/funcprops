"""Check source and documentation conventions that complement Ruff."""

import ast
import re
from pathlib import Path
from urllib.parse import urlsplit

from tools.markdown import normalize_markdown

ROOT = Path(__file__).resolve().parents[1]


def style_errors(root=ROOT):
    """Return actionable source, naming and Markdown consistency failures."""
    errors = []
    paths = [
        p
        for p in root.rglob("*")
        if p.is_file()
        and not any(
            part.startswith(".")
            or part in {"build", "dist", "__pycache__"}
            or part.endswith(".egg-info")
            for part in p.relative_to(root).parts
        )
    ]
    for path in paths:
        relative = path.relative_to(root)
        if re.search(r"_(?:m|i|s)\d(?:_|\.)", path.name):
            errors.append(f"{relative}: use a mathematical task name")
        if path.suffix not in {
            ".py",
            ".md",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
            ".txt",
            ".in",
        }:
            continue
        text = path.read_text()
        if any(line != line.rstrip() for line in text.splitlines()):
            errors.append(f"{relative}: trailing whitespace")
        if path.suffix == ".md" and text != normalize_markdown(text):
            errors.append(
                f"{relative}: wrapped prose or inconsistent paragraph spacing"
            )
        if path.suffix != ".py":
            continue
        tree = ast.parse(text, filename=str(path))
        source = relative.parts[0] == "src"
        for scope in ast.walk(tree):
            if isinstance(scope, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                names = set()
                for node in scope.body:
                    if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        continue
                    if node.name in names:
                        errors.append(
                            f"{relative}:{node.lineno}: overridden definition {node.name}"
                        )
                    names.add(node.name)
            if source and isinstance(scope, ast.Assert):
                errors.append(f"{relative}:{scope.lineno}: use explicit validation")
        if source:
            for node in tree.body:
                if (
                    isinstance(node, (ast.FunctionDef, ast.ClassDef))
                    and not node.name.startswith("_")
                    and not ast.get_docstring(node)
                ):
                    errors.append(
                        f"{relative}:{node.lineno}: undocumented public definition {node.name}"
                    )
    for target in re.findall(r"\]\(([^)]+)\)", (root / "README.md").read_text()):
        if not urlsplit(target).scheme:
            errors.append(f"README.md: relative link {target}")
    return errors


def main():
    errors = style_errors()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Source and Markdown conventions passed")


if __name__ == "__main__":
    main()
