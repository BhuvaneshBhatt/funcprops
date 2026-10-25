"""Compare bounded proof rules, completed answers and fallback costs."""

import argparse
import hashlib
import json
import platform
import statistics
from pathlib import Path
from time import perf_counter

import sympy as sp
from sympy.core.cache import clear_cache

import funcprops as fp
from tools.benchmark_structure import cases as existing_cases


def cases():
    """Include all prior controls and positive and unsupported proof cases."""
    upgrades = {
        "indefinite-box": "NEITHER",
        "loose-entry-bounds": "STRONGLY_CONVEX",
        "unproved-cosine-chart": "FALSE",
        "unproved": "STRONGLY_CONVEX",
    }
    for group, name, op, expr, var, domain, expected, options in existing_cases():
        if op != "replay":
            yield (
                group,
                name,
                op,
                expr,
                var,
                domain,
                upgrades.get(name, expected),
                options,
            )
    x = sp.Symbol("x", real=True)
    z = sp.Symbol("z")
    y = sp.Symbol("y", real=True)
    punctured = sp.Union(sp.Interval.open(-sp.oo, 0), sp.Interval.open(0, sp.oo))
    step = sp.Piecewise((0, x < 0), (1, True))
    for name, expr, domain, expected in (
        ("continuous-sign-product", sp.sin(x) * sp.sign(x), sp.S.Reals, "CONTINUOUS"),
        ("discontinuous-sign", sp.sign(x), sp.S.Reals, "DISCONTINUOUS"),
        ("continuous-punctured-sign", sp.sign(x), punctured, "CONTINUOUS"),
    ):
        yield "seams", name, "continuous", expr, x, domain, expected, {}
    for name, expr in (("step", step), ("atan-gap", sp.atan(1 / x))):
        for op in ("lipschitz", "uniformly_continuous"):
            yield "gap", name + "-" + op, op, expr, x, punctured, "FALSE", {}
    for name, expr in (
        ("cos-root", sp.cos(sp.sqrt(z))),
        ("sin-root-square", sp.sin(sp.sqrt(z)) ** 2),
    ):
        yield (
            "branches",
            name,
            "meromorphic",
            expr,
            z,
            sp.S.Complexes,
            "MEROMORPHIC",
            {},
        )
    yield (
        "branches",
        "uncanceled-root",
        "meromorphic",
        sp.sin(sp.sqrt(z)),
        z,
        sp.S.Complexes,
        "UNKNOWN",
        {},
    )

    for name, expr, op, coordinate, domain in (
        ("gap-equal-limits", x, "uniformly_continuous", x, punctured),
        (
            "gap-separated-components",
            sp.sign(x),
            "uniformly_continuous",
            x,
            sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2)),
        ),
        (
            "insufficient-exp-margin",
            sp.exp(x * y),
            "convexity",
            (x, y),
            sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1)),
        ),
        (
            "nonentire-inner",
            sp.cos(sp.sqrt(sp.log(z))),
            "meromorphic",
            z,
            sp.S.Complexes,
        ),
    ):
        yield (
            "declines",
            name,
            op,
            expr,
            coordinate,
            domain,
            "TRUE" if name == "gap-separated-components" else "UNKNOWN",
            {},
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--warm-rounds", type=int, default=7)
    args = parser.parse_args()
    rows = []
    for group, name, op, expr, var, domain, expected, options in cases():
        call_options = dict(options)
        if op != "meromorphic":
            call_options["domain"] = domain
        samples = {"cleared": [], "warm": []}
        answers = set()
        for state, rounds in (("cleared", args.rounds), ("warm", args.warm_rounds)):
            for _ in range(rounds):
                if state == "cleared":
                    fp.clear_caches()
                    clear_cache()
                start = perf_counter()
                result = getattr(fp, op)(expr, var, **call_options)
                elapsed = perf_counter() - start
                primary = getattr(result, "primary", result)
                actual = getattr(primary, "name", str(primary))
                if actual not in (expected, "UNKNOWN"):
                    raise ValueError(f"{name}: {actual} != {expected}")
                answers.add(actual)
                samples[state].append(elapsed)
        if len(answers) != 1:
            raise ValueError(f"unstable answers {name}: {answers}")
        rows.append(
            dict(
                group=group,
                case=name,
                operation=op,
                expected=expected,
                answer=answers.pop(),
                seconds=samples,
                median_seconds={k: statistics.median(v) for k, v in samples.items()},
            )
        )
        print(name, rows[-1]["answer"], flush=True)
    report = dict(
        python=platform.python_version(),
        sympy=sp.__version__,
        source=str(Path(fp.__file__).resolve()),
        harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_sha256={
            str(p.relative_to(Path(fp.__file__).parent)): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in sorted(Path(fp.__file__).parent.rglob("*.py"))
        },
        cases=rows,
        timing="Elapsed calls exclude imports and answer checks. Cleared resets funcprops and SymPy caches. UNKNOWN is a decline, not a completed proof. Local sequential samples are advisory.",
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
