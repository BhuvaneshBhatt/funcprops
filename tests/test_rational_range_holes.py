"""Consumer ranges retain missing values and remain independent of symbopt."""

import subprocess
import sys

import pytest
import sympy as sp

import funcprops as fp

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    "f,domain,expected",
    [
        (1 / x, sp.S.Reals, sp.S.Reals - sp.FiniteSet(0)),
        (2 + 3 / (x - 1), sp.S.Reals, sp.S.Reals - sp.FiniteSet(2)),
        ((x + 1) / (x - 1), sp.S.Reals, sp.S.Reals - sp.FiniteSet(1)),
        (
            1 / x,
            sp.Interval(-1, 1),
            sp.Union(sp.Interval(-sp.oo, -1), sp.Interval(1, sp.oo)),
        ),
        (1 / x, sp.Interval.open(0, 1), sp.Interval.open(1, sp.oo)),
        (
            sp.exp(1 / x),
            sp.S.Reals,
            sp.Union(sp.Interval.open(0, 1), sp.Interval.open(1, sp.oo)),
        ),
        (
            sp.atan(1 / x),
            sp.S.Reals,
            sp.Union(sp.Interval.open(-sp.pi / 2, 0), sp.Interval.open(0, sp.pi / 2)),
        ),
        (
            (sp.exp(x) + 1) / (sp.exp(x) - 1),
            sp.S.Reals,
            sp.Union(sp.Interval.open(-sp.oo, -1), sp.Interval.open(1, sp.oo)),
        ),
    ],
)
def test_range_holes(f, domain, expected):
    result = fp.range(f, x, y, domain=domain)
    assert fp.condition_to_real_set(result, y) == expected


def test_without_symbopt():
    source = """import importlib.abc
import sys
class BlockOptimizer(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] == "symbopt":
            raise ModuleNotFoundError(fullname, name=fullname)
sys.meta_path.insert(0, BlockOptimizer())
import funcprops as fp
import sympy as sp
x,y=sp.symbols("x y",real=True)
assert fp.condition_to_real_set(fp.range(1/x,x,y),y) == sp.S.Reals-sp.FiniteSet(0)
assert not any(name.split(".")[0]=="symbopt" for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", source], capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
