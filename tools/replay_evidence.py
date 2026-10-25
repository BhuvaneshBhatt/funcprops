"""Optional pytest plugin recording observed replay outcomes by concrete type.

Set FUNCPROPS_REPLAY_EVIDENCE and load -p tools.replay_evidence. Lightweight
wrappers preserve the original checkers and avoid profiling symbolic arithmetic.
Observations record execution, not complete semantic coverage.
"""

from __future__ import annotations

import json
import os
from functools import wraps
from pathlib import Path

import pytest

_registered = set()
_observed = {}
_current = "collection"
_patches = None


def _observe(record, result):
    cls = type(record)
    if cls not in _registered:
        return
    accepted = result if type(result) is bool else getattr(result, "certified", None)
    if type(accepted) is not bool:
        return
    name = cls.__module__ + "." + cls.__name__
    row = _observed.setdefault(name, {"accepted": set(), "rejected": set()})
    row["accepted" if accepted else "rejected"].add(_current)


def _wrap(function):
    @wraps(function)
    def checked(*args, **kwargs):
        result = function(*args, **kwargs)
        for record in (*args, *kwargs.values()):
            if type(record) in _registered:
                _observe(record, result)
                break
        return result

    return checked


def pytest_configure(config):
    global _registered, _patches
    import funcprops as fp
    import funcprops.verification as verification

    expected = os.environ.get("FUNCPROPS_EXPECTED_PACKAGE_ROOT")
    if expected and not Path(fp.__file__).resolve().is_relative_to(
        Path(expected).resolve()
    ):
        raise RuntimeError(
            f"wrong package imported: {fp.__file__}, expected {expected}"
        )
    factory = verification._certificate_verifiers
    entries = factory()
    _registered = {cls for cls, _ in entries}
    _patches = pytest.MonkeyPatch()
    for cls, _ in entries:
        for name in ("verify", "check"):
            method = getattr(cls, name, None)
            if callable(method):
                _patches.setattr(cls, name, _wrap(method))
    cached = [entries, tuple((cls, _wrap(verifier)) for cls, verifier in entries)]

    @wraps(factory)
    def observed_registry():
        fresh = factory()
        if fresh is not cached[0]:
            cached[:] = [
                fresh,
                tuple((cls, _wrap(verifier)) for cls, verifier in fresh),
            ]
        return cached[1]

    for name in ("cache_info", "cache_clear", "cache_parameters"):
        setattr(observed_registry, name, getattr(factory, name))
    _patches.setattr(verification, "_certificate_verifiers", observed_registry)
    for module in (fp, verification):
        for name, value in list(vars(module).items()):
            if name.startswith("verify_") and callable(value):
                _patches.setattr(module, name, _wrap(value))


def pytest_runtest_setup(item):
    global _current
    _current = item.nodeid


def pytest_unconfigure(config):
    if _patches is not None:
        _patches.undo()
    path = os.environ.get("FUNCPROPS_REPLAY_EVIDENCE")
    if path:
        report = {
            cls.__module__ + "." + cls.__name__: {
                key: sorted(
                    _observed.get(cls.__module__ + "." + cls.__name__, {}).get(
                        key, set()
                    )
                )
                for key in ("accepted", "rejected")
            }
            for cls in sorted(_registered, key=lambda c: (c.__module__, c.__name__))
        }
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n")
