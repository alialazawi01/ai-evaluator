from src.core.check import Check
from src.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)


class ExactMatchCheck(Check):

    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:

        passed = (
            result.output.strip()
            == test_case.expected_output.strip()
        )

        return CheckResult(
            name="exact_match",
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=(
                "Output matches expected output."
                if passed
                else "Output does not match expected output."
            )
        )