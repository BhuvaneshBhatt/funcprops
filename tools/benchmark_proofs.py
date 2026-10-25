"""Report proposal, replay and source-preserving transport costs without timing gates."""

import argparse
import json
import pickle
from pathlib import Path
from time import perf_counter

import sympy as sp

import funcprops as fp
from funcprops._source_transport import _dumps


def benchmark():
    """Measure fixed known-answer families with separate checking and transport work."""
    x, a, b = sp.symbols("x a b", real=True)
    z, w = sp.symbols("z w")
    spike = sp.Piecewise((10, sp.Eq(x, 0)), (x * x, True))

    def charts():
        boxes = (fp.CoverageRectangle(0, 1 + sp.I), fp.CoverageRectangle(1, 2 + sp.I))
        return fp.glue_branch_charts(
            tuple(fp.certify_branch_chart(w - z, z, w, D, z) for D in boxes)
        )

    cases = (
        (
            "finite-metric",
            lambda: fp.certify_finite_lipschitz(x * x, x, sp.FiniteSet(0, 1, 2)),
            lambda p: p.constant == 3,
        ),
        (
            "jump-variation",
            lambda: fp.certify_jump_variation(spike, x, sp.Interval(-1, 1)),
            lambda p: p.total_variation == 22,
        ),
        (
            "coefficient-field",
            lambda: fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,)),
            lambda p: sp.degree(p.polynomial, p.generator) == 2,
        ),
        (
            "parameter-geometry",
            lambda: fp.certify_parameter_geometry(
                x * x + a * x + b, x, (a, b), max_cells=100
            ),
            lambda p: p.specialize({a: 0, b: -1}) == 2,
        ),
        (
            "partial-geometry",
            lambda: fp.certify_parameter_geometry(
                x * x + a * x + b, x, (a, b), max_cells=0
            ),
            lambda p: p.complete is False and p.specialize({a: 0, b: -1}) is None,
        ),
        ("branch-gluing", charts, lambda p: p.coverage_complete and p.gluing_complete),
    )
    rows = []
    for name, propose, correct in cases:
        fp.clear_caches()
        for state in ("cold", "warm"):
            start = perf_counter()
            proof = propose()
            proposal = perf_counter() - start
            start = perf_counter()
            valid = proof.verify()
            replay = perf_counter() - start
            start = perf_counter()
            data = _dumps(proof)
            restored = pickle.loads(data)
            transport = perf_counter() - start
            valid = (
                valid
                and restored.verify()
                and bool(correct(proof))
                and bool(correct(restored))
            )
            rows.append(
                dict(
                    case=name,
                    state=state,
                    complete=proof.complete,
                    correct=bool(valid),
                    work=getattr(proof, "tested", None),
                    proposal_seconds=round(proposal, 6),
                    replay_seconds=round(replay, 6),
                    transport_seconds=round(transport, 6),
                    transport_bytes=len(data),
                )
            )
    return dict(
        cases=rows,
        false_claims=sum(not row["correct"] for row in rows),
        complete=sum(row["complete"] for row in rows),
        partial=sum(not row["complete"] for row in rows),
        timing="Advisory. Proposal includes internal checks; transport excludes worker startup. No wall-time pass threshold.",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", type=Path, default=Path("validation/proof-performance.json")
    )
    args = parser.parse_args()
    result = benchmark()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))
    if result["false_claims"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
