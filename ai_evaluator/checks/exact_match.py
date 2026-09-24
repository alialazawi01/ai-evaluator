from ai_evaluator.core.check import Check
from ai_evaluator.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)


class ExactMatchCheck(Check):

    name = "exact_match"

    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:

        passed = (
            result.output.strip()
            == test_case.expected.strip()
        )

        return CheckResult(
            name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=(
                "Output matches expected output."
                if passed
                else "Output does not match expected output."
            )
        )