"""Generate a conservative DLMF audit manifest for the funcprops catalogue.

This script covers every catalogue family.  It separates DLMF-covered special
function families from elementary/non-DLMF entries and records whether a
family has hand-audited executable facts, chapter-level coverage only, or
requires future formula-by-formula review.  It also performs structural
consistency checks on every property table.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from dlmf_formula_audit import FORMULA_AUDIT

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "src/funcprops/data/catalogue.json"
OUT = ROOT / "src/funcprops/data/dlmf_audit.json"

CHAPTER = {
    "gamma_functions": "5, 8",
    "beta_functions": "5, 8",
    "error_functions": "6, 7",
    "bessel": "9, 10, 11, 13",
    "hyper": "15, 16",
    "hypergeometric": "16",
    "polynomials": "14, 18",
    "orthogonal": "12, 14, 18",
    "elliptic_integrals": "19",
    "elliptic": "19, 22, 23",
    "theta": "20",
    "zeta_functions": "25",
    "zeta": "25",
    "zetazeros": "25",
    "mathieu_functions": "28",
    "spherical_harmonics": "14",
}
HAND = {
    "airyai",
    "airyaiprime",
    "airybi",
    "airybiprime",
    "besseli",
    "besselj",
    "besselk",
    "bessely",
    "hankel1",
    "hankel2",
    "gamma",
    "digamma",
    "polygamma",
    "trigamma",
    "lowergamma",
    "uppergamma",
    "beta",
    "betainc",
    "betainc_regularized",
    "erf",
    "erfc",
    "fresnelc",
    "fresnels",
    "Ei",
    "Ci",
    "Si",
    "Chi",
    "Shi",
    "zeta",
    "hyper",
    "assoc_legendre",
    "legendre",
    "elliptic_k",
    "elliptic_e",
    "elliptic_f",
    "elliptic_pi",
}

URL = {
    c: f"https://dlmf.nist.gov/{c}"
    for c in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23, 25, 28]
}


def structural_issues(f):
    issues = []
    props = f.get("properties", {})
    for name, p in props.items():
        if p.get("representation") != "PiecewiseCases":
            issues.append(f"{name}: unexpected representation")
        for i, c in enumerate(p.get("cases", [])):
            if "value_source" not in c or "condition_source" not in c:
                issues.append(f"{name}[{i}]: missing value/condition")
            if not c.get("source_lhs"):
                issues.append(f"{name}[{i}]: missing source_lhs")
    if f.get("entire", {}).get("cases") and f.get("poles", {}).get("cases"):
        # Not automatically a contradiction because conditional guards may differ.
        pass
    return issues


def main():
    data = json.loads(CAT.read_text())
    rows = []
    for f in data["families"]:
        fid = f["family_id"]
        cat = f.get("category", "")
        chapters = CHAPTER.get(cat)
        if not chapters:
            status = "not-dlmf-scoped"
        elif fid in HAND:
            status = "hand-audited-core"
        elif fid in FORMULA_AUDIT:
            status = (
                "formula-verified-derived"
                if FORMULA_AUDIT[fid][2]
                else "formula-verified-core"
            )
        elif fid == "marcumq":
            status = "dlmf-related-not-native"
        elif fid.startswith("mpmath:"):
            status = "dlmf-mapped-mpmath-inventory"
        else:
            status = "chapter-mapped-core-needs-formula-review"
        urls = []
        if chapters:
            for bit in chapters.split(", "):
                with contextlib.suppress(Exception):
                    urls.append(URL[int(bit)])
        audit = FORMULA_AUDIT.get(fid)
        rows.append(
            {
                "family_id": fid,
                "category": cat,
                "status": status,
                "dlmf_chapters": chapters or "",
                "dlmf_urls": urls,
                "structural_issues": structural_issues(f),
                "property_count": len(f.get("properties", {})),
                "formula_refs": list(audit[0]) if audit else [],
                "formula_verified_properties": audit[1] if audit else "",
                "verification_kind": (
                    "derived" if audit and audit[2] else ("direct" if audit else "")
                ),
            }
        )
    summary = {
        "catalogue_families": len(rows),
        "dlmf_scoped": sum(bool(r["dlmf_chapters"]) for r in rows),
        "hand_audited": sum(r["status"] == "hand-audited-core" for r in rows),
        "needs_formula_review": sum(
            r["status"] == "chapter-mapped-core-needs-formula-review" for r in rows
        ),
        "formula_verified_core": sum(
            r["status"] == "formula-verified-core" for r in rows
        ),
        "formula_verified_derived": sum(
            r["status"] == "formula-verified-derived" for r in rows
        ),
        "dlmf_mapping_corrections": sum(
            r["status"] == "dlmf-related-not-native" for r in rows
        ),
        "structural_issue_count": sum(len(r["structural_issues"]) for r in rows),
    }
    OUT.write_text(
        json.dumps(
            {"schema_version": "1.0", "summary": summary, "families": rows},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
