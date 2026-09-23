from .adapter import Adapter
from .check import Check
from .models import TestCase, EvaluationResult


class Evaluator:

    def __init__(
        self,
        adapter: Adapter,
        checks: list[Check]
    ):
        self.adapter = adapter
        self.checks = checks

    def run(
        self,
        test_cases: list[TestCase]
    ) -> list[EvaluationResult]:

        results = []

        for test_case in test_cases:

            execution = self.adapter.run(test_case)

            check_results = []

            for check in self.checks:
                result = check.evaluate(
                    test_case,
                    execution
                )

                check_results.append(result)

            evaluation = EvaluationResult(
                test_case_id=test_case.id,
                checks=check_results
            )

            results.append(evaluation)

        return results