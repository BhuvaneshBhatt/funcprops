"""Performance reporting checks correctness and preserves partial outcomes."""

from tools.benchmark_proofs import benchmark


def test_report_phases():
    result = benchmark()
    assert (
        result["false_claims"] == 0
        and result["complete"] == 10
        and result["partial"] == 2
    )
    assert {(row["case"], row["state"]) for row in result["cases"]} == {
        (case, state)
        for case in (
            "finite-metric",
            "jump-variation",
            "coefficient-field",
            "parameter-geometry",
            "partial-geometry",
            "branch-gluing",
        )
        for state in ("cold", "warm")
    }
    for row in result["cases"]:
        assert row["transport_bytes"] > 0
        assert all(
            row[key] >= 0
            for key in ("proposal_seconds", "replay_seconds", "transport_seconds")
        )
