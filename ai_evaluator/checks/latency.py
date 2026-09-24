from ai_evaluator.core.check import Check
from ai_evaluator.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)


class LatencyCheck(Check):
    """Passes if the call took at most max_ms. Slower calls score lower."""

    name = "latency"

    def __init__(self, max_ms: float):

        if max_ms <= 0:
            raise ValueError("max_ms must be greater than 0")

        self.max_ms = max_ms

    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:

        passed = result.latency_ms <= self.max_ms

        score = min(
            1.0,
            self.max_ms / max(result.latency_ms, 1)
        )

        return CheckResult(
            name=self.name,
            score=score,
            passed=passed,
            reason=(
                f"Latency: {result.latency_ms:.2f} ms "
                f"(limit {self.max_ms:g} ms)"
            )
        )
