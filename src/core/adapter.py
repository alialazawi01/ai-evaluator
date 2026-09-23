from abc import ABC, abstractmethod

from .models import TestCase, ExecutionResult


class Adapter(ABC):

    @abstractmethod
    def run(self, test_case: TestCase) -> ExecutionResult:
        pass