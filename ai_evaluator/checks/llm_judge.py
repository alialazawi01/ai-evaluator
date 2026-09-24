import json
from typing import Any

from ai_evaluator.core.check import Check
from ai_evaluator.core.models import (
    TestCase,
    ExecutionResult,
    CheckResult
)
from ai_evaluator.judges.base import Judge, MAX_SCORE


DEFAULT_CRITERIA = (
    "The response correctly and fully answers the input. If an expected "
    "answer is given, the response agrees with it, even if worded differently."
)

SYSTEM_PROMPT = f"""You are a strict, fair evaluator of AI responses.
Grade the response against the criteria only. Do not reward length or style
unless the criteria ask for it.

Reply with JSON only, in this exact form:
{{"reason": "<one or two sentences>", "score": <whole number 0-{MAX_SCORE}>}}

{MAX_SCORE} = fully meets the criteria, 0 = does not meet them at all."""


class LLMJudgeCheck(Check):
    """Asks an LLM to grade the output against written criteria."""

    name = "llm_judge"

    # Tells the registry to pass in the judge from the config.
    needs_judge = True

    def __init__(
        self,
        judge: Judge,
        criteria: str = DEFAULT_CRITERIA,
        threshold: float = 0.7
    ):
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")

        self.judge = judge
        self.criteria = criteria
        self.threshold = threshold

    def evaluate(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> CheckResult:

        grade = self.judge.grade(self.build_messages(test_case, result))

        return CheckResult(
            name=self.name,
            score=grade.score,
            passed=grade.score >= self.threshold,
            reason=grade.reason or "(judge gave no reason)"
        )

    def build_messages(
        self,
        test_case: TestCase,
        result: ExecutionResult
    ) -> list[dict[str, str]]:

        parts = [
            f"## Criteria\n{self.criteria}",
            f"## Input\n{as_text(test_case.input)}",
        ]

        if test_case.expected is not None:
            parts.append(f"## Expected answer\n{as_text(test_case.expected)}")

        parts.append(f"## Response to grade\n{as_text(result.output)}")

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n\n".join(parts)},
        ]


def as_text(value: Any) -> str:

    if isinstance(value, str):
        return value

    return json.dumps(value, ensure_ascii=False, default=str)
