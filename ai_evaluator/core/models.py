from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TestCase:
    # Stops pytest from trying to collect this class as a test.
    __test__ = False

    id: str
    input: Any
    expected: Any | None = None
    difficulty: str = "medium"


@dataclass
class ExecutionResult:
    output: Any
    latency_ms: float

    input_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None

    # RAG: documents the system looked up before answering.
    retrieved_docs: list[Any] | None = None
    # Agent: actions or tool calls the system made.
    steps: list[Any] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    name: str
    score: float
    passed: bool
    reason: str = ""


@dataclass
class CaseResult:
    test_case: TestCase
    execution: ExecutionResult | None
    checks: list[CheckResult] = field(default_factory=list)

    # Set when the target raised, in which case no checks were run.
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and all(
            check.passed for check in self.checks
        )


@dataclass
class RunReport:
    target: str
    started_at: datetime
    finished_at: datetime
    cases: list[CaseResult]

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed(self) -> int:
        return sum(case.passed for case in self.cases)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0
