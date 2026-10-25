"""Restricted images and the difference between held source and extension."""

import sympy as sp

import funcprops as fp

x, y = sp.symbols("x y", real=True)
image = fp.range(sp.exp(x), x, y, constraints=(x > 0) & (x < 1))
assert sp.simplify(image ^ ((y > 1) & (y < sp.E))) is sp.false
held = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
record = fp.track_domain(held, x, sp.Interval(-1, 1))
assert record.verify() and record.complete
assert record.effective == sp.Union(sp.Interval.Ropen(-1, 0), sp.Interval.Lopen(0, 1))
assert sp.simplify(held) == 1
assert record.effective.contains(0) is sp.false
assert fp.sign(x - 1, x, domain=sp.FiniteSet(0, 2)) is fp.Sign.SIGN_CHANGING

# Holding a logarithm preserves its base as well as its source restrictions.
decreasing_log = sp.log(x, sp.Rational(1, 2), evaluate=False)
assert fp.domain(decreasing_log, x) == (x > 0)
assert (
    fp.monotonicity(decreasing_log, x, domain=sp.Interval(2, 4))
    is fp.Monotonicity.STRICTLY_DECREASING
)
enclosure = fp.certified_real_ball(decreasing_log, x, sp.Interval(2, 4))
assert enclosure.verify()
assert enclosure.lower <= -2 < -1 <= enclosure.upper


power_domain = fp.track_domain(x ** sp.sqrt(2), x, sp.Interval(-1, 2))
assert power_domain.verify() and power_domain.natural_complete
assert power_domain.natural == sp.Interval(0, sp.oo)
assert power_domain.effective == sp.Interval(0, 2)
guarded = sp.Piecewise((1, sp.log(x) > 0), (0, True))
guard_domain = fp.track_domain(guarded, x, sp.Interval(-1, 2))
assert guard_domain.verify() and guard_domain.effective == sp.Interval.Lopen(0, 2)
assert (
    fp.continuous(decreasing_log, x, domain=sp.Interval(2, 4))
    is fp.Continuity.CONTINUOUS
)
assert fp.lipschitz(decreasing_log, x, domain=sp.Interval(2, 4)) == 1 / (2 * sp.log(2))
