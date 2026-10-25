"""Deterministic proof-route telemetry; observations never affect correctness."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter


@dataclass(frozen=True)
class RouteObservation:
    """Record the outcome and effort of one attempted proof route."""

    route: str
    estimated_cost: int
    elapsed: float
    outcome: str
    cache_hit: bool = False


@dataclass
class ProofTelemetry:
    """Collect proof-route observations without changing their conclusions."""

    enabled: bool = True
    observations: list[RouteObservation] = field(default_factory=list)

    def record(self, route, estimated_cost, started, outcome, cache_hit=False):
        if self.enabled:
            self.observations.append(
                RouteObservation(
                    route,
                    estimated_cost,
                    max(0.0, perf_counter() - started),
                    outcome,
                    cache_hit,
                )
            )
