"""Validate workflow test selectors and the shared test catalog without network access."""

import argparse
import re
from pathlib import Path

from tools.test_selections import GROUPS

ROOT = Path(__file__).resolve().parents[1]


def selection_errors(root=ROOT, groups=GROUPS):
    """Report missing test paths, repeated selections and unknown CI groups."""
    errors = []
    for group, selectors in groups.items():
        if len(selectors) != len(set(selectors)):
            errors.append(f"{group}: repeated selectors")
        for selector in selectors:
            if not (root / selector.split("::", 1)[0]).is_file():
                errors.append(f"{group}: missing selector {selector}")
    for workflow in sorted(
        [
            *(root / ".github/workflows").glob("*.yml"),
            *(root / ".github/workflows").glob("*.yaml"),
        ]
    ):
        text = workflow.read_text()
        for selector in sorted(set(re.findall(r"tests/[\w./-]+\.py", text))):
            if not (root / selector).is_file():
                errors.append(f"{workflow.name}: missing selector {selector}")
        for group in re.findall(r"tools\.run_selected_tests\s+([\w-]+)", text):
            if group not in groups:
                errors.append(f"{workflow.name}: unknown test group {group}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = selection_errors()
    if errors:
        raise SystemExit("\n".join(errors))
    print("CI selectors and shared test selections passed")


if __name__ == "__main__":
    main()
