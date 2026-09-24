from ai_evaluator.core.check import Check
from ai_evaluator.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)


class ContainsExpectedCheck(Check):
    """
    Output must contain the expected text. If expected is a list, every item
    must appear, and the score is the share of items found.
    """

    name = "contains_expected"

    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive

    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:

        expected = test_case.expected

        if expected is None or expected == []:
            return CheckResult(
                name=self.name,
                score=0.0,
                passed=False,
                reason="Test case has no expected value."
            )

        wanted = expected if isinstance(expected, list) else [expected]
        output = self.normalize(result.output)

        missing = [
            item for item in wanted
            if self.normalize(item) not in output
        ]

        score = 1 - len(missing) / len(wanted)
        passed = not missing

        return CheckResult(
            name=self.name,
            score=score,
            passed=passed,
            reason=(
                "Output contains all expected text."
                if passed
                else f"Missing from output: {missing}"
            )
        )

    def normalize(self, value) -> str:

        text = str(value)

        return text if self.case_sensitive else text.lower()
