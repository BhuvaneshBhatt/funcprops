"""Measure Hessian and scalar-domain reuse against unchanged proof payloads."""

import argparse
import hashlib
import json
import platform
import statistics
from functools import partial
from pathlib import Path
from time import perf_counter

import sympy as sp
from sympy.core.cache import clear_cache

import funcprops as fp
from tools.benchmark_sign_routes import cases as sign_cases


def cases():
    """Include completed proofs, unsupported controls and certificate replay."""
    for group, name, operation, expression, variables, domain, expected in sign_cases():
        yield group, name, operation, expression, variables, domain, expected, {}
    x, y, z, w = sp.symbols("x y z w", real=True)
    unit = sp.Interval(-sp.Rational(1, 8), sp.Rational(1, 8))
    for variables in ((x, y), (x, y, z), (x, y, z, w)):
        expression = sp.exp(sum(variables)) + 5 * sum(v**2 for v in variables)
        domain = sp.ProductSet(*(unit for _ in variables))
        for operation in ("convexity", "replay"):
            yield (
                "box-reuse",
                f"{operation}-{len(variables)}d",
                operation,
                expression,
                variables,
                domain,
                "STRONGLY_CONVEX" if operation == "convexity" else "True",
                {"return_result": True} if operation == "convexity" else {},
            )
    square = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
    for name, expression, expected in (
        ("affine", x + y, "AFFINE"),
        ("constant", x * x + x * y + y * y, "STRONGLY_CONVEX"),
        ("separable", sp.exp(x) + y**4, "CONVEX"),
        ("indefinite", x * x - y * y, "NEITHER"),
        ("unproved", sp.exp(x * y) + 2 * x * x + 2 * y * y, "STRONGLY_CONVEX"),
    ):
        yield (
            "hessian-controls",
            name,
            "convexity",
            expression,
            (x, y),
            square,
            expected,
            {"return_result": True},
        )
    for name, expression, domain in (
        ("factored-exponential", sp.exp(x * x), sp.Interval(1, 2)),
        ("factored-exponential-wide", sp.exp(x * x - x), sp.Interval(1, 2)),
        ("factored-exponential-product", sp.exp(x * x + x), sp.Interval(0, 1)),
    ):
        yield (
            "factor-domain",
            name,
            "determinant_nonvanishing",
            expression,
            x,
            domain,
            "TRUE",
            {"return_result": True},
        )


def benchmark(rounds, warm_rounds):
    """Time calls with answer checking and certificate construction excluded."""
    rows = []
    for (
        group,
        name,
        operation,
        expression,
        variables,
        domain,
        expected,
        options,
    ) in cases():
        if operation == "replay":
            result = fp.convexity(
                expression, variables, domain=domain, return_result=True
            )
            proof = result.evidence[0]

            call = partial(fp.verify_certificate, proof, expr=expression, var=variables)
        else:
            call = partial(
                getattr(fp, operation), expression, variables, domain=domain, **options
            )

        samples = {"cleared": [], "warm": []}
        payloads = set()
        for state, repetitions in (("cleared", rounds), ("warm", warm_rounds)):
            for _ in range(repetitions):
                if state == "cleared":
                    fp.clear_caches()
                    clear_cache()
                start = perf_counter()
                value = call()
                elapsed = perf_counter() - start
                primary = getattr(value, "primary", value)
                actual = getattr(primary, "name", str(primary))
                if actual != expected:
                    raise ValueError(f"{name}: {actual} != {expected}")
                samples[state].append(elapsed)
                payloads.add(repr(value))
        if len(payloads) != 1:
            raise ValueError(f"unstable proof payload: {name}")
        payload = payloads.pop()
        rows.append(
            {
                "group": group,
                "case": name,
                "operation": operation,
                "expression": str(expression),
                "domain": str(domain),
                "answer": expected,
                "payload": payload,
                "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
                "seconds": samples,
                "median_seconds": {k: statistics.median(v) for k, v in samples.items()},
            }
        )
        print(name, expected, flush=True)
    source = Path(fp.__file__).resolve().parent
    return {
        "source": str(source),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in (
                "real_analysis/convexity.py",
                "real_analysis/hessian_bounds.py",
                "transformation.py",
            )
        },
        "python": platform.python_version(),
        "sympy": sp.__version__,
        "cases": rows,
        "timing": "Elapsed calls; imports, answer checking and replay proposal excluded. Cleared resets funcprops/SymPy caches. Sequential local samples, without confidence intervals.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--warm-rounds", type=int, default=15)
    args = parser.parse_args()
    if min(args.rounds, args.warm_rounds) < 1:
        parser.error("sample counts must be positive")
    result = benchmark(args.rounds, args.warm_rounds)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
