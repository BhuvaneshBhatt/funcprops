"""Deterministic expression-sensitive proof routing and bounded complexity budgets."""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp


@dataclass
class ProofBudget:
    """Limit symbolic proof routes by effort and expression size."""

    max_cost: int = 100
    spent: int = 0
    attempted: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def allow(self, route, cost):
        """Decide whether the remaining proof budget admits the proposed work."""

        if cost < 0:
            raise ValueError("cost must be nonnegative")
        if self.spent + cost > self.max_cost:
            self.skipped.append(route)
            return False
        self.spent += cost
        self.attempted.append(route)
        return True


def expression_cost(expr):
    """Estimate proof-route work as one plus the symbolic operation count."""
    return int(sp.count_ops(sp.sympify(expr), visual=False)) + 1


def route_proofs(expr, routes, *, budget=None):
    """Try eligible proof routes within the requested symbolic effort budget."""

    budget = budget or ProofBudget()
    accepted = []
    base = expression_cost(expr)
    for name, multiplier in routes:
        if budget.allow(name, max(1, int(base * multiplier))):
            accepted.append(name)
    return tuple(accepted), budget
