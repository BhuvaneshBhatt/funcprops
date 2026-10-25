"""Check derivative availability after an ordinary warm-state test workload.

Run from the project root with PYTHONPATH=src and PYTHONHASHSEED=3.
On the affected baseline the failure is intermittent. A failure reports the
exact held source and any InconsistentAssumptions exception seen during replay.
Exits unsuccessfully when proof availability is lost.
"""

import json
import sys
from pathlib import Path

import pytest
import sympy as sp

import funcprops.derivative_inequalities as module

x = sp.Symbol("x", real=True)
domain = sp.Interval(0, 1)
exceptions = []
bases = []
original = module.certify_inequality


def traced_inequality(*args, **kwargs):
    result = original(*args, **kwargs)
    if args[0] == 1 and args[2] == x:
        bases.append(result)
    return result


def trace(frame, event, arg):
    if "/funcprops/" not in frame.f_code.co_filename:
        return None
    if event == "exception" and arg[0].__name__ == "InconsistentAssumptions":
        exceptions.append(
            {
                "file": Path(frame.f_code.co_filename).name,
                "function": frame.f_code.co_name,
                "line": frame.f_lineno,
                "exception": repr(arg[1]),
            }
        )
    return trace


class AvailabilityProbe:
    probes = 0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        yield
        exceptions.clear()
        bases.clear()
        sys.settrace(trace)
        try:
            result = module.derivative_chain_positive(x, x, domain)
        finally:
            sys.settrace(None)
        self.probes += 1
        if result is None:
            print(
                json.dumps(
                    {
                        "after": item.nodeid,
                        "probes": self.probes,
                        "bases": [repr(b) for b in bases],
                        "exceptions": exceptions,
                    },
                    indent=2,
                ),
                flush=True,
            )
            raise AssertionError("derivative proof availability failure reproduced")


if __name__ == "__main__":
    module.certify_inequality = traced_inequality
    files = [
        str(p)
        for p in sorted(Path("tests").glob("test_*.py"))
        if any(
            word in p.name
            for word in ("compositional", "consistent", "practical", "proof", "guard")
        )
    ]
    probe = AvailabilityProbe()
    code = pytest.main(["-x", "-q", *files], plugins=[probe])
    print(json.dumps({"availability_probes": probe.probes, "exit_code": int(code)}))
    sys.exit(code)
