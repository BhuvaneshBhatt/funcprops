"""One immutable effort policy for an entire enclosure/coverage query."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class EnclosurePolicy:
    """Bound precision refinement, subdivision, series work and elapsed time."""

    precision: int = 30
    max_precision: int = 240
    max_refinements: int = 3
    max_depth: int = 10
    max_cells: int = 1024
    max_taylor_order: int = 2
    max_series_terms: int = 4096
    seconds: float | None = None

    def __post_init__(self):
        for name in (
            "precision",
            "max_precision",
            "max_refinements",
            "max_depth",
            "max_cells",
            "max_taylor_order",
            "max_series_terms",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.precision < 2 or self.max_precision < self.precision:
            raise ValueError("require 2 <= precision <= max_precision")
        if self.seconds is not None and (
            isinstance(self.seconds, bool)
            or not math.isfinite(self.seconds)
            or self.seconds <= 0
        ):
            raise ValueError("seconds must be finite and positive")

    @property
    def precisions(self):
        values = [self.precision]
        for _ in range(self.max_refinements):
            if values[-1] >= self.max_precision:
                break
            values.append(min(2 * values[-1], self.max_precision))
        return tuple(values)
