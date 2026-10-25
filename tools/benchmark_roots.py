"""Fixed quotient constructions with exact count oracles and advisory timing."""

from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import sympy as sp

import funcprops as fp


def benchmark():
    z = sp.Symbol("z")
    g = sp.exp(z) - 2
    policy = fp.EnclosurePolicy(max_cells=1024, max_depth=16, max_taylor_order=5)
    rows = []
    for numerator, denominator, unit in itertools.product(
        range(1, 4), range(4), (False, True)
    ):
        # A zero-free exponential supplies an actual held quotient when the
        # denominator has order zero. The dedicated quotient API declines bare
        # entire sources; ordinary simplification would erase this test route.
        divisor = sp.sin(g) ** denominator if denominator else sp.exp(z)
        top = sp.exp(z) * g**numerator if unit else g**numerator
        f = sp.Mul(top, sp.Pow(divisor, -1, evaluate=False), evaluate=False)
        start = time.monotonic()
        result = fp.certify_quotient_isolation(f, z, -1 - sp.I, 1 + sp.I, policy=policy)
        # In this rectangle only g=0 can occur among the numerator/denominator
        # zeros. exp(z)=2+k*pi has no other solution here (nonzero k), and exp
        # has no zeros. Every original denominator excludes its common root.
        expected = (
            numerator if not denominator else 0,
            max(denominator - numerator, 0),
            max(numerator - denominator, 0),
        )
        actual = (
            result.total_count,
            result.pole_multiplicity_count,
            result.proof.extension_zero_count,
        )
        valid = result.verify()
        correct = valid and all(
            a is None or a == b for a, b in zip(actual, expected, strict=True)
        )
        if result.complete:
            correct = correct and actual == expected
        rows.append(
            {
                "numerator_order": numerator,
                "denominator_order": denominator,
                "exponential_unit": unit,
                "complete": result.complete,
                "coverage_complete": result.coverage_complete,
                "correct": correct,
                "counts": actual,
                "expected_counts": expected,
                "work": result.tested,
                "seconds": round(time.monotonic() - start, 4),
            }
        )
    return {
        "construction_set": "exp-minus-two-sine-orders",
        "cases": rows,
        "complete": sum(r["complete"] for r in rows),
        "unresolved": sum(not r["complete"] for r in rows),
        "false_counts": sum(not r["correct"] for r in rows),
        "timing": "advisory; no wall-time pass threshold",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("validation/root-benchmarks.json")
    )
    args = parser.parse_args()
    report = benchmark()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}))
    if report["false_counts"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
