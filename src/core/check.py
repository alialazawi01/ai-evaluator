from abc import ABC, abstractmethod

from .models import TestCase, ExecutionResult, CheckResult


class Check(ABC):

    @abstractmethod
    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:
        pass