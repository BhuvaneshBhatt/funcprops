from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from funcprops._checkpoints import capture_checkpoints, checkpoint_sink, emit_checkpoint


def test_nested_sinks():
    outer, inner = [], []
    assert checkpoint_sink() is None
    with capture_checkpoints(outer.append):
        emit_checkpoint(1)
        with capture_checkpoints(inner.append):
            emit_checkpoint(2)
        emit_checkpoint(3)
    emit_checkpoint(4)
    assert outer == [1, 3] and inner == [2]
    assert checkpoint_sink() is None


def test_exception_restores_sink():
    saved = []
    with capture_checkpoints(saved.append):
        with pytest.raises(InterruptedError), capture_checkpoints(None):
            emit_checkpoint("unobserved")
            raise InterruptedError
        emit_checkpoint("restored")
    assert saved == ["restored"]
    assert checkpoint_sink() is None


def test_concurrent_sinks():
    barrier = Barrier(2)

    def run(label):
        saved = []
        with capture_checkpoints(saved.append):
            barrier.wait(timeout=10)
            for index in range(10):
                emit_checkpoint((label, index))
        return saved

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run, "first")
        second = pool.submit(run, "second")
        assert first.result(timeout=15) == [("first", i) for i in range(10)]
        assert second.result(timeout=15) == [("second", i) for i in range(10)]
    assert checkpoint_sink() is None
