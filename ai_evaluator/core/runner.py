from datetime import datetime, timezone
from typing import Callable

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

    def run(
        self,
        test_cases: list[TestCase],
        on_case_done: Callable[[int, int, CaseResult], None] | None = None
    ) -> RunReport:
        """on_case_done(number, total, result) is called after each case."""

        started_at = datetime.now(timezone.utc)

        cases = []

        for number, test_case in enumerate(test_cases, start=1):

            case = self.run_case(test_case)
            cases.append(case)

            if on_case_done:
                on_case_done(number, len(test_cases), case)

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
