"""
Loads an eval config file and its dataset into ready-to-run objects.

    target: my_bot.app:ask
    dataset: cases.yaml          # relative to this config file
    judge:                       # only needed for llm_judge checks
      provider: ollama
      model: qwen2.5:7b
    default_checks:
      - latency: { max_ms: 3000 }
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ai_evaluator.checks.registry import build_checks
from ai_evaluator.core.check import Check
from ai_evaluator.core.models import DIFFICULTIES, TestCase
from ai_evaluator.core.target import Target
from ai_evaluator.judges import Judge, build_judge
from ai_evaluator.targets.function import FunctionTarget


CONFIG_KEYS = {"target", "dataset", "judge", "default_checks"}
CASE_KEYS = {"id", "input", "expected", "difficulty", "checks"}


class ConfigError(Exception):
    """A config or dataset file is missing, malformed or invalid."""


@dataclass
class EvalConfig:
    target: Target
    checks: list[Check]
    test_cases: list[TestCase]
    judge: Judge | None = None

    @property
    def uses_judge(self) -> bool:
        checks = [*self.checks, *(c for t in self.test_cases for c in t.checks)]
        return any(getattr(check, "needs_judge", False) for check in checks)


def load_config(path: str | Path) -> EvalConfig:

    path = Path(path)
    data = read_file(path)

    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected a mapping at the top level")

    unknown = set(data) - CONFIG_KEYS
    if unknown:
        raise ConfigError(
            f"{path}: unknown keys {sorted(unknown)}. "
            f"Allowed keys: {sorted(CONFIG_KEYS)}"
        )

    for key in ("target", "dataset"):
        if not data.get(key):
            raise ConfigError(f"{path}: '{key}' is required")

    try:
        target = FunctionTarget.from_path(data["target"])
    except Exception as error:
        # Importing the user's module can fail in any way (e.g. a syntax error).
        raise ConfigError(
            f"{path}: could not load target: {type(error).__name__}: {error}"
        )

    judge = None
    if data.get("judge") is not None:
        try:
            judge = build_judge(data["judge"])
        except ValueError as error:
            raise ConfigError(f"{path}: {error}")

    checks = checks_from(
        data.get("default_checks") or [],
        f"{path}: default_checks",
        judge
    )

    return EvalConfig(
        target=target,
        checks=checks,
        test_cases=load_dataset(path.parent / data["dataset"], judge),
        judge=judge
    )


def load_dataset(
    path: str | Path,
    judge: Judge | None = None
) -> list[TestCase]:
    """Load test cases from a YAML or JSON list."""

    path = Path(path)
    data = read_file(path)

    if not isinstance(data, list):
        raise ConfigError(f"{path}: expected a list of test cases")

    test_cases = [
        parse_case(item, f"{path}: case {number}", judge)
        for number, item in enumerate(data, start=1)
    ]

    seen = set()
    for test_case in test_cases:
        if test_case.id in seen:
            raise ConfigError(f"{path}: duplicate id '{test_case.id}'")
        seen.add(test_case.id)

    return test_cases


def parse_case(item: Any, where: str, judge: Judge | None = None) -> TestCase:

    if not isinstance(item, dict):
        raise ConfigError(f"{where}: expected a mapping")

    unknown = set(item) - CASE_KEYS
    if unknown:
        raise ConfigError(
            f"{where}: unknown keys {sorted(unknown)}. "
            f"Allowed keys: {sorted(CASE_KEYS)}"
        )

    for key in ("id", "input"):
        if key not in item:
            raise ConfigError(f"{where}: '{key}' is required")

    where = f"{where} ('{item['id']}')"

    difficulty = item.get("difficulty", "medium")
    if difficulty not in DIFFICULTIES:
        raise ConfigError(
            f"{where}: difficulty must be one of {', '.join(DIFFICULTIES)}"
        )

    return TestCase(
        id=str(item["id"]),
        input=item["input"],
        expected=item.get("expected"),
        difficulty=difficulty,
        checks=checks_from(item.get("checks") or [], f"{where}: checks", judge)
    )


def checks_from(
    specs: Any,
    where: str,
    judge: Judge | None = None
) -> list[Check]:

    if not isinstance(specs, list):
        raise ConfigError(f"{where}: expected a list")

    try:
        return build_checks(specs, judge)
    except ValueError as error:
        raise ConfigError(f"{where}: {error}")


def read_file(path: Path) -> Any:

    if not path.is_file():
        raise ConfigError(f"File not found: {path}")

    text = path.read_text(encoding="utf-8")

    try:
        if path.suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        raise ConfigError(f"{path}: could not parse file: {error}")
