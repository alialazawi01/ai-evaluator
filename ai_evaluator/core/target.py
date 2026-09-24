from abc import ABC, abstractmethod

from .models import TestCase, ExecutionResult


class Target(ABC):
    """Knows how to call one AI system."""

    name: str = "target"

    @abstractmethod
    def run(self, test_case: TestCase) -> ExecutionResult:
        pass
