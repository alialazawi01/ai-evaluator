"""
Turns check specs from config files into Check objects.

A spec is either a name, or a one-key dict of name to options:

    "exact_match"
    {"latency": {"max_ms": 3000}}

Checks with needs_judge = True get the judge from the config passed in.
"""

from typing import Any

from ai_evaluator.core.check import Check
from ai_evaluator.judges.base import Judge

from .contains import ContainsExpectedCheck
from .exact_match import ExactMatchCheck
from .latency import LatencyCheck
from .llm_judge import LLMJudgeCheck


CHECKS: dict[str, type[Check]] = {}


def register_check(check_class: type[Check]) -> type[Check]:
    """Make a check usable by name in config files. Works as a decorator."""

    CHECKS[check_class.name] = check_class

    return check_class


for check_class in (
    ExactMatchCheck,
    ContainsExpectedCheck,
    LatencyCheck,
    LLMJudgeCheck,
):
    register_check(check_class)


def build_check(
    spec: str | dict[str, Any],
    judge: Judge | None = None
) -> Check:

    if isinstance(spec, str):
        name, options = spec, {}
    elif isinstance(spec, dict) and len(spec) == 1:
        name, options = next(iter(spec.items()))
        options = options or {}
    else:
        raise ValueError(
            f"Invalid check {spec!r}. Use a name like 'exact_match' "
            "or a single mapping like {'latency': {'max_ms': 3000}}."
        )

    if name not in CHECKS:
        raise ValueError(
            f"Unknown check '{name}'. "
            f"Available checks: {', '.join(sorted(CHECKS))}"
        )

    if not isinstance(options, dict):
        raise ValueError(
            f"Options for check '{name}' must be a mapping, got {options!r}"
        )

    if getattr(CHECKS[name], "needs_judge", False):
        if judge is None:
            raise ValueError(
                f"Check '{name}' needs a 'judge' section in the eval config"
            )
        options = {**options, "judge": judge}

    try:
        return CHECKS[name](**options)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid options for check '{name}': {error}")


def build_checks(
    specs: list[str | dict[str, Any]],
    judge: Judge | None = None
) -> list[Check]:

    return [build_check(spec, judge) for spec in specs]
