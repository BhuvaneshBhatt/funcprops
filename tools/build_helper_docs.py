"""Generate scoped helper contracts and concrete replay-record field references."""

import argparse
import importlib
import inspect
import json
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path

import funcprops as fp
from funcprops.verification import _certificate_verifiers
from tools.markdown import normalize_markdown

ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "expression": "Original expression bound to this theorem; source holes remain relevant.",
    "variable": "Analysis coordinate and its intrinsic assumptions.",
    "requested": "Original requested set or rectangle cover.",
    "effective": "Source-defined subset of the requested domain.",
    "domain": "Domain of this concrete claim; consult the route for requested/effective semantics.",
    "parameters": "Parameter coordinates, including their intrinsic assumptions.",
    "parameter_domain": "Explicit guard restricting the parameter family.",
    "events": "Bound polynomial coefficients and exact trace/discriminant event data.",
    "cells": "Certified local cells; their union and ownership are separate obligations.",
    "points": "Every retained owned coordinate/value pair, in the checked order.",
    "seams": "Owned branch-boundary and one-sided data.",
    "ratios": "All retained finite pairwise secant slopes.",
    "values": "Exact values at every retained finite source point.",
    "constant": "The claimed metric constant; optimality requires its own theorem.",
    "optimal": "Whether the supported optimality claim is proved; separate from replay support.",
    "total_variation": "Claimed sum of certified motion and all owned excursions.",
    "proof": "Underlying proof that must agree with this public summary.",
    "evidence": "Route-specific witnesses; their presence alone is not successful replay.",
    "unresolved": "Regions or obligations with no exhaustive conclusion.",
    "rectangle": "Rational rectangle on which the local claim applies.",
    "charts": "Supplied local chart records bound to this assembly.",
    "overlaps": "Every required touching overlap and its equality/disagreement status.",
    "relation": "Entire implicit equation defining the local branch family.",
    "value_symbol": "Dependent coordinate in the implicit relation.",
    "formula": "Supplied local recipe before selected logarithms are substituted.",
    "logarithms": "Placeholder/selected-logarithm chart pairs.",
    "units": "Source-bound zero-exclusion witnesses for supported denominators.",
    "generator": "Auxiliary real algebraic coordinate.",
    "root": "Selected exact root or algebraic embedding under this concrete theorem.",
    "polynomial": "Rational polynomial constraining the auxiliary generator or local source.",
    "interval": "Exact interval supporting this local claim or root selection.",
    "representations": "Exact coefficient formulas in the selected generator.",
    "transformed": "Source-preserving auxiliary expressions.",
    "inputs": "Original expressions and restrictions bound to the encoding.",
    "variables": "Declared query coordinates.",
    "center": "Iteration center for a contraction or geometric center for a contour; a Krawczyk center need not be a root.",
    "tested": "Recorded search work; it is not proof of coverage.",
    "exhaustion": "Resource limit or unresolved-obligation reason.",
    "complete": "Stored completion claim; its theorem premises still require replay.",
    "certified": "Stored or derived certification status, meaningful under the replay contract.",
    "root_count": "Distinct-root count when established, separate from multiplicity.",
    "multiplicity_count": "Count with multiplicity when established.",
    "zero_count": "Local zero count under this concrete contour/root theorem.",
    "schema_version": "Record schema identifier; a matching number is not a proof.",
    "source": "Route identifier or source-context record; consult this type's docstring.",
}


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def reference_text():
    """Build scoped contracts and constructor/status tables for registered records."""
    metadata = json.loads((ROOT / "tools/helper_reference.json").read_text())
    lines = [
        "# Helper and proof contracts",
        "",
        "Use the [helper reference](helpers.md) for signatures and full implementation docstrings, the [property reference](../properties/index.md) for compact queries, and the [result contracts](result-contracts.md) for shared meanings. The contracts below describe common assembly interfaces; each concrete record retains its own theorem scope.",
        "",
        "## Scoped helper interfaces",
        "",
    ]
    for name, info in metadata.items():
        if name not in fp.__all__:
            raise ValueError(f"contract for missing export: {name}")
        lines += [
            f"### {name}",
            "",
            "| Contract | Meaning |",
            "| --- | --- |",
            *(
                f"| {label} | {info[key]} |"
                for key, label in [
                    ("inputs", "Accepted inputs"),
                    ("returns", "Return value"),
                    ("replay", "Replay and completion"),
                    ("failure", "Failure and limits"),
                ]
            ),
            "",
        ]
    manifest = {r["type"]: r for r in fp.proof_api_manifest()["records"]}
    lines += [
        "## Concrete replay records",
        "",
        "The following inventory includes every registered concrete replay type, inventoried proof record and public dataclass. Nested data records require their owning checker and do not gain standalone replay from appearing here. Fields shown are constructor data, not a universal result schema. Derived properties such as coverage_complete and gluing_complete are described by the owning contract and class docstring. A record can verify while remaining incomplete. Search metadata is not automatically a theorem premise.",
        "",
    ]
    records = {
        cls.__module__ + "." + cls.__name__: cls for cls, _ in _certificate_verifiers()
    }
    for name in manifest:
        module, _, class_name = name.rpartition(".")
        records[name] = getattr(importlib.import_module(module), class_name)
    for name in fp.__all__:
        cls = getattr(fp, name)
        if inspect.isclass(cls) and is_dataclass(cls):
            records[cls.__module__ + "." + cls.__name__] = cls
    for name, cls in sorted(records.items()):
        info = manifest.get(
            name,
            {
                "contract": "nested-or-summary-data",
                "replay_mode": "no-registered-standalone-replay",
            },
        )
        lines += [
            f"### {name}",
            "",
            inspect.getdoc(cls) or "See the owning module for this concrete theorem.",
            "",
            f"Replay contract: `{info['contract']}`; mode: `{info['replay_mode']}`.",
            "",
        ]
        if is_dataclass(cls):
            lines += ["| Field | Default | Role |", "| --- | --- | --- |"]
            for f in fields(cls):
                default = (
                    "required"
                    if f.default is MISSING and f.default_factory is MISSING
                    else cell(f.default)
                    if f.default is not MISSING
                    else "factory"
                )
                role = ROLES.get(
                    f.name,
                    "Theorem or context data interpreted by this concrete record; inspect its owning checker before changing it.",
                )
                lines.append(f"| `{f.name}` | `{default}` | {role} |")
        else:
            lines += [
                "Constructor data and derived fields are documented by the class and its owning interface."
            ]
        status = [
            name
            for name in (
                "complete",
                "coverage_complete",
                "isolation_complete",
                "accuracy_complete",
                "gluing_complete",
                "certified",
                "scope",
                "verify",
                "check",
            )
            if hasattr(cls, name)
        ]
        lines += [
            "",
            (
                "Available status/check interfaces: "
                + ", ".join(f"`{name}`" for name in status)
                + "."
                if status
                else "No status or check methods are defined on this data record; use its owning or registered checker."
            ),
            "",
            f"[Owning implementation](https://github.com/BhuvaneshBhatt/funcprops/blob/main/src/{cls.__module__.replace('.', '/')}.py).",
            "",
        ]
    return normalize_markdown("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = reference_text()
    path = ROOT / "docs/reference/helper-contracts.md"
    if args.check:
        if not path.exists() or path.read_text() != text:
            raise SystemExit(
                "stale helper contracts; run python -m tools.build_helper_docs"
            )
    else:
        path.write_text(text)


if __name__ == "__main__":
    main()
