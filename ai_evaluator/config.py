"""
Loads an eval config file and its dataset into ready-to-run objects.

    target: my_bot.app:ask
    dataset: cases.yaml          # relative to this config file
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
from ai_evaluator.core.models import TestCase
from ai_evaluator.core.target import Target
from ai_evaluator.targets.function import FunctionTarget


CONFIG_KEYS = {"target", "dataset", "default_checks"}
CASE_KEYS = {"id", "input", "expected", "difficulty", "checks"}
DIFFICULTIES = ("easy", "medium", "hard")


class ConfigError(Exception):
    """A config or dataset file is missing, malformed or invalid."""


@dataclass
class EvalConfig:
    target: Target
    checks: list[Check]
    test_cases: list[TestCase]


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

    checks = checks_from(data.get("default_checks") or [], f"{path}: default_checks")

    return EvalConfig(
        target=target,
        checks=checks,
        test_cases=load_dataset(path.parent / data["dataset"])
    )


def load_dataset(path: str | Path) -> list[TestCase]:
    """Load test cases from a YAML or JSON list."""

    path = Path(path)
    data = read_file(path)

    if not isinstance(data, list):
        raise ConfigError(f"{path}: expected a list of test cases")

    test_cases = [
        parse_case(item, f"{path}: case {number}")
        for number, item in enumerate(data, start=1)
    ]

    seen = set()
    for test_case in test_cases:
        if test_case.id in seen:
            raise ConfigError(f"{path}: duplicate id '{test_case.id}'")
        seen.add(test_case.id)

    return test_cases


def parse_case(item: Any, where: str) -> TestCase:

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
        checks=checks_from(item.get("checks") or [], f"{where}: checks")
    )


def checks_from(specs: Any, where: str) -> list[Check]:

    if not isinstance(specs, list):
        raise ConfigError(f"{where}: expected a list")

    try:
        return build_checks(specs)
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
