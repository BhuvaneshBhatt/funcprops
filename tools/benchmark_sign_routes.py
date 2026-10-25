"""Compare bounded sign and curvature routes with fixed mathematical answers."""

import argparse
import contextlib
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


def cases():
    """Return route, expression, coordinates, domain and exact expected class."""
    x, y = sp.symbols("x y", real=True)
    unit = sp.Interval(0, 1)
    square = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
    curved = x**4 + y**4 + 2 * x * x + 2 * y * y + x * y
    positive = sp.expand((x * x - x + 1) ** 3)
    return (
        ("polynomial", "positive-sixth", "sign", positive, x, unit, "POSITIVE"),
        ("polynomial", "negative-sixth", "sign", -positive, x, unit, "NEGATIVE"),
        (
            "polynomial",
            "positive-eighth",
            "sign",
            sp.expand((2 * x * x - 3 * x + 2) ** 4),
            x,
            unit,
            "POSITIVE",
        ),
        (
            "polynomial",
            "mixed-quartic",
            "sign",
            x**4 - 2 * x**3 + 2 * x * x - x + 1,
            x,
            unit,
            "POSITIVE",
        ),
        (
            "sturm",
            "positive-quotient",
            "sign",
            (x * x + 1) / (x * x + 2),
            x,
            sp.S.Reals,
            "POSITIVE",
        ),
        (
            "sturm",
            "double-zero",
            "sign",
            (x - 1) ** 2 / (x + 2),
            x,
            sp.Interval(0, 2),
            "NONNEGATIVE",
        ),
        (
            "sturm",
            "odd-zero",
            "sign",
            (x - 1) ** 3 / (x + 2),
            x,
            sp.Interval(0, 2),
            "SIGN_CHANGING",
        ),
        (
            "sturm",
            "pole-components",
            "sign",
            1 / (x - 1),
            x,
            sp.Interval(0, 2),
            "SIGN_CHANGING",
        ),
        (
            "sturm",
            "excluded-zero",
            "sign",
            (x - 1) / (x + 2),
            x,
            sp.Interval.open(1, 3),
            "POSITIVE",
        ),
        (
            "threshold",
            "exp-positive",
            "sign",
            sp.exp(x * x) - 2,
            x,
            sp.Interval(1, 2),
            "POSITIVE",
        ),
        (
            "threshold",
            "exp-crossing",
            "sign",
            sp.exp(x * x) - 2,
            x,
            unit,
            "SIGN_CHANGING",
        ),
        (
            "threshold",
            "exp-negative-level",
            "sign",
            sp.exp(x * x) + 2,
            x,
            sp.Interval(-1, 1),
            "POSITIVE",
        ),
        (
            "threshold",
            "exp-owned-zero",
            "sign",
            sp.exp(x * x) - sp.E,
            x,
            sp.Interval(1, 2),
            "NONNEGATIVE",
        ),
        (
            "threshold",
            "log-negative",
            "sign",
            sp.log(x * x + 1) - 1,
            x,
            sp.Interval(-sp.Rational(1, 2), sp.Rational(1, 2)),
            "NEGATIVE",
        ),
        (
            "threshold",
            "log-endpoint-zeros",
            "sign",
            sp.log(x * x + 1) - sp.log(2),
            x,
            sp.Interval(-1, 1),
            "NONPOSITIVE",
        ),
        (
            "jacobian",
            "cosine-determinant",
            "determinant_nonvanishing",
            sp.sin(x),
            x,
            sp.Interval(-1, 1),
            "TRUE",
        ),
        (
            "jacobian",
            "sine-determinant",
            "determinant_nonvanishing",
            -sp.cos(x),
            x,
            sp.Interval.open(0, 1),
            "TRUE",
        ),
        (
            "jacobian",
            "exp-polynomial",
            "determinant_nonvanishing",
            sp.exp(x * x),
            x,
            sp.Interval(1, 2),
            "TRUE",
        ),
        (
            "jacobian",
            "polynomial-map",
            "determinant_nonvanishing",
            x**3 / 3 - 2 * x * x + 5 * x,
            x,
            unit,
            "TRUE",
        ),
        (
            "hessian",
            "polynomial-box",
            "convexity",
            curved,
            (x, y),
            square,
            "STRONGLY_CONVEX",
        ),
        (
            "hessian",
            "negative-box",
            "convexity",
            -curved,
            (x, y),
            square,
            "STRONGLY_CONCAVE",
        ),
        (
            "hessian",
            "exponential-box",
            "convexity",
            sp.exp(x) + sp.exp(y) + x * y / 4,
            (x, y),
            sp.ProductSet(unit, unit),
            "STRONGLY_CONVEX",
        ),
        (
            "hessian",
            "coupled-exponential",
            "convexity",
            sp.exp(x + y) + x * x + y * y,
            (x, y),
            sp.ProductSet(
                sp.Interval(0, sp.Rational(1, 10)), sp.Interval(0, sp.Rational(1, 10))
            ),
            "STRONGLY_CONVEX",
        ),
        ("control", "primitive-exp", "sign", sp.exp(x), x, unit, "POSITIVE"),
        (
            "control",
            "oscillation",
            "sign",
            sp.sin(x),
            x,
            sp.Interval(-1, 1),
            "SIGN_CHANGING",
        ),
        (
            "control",
            "absolute-value",
            "sign",
            sp.Abs(x - 1),
            x,
            sp.Interval(0, 2),
            "NONNEGATIVE",
        ),
        ("control", "radical", "sign", sp.sqrt(x), x, unit, "NONNEGATIVE"),
        (
            "control",
            "constant-jacobian",
            "determinant_nonvanishing",
            3 * x + 1,
            x,
            unit,
            "TRUE",
        ),
        (
            "control",
            "source-hole",
            "determinant_nonvanishing",
            sp.Mul(x, x, sp.Pow(x, -1, evaluate=False), evaluate=False),
            x,
            sp.S.Reals,
            "UNKNOWN",
        ),
        (
            "control",
            "constant-hessian",
            "convexity",
            x * x + y * y + x * y,
            (x, y),
            square,
            "STRONGLY_CONVEX",
        ),
        (
            "control",
            "indefinite-box",
            "convexity",
            x**4 + y**4 + 10 * x * y,
            (x, y),
            square,
            "NEITHER",
        ),
        (
            "hessian",
            "wide-exponential",
            "convexity",
            sp.exp(x + y) + x * x + y * y,
            (x, y),
            square,
            "STRONGLY_CONVEX",
        ),
        (
            "control",
            "loose-entry-bounds",
            "convexity",
            sp.exp(x * y) + 2 * x * x + 2 * y * y,
            (x, y),
            square,
            "STRONGLY_CONVEX",
        ),
        (
            "control",
            "unproved-cosine-chart",
            "determinant_nonvanishing",
            sp.sin(x),
            x,
            sp.Interval(0, 2),
            "FALSE",
        ),
        (
            "control",
            "sine-crossing",
            "determinant_nonvanishing",
            -sp.cos(x),
            x,
            sp.Interval(-1, 1),
            "FALSE",
        ),
    )


def benchmark(rounds=3, warm_rounds=7, groups=()):
    """Record raw cleared/warm samples and separate new answers from speedups."""
    rows = []
    for group, name, operation, expression, variables, domain, expected in cases():
        if groups and group not in groups:
            continue
        samples = {"cleared": [], "warm": []}
        answers = set()
        for state, repetitions in (("cleared", rounds), ("warm", warm_rounds)):
            for _ in range(repetitions):
                if state == "cleared":
                    fp.clear_caches()
                    clear_cache()
                start = perf_counter()
                result = getattr(fp, operation)(expression, variables, domain=domain)
                elapsed = perf_counter() - start
                actual = getattr(getattr(result, "primary", result), "name", None)
                if actual not in (expected, "UNKNOWN"):
                    raise ValueError(f"{name}: {actual} != {expected}")
                samples[state].append(elapsed)
                answers.add(actual)
        if len(answers) != 1:
            raise ValueError(f"unstable answer: {name}: {answers}")
        rows.append(
            {
                "group": group,
                "case": name,
                "operation": operation,
                "expression": str(expression),
                "domain": str(domain),
                "expected": expected,
                "answer": answers.pop(),
                "seconds": samples,
                "median_seconds": {k: statistics.median(v) for k, v in samples.items()},
            }
        )
        print(name, rows[-1]["answer"], flush=True)
    source = Path(fp.__file__).resolve().parent
    names = (
        "real_analysis/sign.py",
        "transformation.py",
        "real_analysis/convexity.py",
        "real_analysis/sign_rules.py",
        "real_analysis/hessian_bounds.py",
    )
    return {
        "source": str(source),
        "source_sha256": {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            if (source / name).exists()
            else None
            for name in names
        },
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "sympy": sp.__version__,
        "cases": rows,
        "timing": "Advisory elapsed time excluding imports/answer checks. Cleared resets funcprops/SymPy caches. UNKNOWN is an honest decline, not a proved answer. Compare time and conclusion coverage separately.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--warm-rounds", type=int, default=7)
    parser.add_argument(
        "--groups",
        nargs="*",
        choices=("polynomial", "sturm", "threshold", "jacobian", "hessian", "control"),
        default=(),
    )
    parser.add_argument(
        "--disable",
        nargs="*",
        choices=("sturm", "threshold", "jacobian", "hessian", "trig"),
        default=(),
    )
    args = parser.parse_args()
    if min(args.rounds, args.warm_rounds) < 1:
        parser.error("sample counts must be positive")
    with contextlib.ExitStack() as stack:
        if args.disable:
            rules = importlib.import_module("funcprops.real_analysis.sign_rules")
            if "sturm" in args.disable:
                stack.enter_context(
                    patch.object(rules, "rational_sign", return_value=fp.Sign.UNKNOWN)
                )
            for name in ("threshold", "trig"):
                if name in args.disable:
                    stack.enter_context(
                        patch.object(
                            rules, name + "_sign", return_value=fp.Sign.UNKNOWN
                        )
                    )
            if "jacobian" in args.disable:
                module = importlib.import_module("funcprops.transformation")
                stack.enter_context(
                    patch.object(
                        module, "_scalar_sign_exclusion", return_value=fp.Sign.UNKNOWN
                    )
                )
            if "hessian" in args.disable:
                module = importlib.import_module(
                    "funcprops.real_analysis.hessian_bounds"
                )
                stack.enter_context(
                    patch.object(
                        module, "hessian_dominance_certificate", return_value=None
                    )
                )
        report = benchmark(args.rounds, args.warm_rounds, args.groups)
    report["disabled"] = list(args.disable)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
