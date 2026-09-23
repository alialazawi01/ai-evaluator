from src.core.check import Check
from src.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)


class LatencyCheck(Check):

    def __init__(self, max_ms: float):
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
            name="latency",
            score=score,
            passed=passed,
            reason=f"Latency: {result.latency_ms:.2f} ms"
        )