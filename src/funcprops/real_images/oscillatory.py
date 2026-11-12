"""Image theorems for exact oscillatory escape along phase sequences."""

from dataclasses import dataclass

import sympy as sp

from ..source_syntax import normalize_arithmetic, same_data


def escape_data(expression, variable, domain):
    """Derive two opposite unbounded values on an unbounded continuous interval.

    A nonconstant rational polynomial amplitude has a fixed eventual sign on
    either half-line. The two phase sequences set the oscillator to +1 and -1,
    so their function values escape in opposite directions.
    """
    from ..domain_tracking import track_domain

    if domain is sp.S.Reals:
        domain = sp.Interval(-sp.oo, sp.oo)
    if not isinstance(domain, sp.Interval) or not (
        domain.start is -sp.oo or domain.end is sp.oo
    ):
        return None
    if expression.free_symbols - {variable} or expression.has(sp.Float):
        return None
    f = normalize_arithmetic(expression)
    heads = [h for h in f.atoms(sp.sin, sp.cos) if h.has(variable)]
    if len(heads) != 1:
        return None
    head = heads[0]
    parts = sp.collect(sp.expand(f), head, evaluate=False)
    amplitude, offset = parts.get(head), parts.get(1, sp.S.Zero)
    if amplitude is None or set(parts) - {head, 1} or offset.has(variable):
        return None
    try:
        polynomial = sp.Poly(amplitude, variable, domain=sp.QQ)
        phase = sp.Poly(head.args[0], variable)
    except (sp.PolynomialError, sp.polys.polyerrors.CoercionFailed):
        return None
    if not 1 <= polynomial.degree() <= 16 or phase.degree() != 1:
        return None
    slope, shift = phase.nth(1), phase.nth(0)
    if (
        slope.is_real is not True
        or slope.is_zero is not False
        or (slope.is_positive is not True and slope.is_negative is not True)
        or shift.is_real is not True
        or offset.is_finite is not True
        or offset.is_real is not True
    ):
        return None
    source = track_domain(expression, variable, domain)
    if not source.complete or source.effective != domain:
        return None
    if sp.calculus.util.continuous_domain(f, variable, domain) != domain:
        return None
    direction = 1 if domain.end is sp.oo else -1
    turn = direction if slope.is_positive else -direction
    n = sp.Symbol("phase_index", integer=True, positive=True)
    angles = (sp.pi / 2, 3 * sp.pi / 2) if head.func is sp.sin else (0, sp.pi)
    sequences = tuple(
        sp.Lambda(n, (angle - shift + 2 * sp.pi * turn * n) / slope) for angle in angles
    )
    return amplitude, offset, head, direction, sequences


@dataclass(frozen=True)
class OscillatoryEscape:
    """A continuous image is all reals by two exact oscillatory phase sequences."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    amplitude: sp.Expr
    offset: sp.Expr
    oscillator: sp.Expr
    direction: int
    sequences: tuple

    def verify(self):
        """Replay polynomial growth, phase identities, source and continuity."""
        try:
            data = escape_data(self.expression, self.variable, self.domain)
            return (
                type(self) is OscillatoryEscape
                and data is not None
                and same_data(
                    data,
                    (
                        self.amplitude,
                        self.offset,
                        self.oscillator,
                        self.direction,
                        self.sequences,
                    ),
                )
            )
        except (
            TypeError,
            ValueError,
            AttributeError,
            ArithmeticError,
            NotImplementedError,
        ):
            return False
