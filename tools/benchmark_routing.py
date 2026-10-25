"""Measure exact range queries against fixed answers, including declined fast paths."""

import argparse
import hashlib
import importlib
import json
import platform
import statistics
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import sympy as sp
from sympy.core.cache import clear_cache

import funcprops as fp
from funcprops.real_analysis.common import condition_to_set


def range_cases():
    """Return fixed input/image pairs with endpoint and fallback controls."""
    x = sp.Symbol("x", real=True)
    q = x**2 + 2 * x + 3
    hole = sp.Mul(q, x + 1, sp.Pow(x + 1, -1, evaluate=False), evaluate=False)
    return x, (
        ("increasing", q, sp.Interval(0, 1), sp.Interval(3, 6), "quadratic"),
        (
            "interior-vertex",
            q,
            sp.Interval.open(-2, 0),
            sp.Interval.Ropen(2, 3),
            "quadratic",
        ),
        ("tied-endpoints", q, sp.Interval.Lopen(-2, 0), sp.Interval(2, 3), "quadratic"),
        (
            "decreasing-side",
            q,
            sp.Interval.open(-3, -2),
            sp.Interval.open(3, 6),
            "quadratic",
        ),
        (
            "negative-leading",
            -2 * x**2 + 3 * x - 7,
            sp.Interval(0, 2),
            sp.Interval(-9, -sp.Rational(47, 8)),
            "quadratic",
        ),
        (
            "whole-line",
            x**2 - 3 * x + 2,
            sp.S.Reals,
            sp.Interval(-sp.Rational(1, 4), sp.oo),
            "quadratic",
        ),
        (
            "open-vertex",
            q,
            sp.Interval.open(-1, 0),
            sp.Interval.open(2, 3),
            "quadratic",
        ),
        (
            "half-line",
            q,
            sp.Interval.open(-1, sp.oo),
            sp.Interval.open(2, sp.oo),
            "quadratic",
        ),
        (
            "disconnected",
            q,
            sp.Union(sp.Interval.open(-1, 0), sp.Interval.Lopen(2, 3)),
            sp.Union(sp.Interval.open(2, 3), sp.Interval.Lopen(11, 18)),
            "quadratic",
        ),
        (
            "isolated-point",
            q,
            sp.Union(sp.Interval.Ropen(-2, -1), sp.FiniteSet(1)),
            sp.Union(sp.Interval.Lopen(2, 3), sp.FiniteSet(6)),
            "quadratic",
        ),
        ("source-hole", hole, sp.Interval(-2, 0), sp.Interval.Lopen(2, 3), "quadratic"),
        (
            "rational-coefficients",
            x**2 / 2 + x / 3 + sp.Rational(5, 6),
            sp.Interval(0, 1),
            sp.Interval(sp.Rational(5, 6), sp.Rational(5, 3)),
            "quadratic",
        ),
        (
            "factored",
            (x - 1) * (x + 2),
            sp.Interval(0, 2),
            sp.Interval(-2, 4),
            "quadratic",
        ),
        ("boolean-increasing", q, (x >= 0) & (x <= 1), sp.Interval(3, 6), "quadratic"),
        (
            "boolean-negative-leading",
            -2 * x**2 + 3 * x - 7,
            (x >= 0) & (x <= 2),
            sp.Interval(-9, -sp.Rational(47, 8)),
            "quadratic",
        ),
        ("affine", 1 - 2 * x, sp.Interval(-1, 1), sp.Interval(-1, 3), "control"),
        (
            "quartic",
            x**4 - x,
            sp.Interval(-1, 1),
            sp.Interval(-3 * 2 ** sp.Rational(1, 3) / 8, 2),
            "control",
        ),
        (
            "rational-pole",
            1 / (x - 1),
            sp.Interval(0, 2),
            sp.Union(sp.Interval(-sp.oo, -1), sp.Interval(1, sp.oo)),
            "control",
        ),
        (
            "cubic",
            x**3 - x,
            sp.Interval(0, 1),
            sp.Interval(-2 * sp.sqrt(3) / 9, 0),
            "control",
        ),
        ("radical", sp.sqrt(x), sp.Interval(0, 4), sp.Interval(0, 2), "control"),
        ("exponential", sp.exp(x), sp.Interval(0, 1), sp.Interval(1, sp.E), "control"),
        (
            "absolute-value",
            sp.Abs(x - 1),
            sp.Interval(0, 2),
            sp.Interval(0, 1),
            "control",
        ),
        (
            "algebraic-coefficient",
            sp.sqrt(2) * x**2 + x,
            sp.Interval(0, 1),
            sp.Interval(0, 1 + sp.sqrt(2)),
            "control",
        ),
        (
            "algebraic-endpoint",
            q,
            sp.Interval(0, sp.sqrt(2)),
            sp.Interval(3, 5 + 2 * sp.sqrt(2)),
            "control",
        ),
        ("quintic", x**5 + x, sp.Interval(0, 1), sp.Interval(0, 2), "control"),
    )


def benchmark(rounds=5, warm_rounds=9):
    """Measure cleared and warm caches; validate every result outside timing."""
    x, cases = range_cases()
    y = sp.Symbol("y", real=True)
    adapter = importlib.import_module("funcprops._semialg")
    ranges = importlib.import_module("funcprops.real_analysis.range")
    rows = []
    for name, expression, domain, expected, group in cases:
        samples = {"cleared": [], "warm": []}
        for state, repetitions in (("cleared", rounds), ("warm", warm_rounds)):
            for _ in range(repetitions):
                if state == "cleared":
                    fp.clear_caches()
                    clear_cache()
                start = perf_counter()
                result = fp.range(expression, x, y, constraints=domain)
                elapsed = perf_counter() - start
                actual = condition_to_set(result, y)
                if actual != expected:
                    raise ValueError(f"{name}: {actual} != {expected}")
                samples[state].append(elapsed)
        # Instrument separately so call counting cannot distort timings.
        with (
            patch.object(adapter, "range", wraps=adapter.range) as delegated,
            patch.object(ranges, "_sympy_range", wraps=ranges._sympy_range) as calculus,
        ):
            result = fp.range(expression, x, y, constraints=domain)
        if condition_to_set(result, y) != expected:
            raise ValueError(f"{name}: instrumentation changed the answer")
        rows.append(
            {
                "case": name,
                "group": group,
                "correct": True,
                "backend_range_calls": delegated.call_count,
                "general_calculus_calls": calculus.call_count,
                "expression": str(expression),
                "domain": str(domain),
                "expected": str(expected),
                "seconds": samples,
                "median_seconds": {k: statistics.median(v) for k, v in samples.items()},
            }
        )
    return {
        "source": str(Path(fp.__file__).resolve()),
        "source_sha256": {
            name: hashlib.sha256(
                (Path(fp.__file__).parent / name).read_bytes()
            ).hexdigest()
            for name in ("real_analysis/range.py", "real_analysis/image_rules.py")
        },
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "sympy": sp.__version__,
        "platform": platform.platform(),
        "cases": rows,
        "timing": "Advisory wall time, excluding interpreter imports and answer checks. Cleared resets funcprops and SymPy caches; warm runs follow in the same process. Backend instrumentation is untimed. No timing pass threshold.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--warm-rounds", type=int, default=9)
    args = parser.parse_args()
    if min(args.rounds, args.warm_rounds) < 1:
        parser.error("sample counts must be positive")
    report = benchmark(args.rounds, args.warm_rounds)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(report["cases"]),
                "all_correct": True,
                "source": report["source"],
            }
        )
    )


if __name__ == "__main__":
    main()
