from typing import Any

from ai_evaluator.core.check import Check
from ai_evaluator.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)


class ExactMatchCheck(Check):
    """Output must equal the expected value. Strings are compared trimmed."""

    name = "exact_match"

    def __init__(self, case_sensitive: bool = True):
        self.case_sensitive = case_sensitive

    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:

        if test_case.expected is None:
            return CheckResult(
                name=self.name,
                score=0.0,
                passed=False,
                reason="Test case has no expected value."
            )

        passed = (
            self.normalize(result.output)
            == self.normalize(test_case.expected)
        )

        return CheckResult(
            name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            reason=(
                "Output matches expected output."
                if passed
                else (
                    f"Expected {test_case.expected!r}, "
                    f"got {result.output!r}."
                )
            )
        )

    def normalize(self, value: Any) -> Any:

        if not isinstance(value, str):
            return value

        value = value.strip()

        return value if self.case_sensitive else value.lower()
