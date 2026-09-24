import textwrap

import pytest

from ai_evaluator.checks import ContainsExpectedCheck, LatencyCheck
from ai_evaluator.config import ConfigError, load_config, load_dataset


def fake_bot(question):
    return f"Answer: {question}"


def write(path, text):
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return path


@pytest.fixture
def dataset(tmp_path):
    return write(tmp_path / "cases.yaml", """
        - id: one
          input: hello
          expected: hello
          difficulty: easy
          checks: [contains_expected]
        - id: two
          input: bye
    """)


def test_loads_config_with_target_checks_and_dataset(tmp_path, dataset):

    config_path = write(tmp_path / "eval.yaml", """
        target: tests.test_config:fake_bot
        dataset: cases.yaml
        default_checks:
          - latency: { max_ms: 500 }
    """)

    config = load_config(config_path)

    assert config.target.name == "tests.test_config:fake_bot"
    assert [type(c) for c in config.checks] == [LatencyCheck]
    assert [c.id for c in config.test_cases] == ["one", "two"]


def test_dataset_fields_and_defaults(dataset):

    one, two = load_dataset(dataset)

    assert one.expected == "hello"
    assert one.difficulty == "easy"
    assert [type(c) for c in one.checks] == [ContainsExpectedCheck]

    assert two.expected is None
    assert two.difficulty == "medium"
    assert two.checks == []


def test_loads_json_dataset(tmp_path):

    path = write(tmp_path / "cases.json", '[{"id": 1, "input": "hi"}]')

    (case,) = load_dataset(path)

    assert case.id == "1"


@pytest.mark.parametrize(
    "config, message",
    [
        ("dataset: cases.yaml", "'target' is required"),
        ("target: tests.test_config:fake_bot", "'dataset' is required"),
        ("target: x:y\ndataset: cases.yaml\nextra: 1", "unknown keys \\['extra'\\]"),
        ("target: no_such_module:ask\ndataset: cases.yaml", "could not load target"),
        ("target: tests.test_config:fake_bot\ndataset: missing.yaml", "File not found"),
        (
            "target: tests.test_config:fake_bot\ndataset: cases.yaml\n"
            "default_checks: [nope]",
            "default_checks: Unknown check 'nope'",
        ),
        ("- just a list", "expected a mapping"),
        ("target: [unclosed", "could not parse file"),
    ],
)
def test_config_errors(tmp_path, dataset, config, message):

    path = write(tmp_path / "eval.yaml", config)

    with pytest.raises(ConfigError, match=message):
        load_config(path)


@pytest.mark.parametrize(
    "cases, message",
    [
        ("id: one", "expected a list"),
        ("- just text", "case 1: expected a mapping"),
        ("- input: hi", "case 1: 'id' is required"),
        ("- id: a", "case 1: 'input' is required"),
        ("- {id: a, input: hi, expect: x}", "unknown keys \\['expect'\\]"),
        ("- {id: a, input: hi, difficulty: extreme}", "difficulty must be one of"),
        ("- {id: a, input: hi, checks: [nope]}", "case 1 \\('a'\\): checks: Unknown check"),
        ("- {id: a, input: hi, checks: exact_match}", "checks: expected a list"),
        ("- {id: a, input: hi}\n- {id: a, input: bye}", "duplicate id 'a'"),
    ],
)
def test_dataset_errors(tmp_path, cases, message):

    path = write(tmp_path / "cases.yaml", cases)

    with pytest.raises(ConfigError, match=message):
        load_dataset(path)
