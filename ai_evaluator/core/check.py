from abc import ABC, abstractmethod

from .models import TestCase, ExecutionResult, CheckResult


class Check(ABC):
    """Judges the output of one test case."""

    name: str = "check"

    @abstractmethod
    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:
        pass
