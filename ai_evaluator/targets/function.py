import importlib
import os
import sys
import time
from dataclasses import fields
from typing import Any, Callable

from ai_evaluator.core.models import TestCase, ExecutionResult
from ai_evaluator.core.target import Target


# Keys a function may return that map straight onto ExecutionResult.
RESULT_FIELDS = {
    f.name for f in fields(ExecutionResult)
} - {"latency_ms", "metadata"}


class FunctionTarget(Target):
    """Calls a Python function with each test case input."""

    def __init__(
        self,
        func: Callable[[Any], Any],
        name: str | None = None
    ):
        self.func = func
        self.name = name or f"{func.__module__}:{func.__qualname__}"

    @classmethod
    def from_path(cls, path: str) -> "FunctionTarget":
        """Load a function from "module:function", e.g. "my_bot.app:ask"."""

        module_name, sep, func_name = path.partition(":")

        if not sep or not module_name or not func_name:
            raise ValueError(
                f"Target must look like 'module:function', got '{path}'"
            )

        # Allow importing the user's code from the folder they run in.
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())

        module = importlib.import_module(module_name)
        func = getattr(module, func_name, None)

        if not callable(func):
            raise ValueError(
                f"'{func_name}' in module '{module_name}' is not a function"
            )

        return cls(func, name=path)

    def run(self, test_case: TestCase) -> ExecutionResult:

        start = time.perf_counter()

        raw = self.func(test_case.input)

        latency_ms = (time.perf_counter() - start) * 1000

        return to_execution_result(raw, latency_ms)


def to_execution_result(raw: Any, latency_ms: float) -> ExecutionResult:
    """
    A plain return value becomes the output. A dict with an "output" key
    fills the matching ExecutionResult fields, and other keys go to metadata.
    """

    if not (isinstance(raw, dict) and "output" in raw):
        return ExecutionResult(output=raw, latency_ms=latency_ms)

    known = {k: v for k, v in raw.items() if k in RESULT_FIELDS}
    metadata = dict(raw.get("metadata") or {})
    metadata.update({
        k: v for k, v in raw.items()
        if k not in RESULT_FIELDS and k != "metadata"
    })

    return ExecutionResult(
        latency_ms=latency_ms,
        metadata=metadata,
        **known
    )
