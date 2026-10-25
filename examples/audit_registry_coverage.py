"""Inventory declarations, not a claim of executable or certified coverage."""

import json
from collections import Counter, defaultdict

from funcprops import registry


def registry_inventory():
    reg = registry()
    columns = Counter()
    categories = defaultdict(list)
    families = []
    placeholders = {"", "unknown", "symbol('unknown')", "none"}
    for family in reg:
        properties = family.raw.get("properties", {})
        meaningful = []
        for name, prop in properties.items():
            if any(
                str(c.get("value_source", "")).strip().lower() not in placeholders
                for c in prop.get("cases", [])
            ):
                meaningful.append(name)
                columns[name] += 1
        row = {
            "family": family.id,
            "category": family.raw.get("category"),
            "declared_columns": sorted(properties),
            "nonplaceholder_columns": sorted(meaningful),
        }
        families.append(row)
        categories[row["category"]].append(row)
    native = reg.property_rules()
    native_heads = defaultdict(set)
    for rule in native:
        native_heads[rule.property].add(str(rule.head))
    targets = [
        "RealDomain",
        "ComplexDomain",
        "Range",
        "GlobalMonotonicity",
        "GlobalConvexity",
        "Injective",
        "Positive",
        "NonNegative",
        "Poles",
        "BranchCuts",
        "Entire",
        "Meromorphic",
    ]
    return {
        "note": "Declarations and nonplaceholder source cases only; not tested mathematical coverage. Algorithms outside the registry may support missing columns.",
        "families": len(families),
        "nonplaceholder_property_counts": dict(sorted(columns.items())),
        "native_property_rules": len(native),
        "native_property_heads": {
            k: sorted(v) for k, v in sorted(native_heads.items())
        },
        "missing_catalogue_columns": {
            p: [r["family"] for r in families if p not in r["nonplaceholder_columns"]]
            for p in targets
        },
        "category_counts": {
            k: {
                "families": len(rows),
                "columns": {
                    p: sum(p in r["nonplaceholder_columns"] for r in rows)
                    for p in targets
                },
            }
            for k, rows in sorted(categories.items())
        },
        "absent_catalogue_property_classes": [
            p
            for p in [
                "Zeros",
                "RootCount",
                "Multiplicity",
                "Interlacing",
                "Periodicity",
                "Symmetry",
                "Homogeneity",
                "Lipschitz",
                "Holder",
                "UniformContinuity",
                "Variation",
                "Integrability",
                "LogConvexity",
                "CompleteMonotonicity",
                "AsymptoticBounds",
            ]
            if p not in columns
        ],
        "family_details": families,
    }


if __name__ == "__main__":
    print(json.dumps(registry_inventory(), indent=2))
