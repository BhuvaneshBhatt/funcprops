"""Optional process-isolated time budgets for expensive public queries."""

from __future__ import annotations

import contextlib
import functools
import inspect
import io
import math
import os
import pickle
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import sympy as sp

from ._source_transport import _dumps
from .results import (
    Convexity,
    DetailedPropertyResult,
    Monotonicity,
    PropertyResult,
    Sign,
    TruthValue,
)

PROPERTY_BUDGET_OPERATIONS = frozenset(
    (
        "range",
        "sign",
        "monotonicity",
        "convexity",
        "domain",
        "boundedness",
        "continuous",
        "differentiability",
        "smoothness",
        "smooth",
        "analytic",
        "meromorphic",
        "lipschitz",
        "uniformly_continuous",
        "holder_regularity",
        "variation",
        "integrability",
        "injective",
        "surjective",
        "bijective",
    )
)
_TYPED_BUDGET_OPERATIONS = PROPERTY_BUDGET_OPERATIONS - {
    "range",
    "sign",
    "monotonicity",
    "convexity",
}
_TYPED_BUDGET_OPERATIONS |= {
    "jacobian",
    "determinant_nonvanishing",
    "local_invertibility",
    "transformation_geometry",
    "change_of_variables",
}


@dataclass(frozen=True)
class BudgetedResult(PropertyResult):
    """Retain an unfinished query and explicit resource-exhaustion status."""

    complete: bool = False
    certified: bool = False
    operation: str | None = None
    query: object = None

    @property
    def outcome(self):
        return {
            "work-budget-exhausted": "resource-exhaustion",
            "work-budget-worker-failed": "worker-failure",
        }.get(self.source, "unsupported-replay")

    @property
    def classification(self):
        return self.primary

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return False

    def as_detailed_result(self):
        """Expose the mathematical value together with scope, cases and evidence."""

        return DetailedPropertyResult(
            self.primary,
            complete=False,
            source=self.source,
            evidence=self.evidence,
            exceptions=self.exceptions,
        )


def bounded_query(operation, expr, args, kwargs, seconds):
    """Run an authorized package operation in a worker with a hard wall-time budget."""

    if isinstance(seconds, bool):
        raise ValueError("work_budget must be a finite positive number of seconds")
    try:
        seconds = float(seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "work_budget must be a finite positive number of seconds"
        ) from exc
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("work_budget must be a finite positive number of seconds")
    env = os.environ.copy()
    root = str(Path(__file__).resolve().parent.parent)
    env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
    reason = "work-budget-exhausted"
    output = b""
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "funcprops.work_budget"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=(os.name == "posix"),
        )
        try:
            output, _ = process.communicate(
                _dumps((operation, expr, args, kwargs)), timeout=seconds
            )
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            output, _ = process.communicate()
            raise
        if process.returncode == 0:
            messages = _messages(output)
            kind, result = messages[-1]
            if kind == "error":
                raise result
            return result
        reason = "work-budget-worker-failed"
    except subprocess.TimeoutExpired:
        pass
    if operation in (
        "adaptive_quotient_isolation",
        "resume_adaptive_quotient_isolation",
    ):
        from .quotient_cofinal import _seed_run, _wall_run

        checkpoints = [
            value for kind, value in _messages(output) if kind == "checkpoint"
        ]
        options = {key: value for key, value in kwargs.items() if key != "stages"}
        run = (
            checkpoints[-1]
            if checkpoints
            else expr
            if operation == "resume_adaptive_quotient_isolation"
            else _seed_run(expr, *args, **options)
        )
        return _wall_run(run)
    if operation in ("adaptive_complex_isolation", "resume_adaptive_complex_isolation"):
        from .complex_cofinal import _seed_run, _wall_run

        checkpoints = [
            value for kind, value in _messages(output) if kind == "checkpoint"
        ]
        options = {key: value for key, value in kwargs.items() if key != "stages"}
        run = (
            checkpoints[-1]
            if checkpoints
            else expr
            if operation == "resume_adaptive_complex_isolation"
            else _seed_run(expr, *args, **options)
        )
        return _wall_run(run)
    if operation in (
        "certify_complex_isolation",
        "resume_complex_isolation",
        "isolate_complex_roots",
        "certify_quotient_isolation",
        "resume_quotient_isolation",
    ):
        from .complex_isolation import _seed, _wall_state
        from .quotient_isolation import (
            QuotientIsolationState,
            quotient_source_supported,
        )
        from .quotient_isolation import (
            _seed as quotient_seed,
        )
        from .quotient_isolation import (
            _wall_state as quotient_wall,
        )

        checkpoints = [
            value for kind, value in _messages(output) if kind == "checkpoint"
        ]
        state = checkpoints[-1] if checkpoints else None
        if operation == "isolate_complex_roots":
            from .transcendental.complex_roots import _timeout_isolation

            return _timeout_isolation(expr, args[0], args[1], kwargs, state)
        if state is None and operation == "resume_quotient_isolation":
            state = getattr(expr, "state", expr)
        if (
            state is None
            and operation in ("certify_quotient_isolation", "certify_complex_isolation")
            and quotient_source_supported(expr, args[0])
        ):
            state = quotient_seed(
                expr,
                *args,
                max_box_width=kwargs.get("max_box_width"),
                max_box_diameter=kwargs.get("max_box_diameter"),
                cancel=False,
            )
        if type(state) is QuotientIsolationState:
            return quotient_wall(state)
        if state is None:
            state = (
                getattr(expr, "state", expr)
                if operation == "resume_complex_isolation"
                else _seed(
                    expr,
                    *args,
                    max_box_width=kwargs.get("max_box_width"),
                    max_box_diameter=kwargs.get("max_box_diameter"),
                )
            )
        return (
            quotient_wall(state)
            if type(state) is QuotientIsolationState
            else _wall_state(state)
        )
    if operation in (
        "certify_complex_refinement",
        "certify_complex_multiple_root",
        "certify_quotient_refinement",
    ):
        return None
    if operation in ("adaptive_root_coverage", "resume_root_coverage"):
        from .adaptive_roots import _timeout_seed, _wall_result

        checkpoints = [
            value for kind, value in _messages(output) if kind == "checkpoint"
        ]
        state = (
            checkpoints[-1]
            if checkpoints
            else (
                getattr(expr, "state", expr)
                if operation == "resume_root_coverage"
                else _timeout_seed(
                    expr, args[0], args[1], kwargs.get("substitutions", ())
                )
            )
        )
        return _wall_result(state)
    if operation == "parameter_root_coverage":
        from dataclasses import replace

        from .parameter_coverage import _parameter_seed

        seed = _parameter_seed(
            expr, args[0], args[1], args[2], kwargs.get("parameter_domain", sp.S.Reals)
        )
        return replace(seed, exhaustion="wall-budget" if not seed.complete else None)
    if operation == "certify_parameter_box":
        from .parameter_coverage import _uniform_seed

        return _uniform_seed(expr, args[0], args[1], args[2], "wall-budget")
    if operation in ("certify_analytic_contour", "analytic_complex_coverage"):
        from .analytic_contours import AnalyticComplexCoverage, _seed

        c = _seed(expr, args[0], args[1], args[2], "wall-budget")
        return (
            c
            if operation == "certify_analytic_contour"
            else AnalyticComplexCoverage(
                c.expression,
                c.variable,
                c.rectangle,
                unresolved=(c.rectangle,),
                exhaustion="wall-budget",
            )
        )
    if operation == "certify_property_coverage":
        from .property_coverage import _seed

        return _seed(expr, args[0], args[1], "wall-budget")
    if operation == "replay_status":
        from .diagnostics import ReplayStatus

        return ReplayStatus(
            True, None, None, reason=reason, outcome="resource-exhaustion"
        )
    if operation == "track_domain":
        from .domain_tracking import DomainRecord

        variable = kwargs.get("var", args[0] if args else None)
        requested = kwargs.get("domain", args[1] if len(args) > 1 else sp.S.Reals)
        return DomainRecord(
            sp.sympify(expr),
            sp.sympify(variable),
            requested,
            None,
            None,
            False,
            reason=reason,
            natural_complete=False,
        )
    from .results import (
        Analyticity,
        Boundedness,
        Continuity,
        Differentiability,
        Meromorphicity,
    )

    unknown = {
        "continuous": Continuity.UNKNOWN,
        "differentiability": Differentiability.UNKNOWN,
        "analytic": Analyticity.UNKNOWN,
        "meromorphic": Meromorphicity.UNKNOWN,
        "boundedness": Boundedness.UNKNOWN,
        **{
            name: TruthValue.UNKNOWN
            for name in (
                "lipschitz",
                "uniformly_continuous",
                "injective",
                "surjective",
                "bijective",
                "determinant_nonvanishing",
                "local_invertibility",
            )
        },
        "certify_inequality": TruthValue.UNKNOWN,
        "sign": Sign.UNKNOWN,
        "monotonicity": Monotonicity.UNKNOWN,
        "convexity": Convexity.UNKNOWN,
    }.get(operation)
    if operation == "range":
        from .conditional import normalize_conditional_input

        expr = normalize_conditional_input(expr).expr
        var = kwargs.get(
            "variable", kwargs.get("var", args[0] if args else sp.Symbol("x"))
        )
        y = kwargs.get("y", args[1] if len(args) > 1 else sp.Symbol("y"))
        unknown = sp.Function("UnknownRange")(
            sp.sympify(expr), sp.sympify(var), sp.sympify(y)
        )
    result = BudgetedResult(
        unknown,
        source=reason,
        exceptions=(f"{seconds:g} second budget",),
        operation=operation,
        query=(expr, args, kwargs),
    )
    return (
        result
        if kwargs.get("return_result", False)
        or kwargs.get("return_certificate", False)
        or operation in _TYPED_BUDGET_OPERATIONS
        or operation
        in (
            "certify_parameter_geometry",
            "resume_parameter_geometry",
            "glue_branch_charts",
            "certify_branch_chart",
            "certify_finite_lipschitz",
            "certify_jump_variation",
            "encode_algebraic_coefficients",
            "certify_inequality",
            "certify_global_minimum",
            "prove_root_coverage",
            "enclose_expression",
            "enclose_derivative",
            "deflate_real_root",
            "certify_complex_cluster",
            "certify_extrema_bounds",
            "certify_log_atlas",
            "certify_root_value",
            "certify_implicit_multiplicity",
            "certify_common_zero",
        )
        else result.primary
    )


def budgeted_operation(function):
    """Expose the same isolated wall-clock budget on certified operations."""

    @functools.wraps(function)
    def wrapped(*args, work_budget=None, **kwargs):
        if work_budget is None:
            return function(*args, **kwargs)
        bound = inspect.signature(function).bind(*args, **kwargs)
        bound.apply_defaults()
        first = next(iter(inspect.signature(function).parameters))
        expression = bound.arguments.pop(first)
        return bounded_query(
            function.__name__, expression, (), dict(bound.arguments), work_budget
        )

    signature = inspect.signature(function)
    parameters = list(signature.parameters.values())
    parameters.append(
        inspect.Parameter("work_budget", inspect.Parameter.KEYWORD_ONLY, default=None)
    )
    wrapped.__signature__ = signature.replace(parameters=parameters)
    return wrapped


def main():
    """Execute a worker query and transport its result, exceptions and complete checkpoints."""

    operation, expr, args, kwargs = pickle.loads(sys.stdin.buffer.read())
    import funcprops

    channel = sys.stdout.buffer
    from ._checkpoints import capture_checkpoints

    def checkpoint(state):
        channel.write(_dumps(("checkpoint", state)))
        channel.flush()

    with capture_checkpoints(checkpoint), contextlib.redirect_stdout(sys.stderr):
        try:
            result = ("ok", getattr(funcprops, operation)(expr, *args, **kwargs))
        except Exception as exc:  # noqa: BLE001 - transported to the calling process unchanged
            result = ("error", exc)
    sys.stdout.buffer.write(_dumps(result))


def _messages(output):
    """Read completed frames; a killed worker may leave a final partial frame."""
    stream, messages = io.BytesIO(output), []
    while stream.tell() < len(output):
        try:
            value = pickle.load(stream)
        except (EOFError, pickle.UnpicklingError):
            break
        messages.append(value)
    return messages


if __name__ == "__main__":
    main()
