from datetime import datetime, timezone

from .check import Check
from .models import TestCase, CheckResult, CaseResult, RunReport
from .target import Target


class Runner:

    def __init__(
        self,
        target: Target,
        checks: list[Check]
    ):
        self.target = target
        self.checks = checks

    def run(self, test_cases: list[TestCase]) -> RunReport:

        started_at = datetime.now(timezone.utc)

        cases = [
            self.run_case(test_case)
            for test_case in test_cases
        ]

        return RunReport(
            target=self.target.name,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            cases=cases
        )

    def run_case(self, test_case: TestCase) -> CaseResult:

        try:
            execution = self.target.run(test_case)
        except Exception as error:
            return CaseResult(
                test_case=test_case,
                execution=None,
                error=f"{type(error).__name__}: {error}"
            )

        check_results = []

        for check in [*self.checks, *test_case.checks]:
            try:
                result = check.evaluate(test_case, execution)
            except Exception as error:
                result = CheckResult(
                    name=check.name,
                    score=0.0,
                    passed=False,
                    reason=f"Check error: {type(error).__name__}: {error}"
                )

            check_results.append(result)

        return CaseResult(
            test_case=test_case,
            execution=execution,
            checks=check_results
        )
