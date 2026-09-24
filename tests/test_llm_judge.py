import textwrap

import pytest

from ai_evaluator import ExecutionResult, TestCase
from ai_evaluator.checks import LLMJudgeCheck, build_check
from ai_evaluator.config import ConfigError, load_config
from ai_evaluator.judges import Judge, OllamaJudge


class FakeJudge(Judge):

    name = "fake"

    def __init__(self, reply='{"score": 8, "reason": "Close enough."}'):
        super().__init__("fake-model")
        self.reply = reply
        self.messages = None

    def chat(self, messages):
        self.messages = messages
        return self.reply


def evaluate(check, output="Stockholm", expected=None, input="Capital of Sweden?"):
    case = TestCase(id="t1", input=input, expected=expected)
    return check.evaluate(case, ExecutionResult(output, 5.0))


def test_passes_when_score_meets_threshold():

    result = evaluate(LLMJudgeCheck(FakeJudge(), threshold=0.8))

    assert result.name == "llm_judge"
    assert result.score == pytest.approx(0.8)
    assert result.passed
    assert result.reason == "Close enough."


def test_fails_below_threshold():

    result = evaluate(LLMJudgeCheck(FakeJudge(), threshold=0.9))

    assert not result.passed


def test_prompt_contains_criteria_input_expected_and_output():

    judge = FakeJudge()
    check = LLMJudgeCheck(judge, criteria="Must be polite.")

    evaluate(check, output={"answer": "Stockholm"}, expected="Stockholm")

    system, user = judge.messages
    assert system["role"] == "system" and "JSON" in system["content"]
    assert "Must be polite." in user["content"]
    assert "Capital of Sweden?" in user["content"]
    assert "## Expected answer\nStockholm" in user["content"]
    assert '{"answer": "Stockholm"}' in user["content"]


def test_prompt_leaves_out_missing_expected():

    judge = FakeJudge()

    evaluate(LLMJudgeCheck(judge), expected=None)

    assert "Expected answer" not in judge.messages[1]["content"]


def test_rejects_bad_threshold():

    with pytest.raises(ValueError):
        LLMJudgeCheck(FakeJudge(), threshold=7)


def test_registry_passes_judge_in():

    judge = FakeJudge()

    check = build_check({"llm_judge": {"criteria": "Be short."}}, judge=judge)

    assert check.judge is judge
    assert check.criteria == "Be short."


def test_registry_requires_judge():

    with pytest.raises(ValueError, match="needs a 'judge' section"):
        build_check("llm_judge")


def test_registry_reports_bad_threshold_as_invalid_options():

    with pytest.raises(ValueError, match="Invalid options for check 'llm_judge'"):
        build_check({"llm_judge": {"threshold": 5}}, judge=FakeJudge())


# ------------------------------------------------------------------ config


def write_eval(tmp_path, config, cases):
    (tmp_path / "cases.yaml").write_text(textwrap.dedent(cases))
    (tmp_path / "eval.yaml").write_text(textwrap.dedent(config))
    return tmp_path / "eval.yaml"


def test_config_builds_judge_for_default_and_case_checks(tmp_path):

    path = write_eval(
        tmp_path,
        """
        target: examples.quickstart.bot:ask
        dataset: cases.yaml
        judge: {provider: ollama, model: qwen2.5:7b}
        default_checks: [llm_judge]
        """,
        """
        - id: a
          input: hi
          checks:
            - llm_judge: {criteria: Be kind.}
        - id: b
          input: hi
        """,
    )

    config = load_config(path)

    assert isinstance(config.judge, OllamaJudge)
    assert config.checks[0].judge is config.judge
    assert config.test_cases[0].checks[0].judge is config.judge
    assert config.uses_judge


def test_config_without_judge_checks_does_not_use_judge(tmp_path):

    path = write_eval(
        tmp_path,
        """
        target: examples.quickstart.bot:ask
        dataset: cases.yaml
        judge: {provider: ollama, model: qwen2.5:7b}
        """,
        "- {id: a, input: hi}\n",
    )

    assert not load_config(path).uses_judge


def test_config_llm_judge_without_judge_section(tmp_path):

    path = write_eval(
        tmp_path,
        "target: examples.quickstart.bot:ask\ndataset: cases.yaml\n",
        "- {id: a, input: hi, checks: [llm_judge]}\n",
    )

    with pytest.raises(ConfigError, match="case 1 \\('a'\\): checks: .*needs a 'judge'"):
        load_config(path)


def test_config_bad_judge(tmp_path):

    path = write_eval(
        tmp_path,
        "target: examples.quickstart.bot:ask\ndataset: cases.yaml\n"
        "judge: {provider: gpt}\n",
        "- {id: a, input: hi}\n",
    )

    with pytest.raises(ConfigError, match="provider must be one of"):
        load_config(path)
