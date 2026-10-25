"""Scoped checkpoint delivery for resumable searches and wall-budget workers."""

from contextlib import contextmanager
from contextvars import ContextVar

_sink = ContextVar("funcprops_checkpoint_sink", default=None)


def checkpoint_sink():
    """Return the callback active in this execution context, if any."""
    return _sink.get()


@contextmanager
def capture_checkpoints(callback):
    """Route checkpoints to callback until this context exits.

    Tokens restore nested sinks on success or failure. Context-local delivery
    lets independent searches run without replacing another module's state.
    """
    token = _sink.set(callback)
    try:
        yield
    finally:
        _sink.reset(token)


def emit_checkpoint(state):
    """Deliver a complete search snapshot to the active scoped callback."""

    callback = _sink.get()
    if callback is not None:
        callback(state)
