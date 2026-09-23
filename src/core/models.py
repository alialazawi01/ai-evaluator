from dataclasses import dataclass
from typing import Any


@dataclass
class TestCase:
    id: str
    input: Any
    expected_output: Any | None = None
    difficulty: str = "medium"


@dataclass
class ExecutionResult:
    test_case_id: str
    output: Any

    latency_ms: float

    input_tokens: int | None = None
    output_tokens: int | None = None
    cost: float | None = None

    metadata: dict[str, Any] | None = None


@dataclass
class CheckResult:
    name: str
    score: float
    passed: bool
    reason: str = ""


@dataclass
class EvaluationResult:
    test_case_id: str
    checks: list[CheckResult]