"""Run a canonical test selection with optional pytest arguments."""

import argparse

import pytest

from tools.test_selections import GROUPS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=GROUPS)
    args, options = parser.parse_known_args()
    if args.group == "warm":
        import sympy as sp

        import funcprops as fp

        x = sp.Symbol("x", real=True)
        fp.monotonic_partition(x * x, x, domain=sp.Interval(-1, 1), return_result=True)
        fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,))
    raise SystemExit(pytest.main(["-q", *GROUPS[args.group], *options]))


if __name__ == "__main__":
    main()
