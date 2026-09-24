import io
import json
from datetime import datetime, timedelta, timezone

from ai_evaluator import (
    CaseResult,
    CheckResult,
    ExecutionResult,
    RunReport,
    TestCase,
)
from ai_evaluator.report import print_report, save_report, summarize


START = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)


def case(id, difficulty, checks, latency_ms=10.0, error=None, **execution):
    return CaseResult(
        test_case=TestCase(id=id, input=f"in {id}", difficulty=difficulty),
        execution=None if error else ExecutionResult(
            output=f"out {id}", latency_ms=latency_ms, **execution
        ),
        checks=[CheckResult(name, score, score == 1.0, f"{name} reason")
                for name, score in checks],
        error=error,
    )


def make_report(cases):
    return RunReport(
        target="bot:ask",
        started_at=START,
        finished_at=START + timedelta(seconds=2),
        cases=cases,
    )


def sample_report():
    return make_report([
        case("a", "easy", [("exact", 1.0), ("latency", 1.0)], latency_ms=10,
             input_tokens=5, output_tokens=2, cost=0.01),
        case("b", "easy", [("exact", 0.0), ("latency", 1.0)], latency_ms=30,
             input_tokens=7, output_tokens=3, cost=0.02),
        case("c", "hard", [], error="ValueError: boom"),
    ])


def test_summary_totals_and_groups():

    summary = summarize(sample_report())

    assert summary["total"] == 3
    assert summary["passed"] == 1
    assert summary["errors"] == 1
    assert summary["duration_s"] == 2.0

    assert list(summary["by_difficulty"]) == ["easy", "hard"]
    assert summary["by_difficulty"]["easy"] == {"total": 2, "passed": 1, "pass_rate": 0.5}
    assert summary["by_difficulty"]["hard"]["passed"] == 0

    assert summary["by_check"]["exact"] == {
        "total": 2, "passed": 1, "pass_rate": 0.5, "avg_score": 0.5
    }
    assert summary["by_check"]["latency"]["pass_rate"] == 1.0

    assert summary["latency_ms"] == {"avg": 20.0, "max": 30.0}
    assert summary["tokens"] == {"input": 12, "output": 5}
    assert summary["cost"] == 0.03


def test_summary_without_optional_metrics():

    summary = summarize(make_report([case("a", "medium", [("exact", 1.0)])]))

    assert summary["tokens"] is None
    assert summary["cost"] is None


def test_summary_of_empty_run():

    summary = summarize(make_report([]))

    assert summary["total"] == 0
    assert summary["pass_rate"] == 0.0
    assert summary["by_difficulty"] == {}
    assert summary["latency_ms"] is None


def test_print_shows_failures_and_summary():

    out = io.StringIO()
    print_report(sample_report(), stream=out)
    text = out.getvalue()

    assert "exact reason" in text             # failed check is explained
    assert "latency reason" not in text       # passed checks hidden
    assert "ValueError: boom" in text
    assert "1/3 passed (33%), 1 error" in text
    assert "Tokens      12 in, 5 out" in text
    assert "Cost        $0.0300" in text
    assert "\033[" not in text                # no colors when not a terminal


def test_verbose_prints_passed_checks():

    out = io.StringIO()
    print_report(sample_report(), verbose=True, stream=out)

    assert "latency reason" in out.getvalue()


def test_save_report_writes_json(tmp_path):

    path = save_report(sample_report(), tmp_path / "runs", config_path="eval.yaml")

    data = json.loads(path.read_text())

    assert path.parent == tmp_path / "runs"
    assert data["schema_version"] == 1
    assert data["config"] == "eval.yaml"
    assert data["target"] == "bot:ask"
    assert data["summary"]["passed"] == 1

    first, _, crashed = data["cases"]
    assert first["output"] == "out a"
    assert first["checks"][0] == {
        "name": "exact", "score": 1.0, "passed": True, "reason": "exact reason"
    }
    assert crashed["error"] == "ValueError: boom"
    assert crashed["output"] is None


def test_save_report_never_overwrites(tmp_path):

    first = save_report(sample_report(), tmp_path)
    second = save_report(sample_report(), tmp_path)

    assert first != second
    assert second.name.endswith("_2.json")


def test_save_report_handles_non_json_output(tmp_path):

    report = make_report([case("a", "easy", [])])
    report.cases[0].execution.output = {1, 2}   # a set is not JSON

    data = json.loads(save_report(report, tmp_path).read_text())

    assert data["cases"][0]["output"] == "{1, 2}"
