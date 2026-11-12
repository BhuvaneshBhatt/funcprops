"""Exact images of two algebraically incommensurate trigonometric phases."""

from dataclasses import dataclass

import sympy as sp

from ..source_syntax import normalize_arithmetic, same_data


def dense_trig_data(expression, variable, domain):
    """Use phase density for closure and integer phase compatibility for ownership.

    For two affine phases with algebraic irrational frequency ratio, the real
    orbit is dense in the phase torus, including on each half-line. With rational
    multiples of pi as offsets, simultaneous extremal phases can occur only at
    x=0: any other solution would express the ratio as a rational number.
    """
    parts = domain.args if isinstance(domain, sp.Union) else (domain,)
    if (
        not any(
            isinstance(p, sp.Interval) and (p.start is -sp.oo or p.end is sp.oo)
            for p in parts
        )
        and domain is not sp.S.Reals
    ):
        return None
    if expression.free_symbols - {variable} or expression.has(sp.Float):
        return None
    from ..domain_tracking import track_domain

    source = track_domain(expression, variable, domain)
    if not source.complete or source.effective != domain:
        return None
    f = normalize_arithmetic(expression)
    offset = sp.S.Zero
    terms = []
    for term in sp.Add.make_args(sp.expand(f)):
        if not term.has(variable):
            if term.is_real is not True or term.is_finite is not True:
                return None
            offset += term
            continue
        heads = [a for a in term.atoms(sp.sin, sp.cos) if a.has(variable)]
        if len(heads) != 1:
            return None
        head = heads[0]
        power = term.as_powers_dict().get(head)
        if power not in (1, 2):
            return None
        coefficient = sp.cancel(term / head**power)
        if coefficient.is_Rational is not True or coefficient == 0:
            return None
        try:
            phase = sp.Poly(head.args[0], variable)
        except sp.PolynomialError:
            return None
        slope = phase.nth(1)
        shift = sp.cancel(phase.nth(0) / sp.pi)
        if (
            phase.degree() != 1
            or slope.is_real is not True
            or slope.is_algebraic is not True
            or slope.is_zero is not False
            or shift.is_Rational is not True
        ):
            return None
        terms.append((head.func, slope, shift, int(power), coefficient))
    if len(terms) != 2:
        return None
    ratio = sp.cancel(terms[0][1] / terms[1][1])
    if ratio.is_Rational is True:
        return None
    t = sp.Symbol("frequency_ratio")
    minimal = sp.minpoly(ratio, t)
    if sp.Poly(minimal, t).degree() <= 1:
        return None
    low = high = offset
    lower_at_zero = upper_at_zero = True
    for head, _, shift, power, coefficient in terms:
        lower, upper = (-1, 1) if power == 1 else (0, 1)
        low += coefficient * (lower if coefficient > 0 else upper)
        high += coefficient * (upper if coefficient > 0 else lower)
        period = 2 if power == 1 else 1
        maximum = sp.Rational(1, 2) if head is sp.sin else sp.S.Zero
        minimum = (
            (sp.Rational(3, 2) if head is sp.sin else sp.S.One)
            if power == 1
            else (sp.S.Zero if head is sp.sin else sp.Rational(1, 2))
        )
        lower_phase = minimum if coefficient > 0 else maximum
        upper_phase = maximum if coefficient > 0 else minimum
        lower_at_zero &= sp.Mod(shift - lower_phase, period) == 0
        upper_at_zero &= sp.Mod(shift - upper_phase, period) == 0
    owned = domain.contains(0)
    if owned not in (sp.true, sp.false):
        return None
    image = sp.Interval(
        low,
        high,
        not (lower_at_zero and owned is sp.true),
        not (upper_at_zero and owned is sp.true),
    )
    return tuple(terms), offset, minimal, image


@dataclass(frozen=True)
class DenseTrigImage:
    """Phase density and exact endpoint compatibility for two trig frequencies."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    terms: tuple
    offset: sp.Expr
    frequency_polynomial: sp.Expr
    image: sp.Interval

    def verify(self):
        """Replay the exact algebraic frequency and rational phase premises."""
        try:
            data = dense_trig_data(self.expression, self.variable, self.domain)
            return (
                type(self) is DenseTrigImage
                and data is not None
                and same_data(
                    data,
                    (self.terms, self.offset, self.frequency_polynomial, self.image),
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
