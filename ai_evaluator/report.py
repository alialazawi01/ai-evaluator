"""
Turns a RunReport into a summary, a terminal printout and a JSON file.

The JSON file is the contract for tools that read runs later (compare,
dashboard). Bump SCHEMA_VERSION when its shape changes.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, TextIO

from ai_evaluator.core.models import DIFFICULTIES, CaseResult, RunReport


SCHEMA_VERSION = 1


def summarize(report: RunReport) -> dict[str, Any]:

    cases = report.cases

    by_difficulty = {
        difficulty: rate(
            [c for c in cases if c.test_case.difficulty == difficulty]
        )
        for difficulty in DIFFICULTIES
        if any(c.test_case.difficulty == difficulty for c in cases)
    }

    by_check: dict[str, list] = {}
    for case in cases:
        for check in case.checks:
            by_check.setdefault(check.name, []).append(check)

    executions = [c.execution for c in cases if c.execution is not None]
    latencies = [e.latency_ms for e in executions]
    input_tokens = [e.input_tokens for e in executions if e.input_tokens is not None]
    output_tokens = [e.output_tokens for e in executions if e.output_tokens is not None]
    costs = [e.cost for e in executions if e.cost is not None]

    return {
        **rate(cases),
        "errors": sum(c.error is not None for c in cases),
        "duration_s": (report.finished_at - report.started_at).total_seconds(),
        "by_difficulty": by_difficulty,
        "by_check": {
            name: {
                "total": len(results),
                "passed": sum(r.passed for r in results),
                "pass_rate": sum(r.passed for r in results) / len(results),
                "avg_score": sum(r.score for r in results) / len(results),
            }
            for name, results in by_check.items()
        },
        "latency_ms": {
            "avg": sum(latencies) / len(latencies),
            "max": max(latencies),
        } if latencies else None,
        "tokens": {
            "input": sum(input_tokens),
            "output": sum(output_tokens),
        } if input_tokens or output_tokens else None,
        "cost": sum(costs) if costs else None,
    }


def rate(cases: list[CaseResult]) -> dict[str, Any]:

    passed = sum(c.passed for c in cases)

    return {
        "total": len(cases),
        "passed": passed,
        "pass_rate": passed / len(cases) if cases else 0.0,
    }


# ---------------------------------------------------------------- terminal


def print_report(
    report: RunReport,
    verbose: bool = False,
    stream: TextIO | None = None
) -> None:
    """Print one line per case, the reasons for failures, and a summary."""

    out = stream or sys.stdout
    color = Colors(enabled=use_color(out))
    summary = summarize(report)

    width = max((len(c.test_case.id) for c in report.cases), default=0)
    check_width = max(
        (len(check.name) for c in report.cases for check in c.checks),
        default=0
    )

    print(file=out)

    for case in report.cases:

        if case.error:
            mark = color.yellow("!")
        elif case.passed:
            mark = color.green("✓")
        else:
            mark = color.red("✗")

        print(
            f"  {mark} {case.test_case.id:<{width}}  "
            f"{color.dim(case.test_case.difficulty)}",
            file=out
        )

        if case.error:
            print(f"      {color.yellow('error')}  {case.error}", file=out)
            continue

        for check in case.checks:
            if verbose or not check.passed:
                name = f"{check.name:<{check_width}}"
                label = color.green(name) if check.passed else color.red(name)
                print(
                    f"      {label}  {check.score:.2f}  {check.reason}",
                    file=out
                )

    print(f"\n{color.bold('Summary')}", file=out)

    passed_text = f"{summary['passed']}/{summary['total']} passed ({summary['pass_rate']:.0%})"
    all_passed = summary["passed"] == summary["total"]
    print(
        f"  Cases       "
        f"{color.green(passed_text) if all_passed else color.red(passed_text)}"
        + (
            f", {summary['errors']} error{'s' if summary['errors'] > 1 else ''}"
            if summary["errors"] else ""
        ),
        file=out
    )

    if summary["by_difficulty"]:
        print("  Difficulty", file=out)
        for name, stats in summary["by_difficulty"].items():
            print(f"    {name:<12}{fraction(stats)}", file=out)

    if summary["by_check"]:
        print("  Checks", file=out)
        for name, stats in summary["by_check"].items():
            avg_score = f"avg score {stats['avg_score']:.2f}"
            print(
                f"    {name:<{check_width + 2}}{fraction(stats)}  "
                f"{color.dim(avg_score)}",
                file=out
            )

    if summary["latency_ms"]:
        latency = summary["latency_ms"]
        print(
            f"  Latency     avg {latency['avg']:.1f} ms, "
            f"max {latency['max']:.1f} ms",
            file=out
        )

    if summary["tokens"]:
        tokens = summary["tokens"]
        print(
            f"  Tokens      {tokens['input']} in, {tokens['output']} out",
            file=out
        )

    if summary["cost"] is not None:
        print(f"  Cost        ${summary['cost']:.4f}", file=out)

    print(f"  Duration    {summary['duration_s']:.2f} s", file=out)


def fraction(stats: dict[str, Any]) -> str:
    return f"{stats['passed']:>3}/{stats['total']:<3} {stats['pass_rate']:>4.0%}"


def use_color(stream: TextIO) -> bool:
    return (
        hasattr(stream, "isatty")
        and stream.isatty()
        and "NO_COLOR" not in os.environ
    )


class Colors:

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def paint(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def green(self, text: str) -> str:
        return self.paint("32", text)

    def red(self, text: str) -> str:
        return self.paint("31", text)

    def yellow(self, text: str) -> str:
        return self.paint("33", text)

    def bold(self, text: str) -> str:
        return self.paint("1", text)

    def dim(self, text: str) -> str:
        return self.paint("2", text)


# -------------------------------------------------------------------- json


def report_to_dict(
    report: RunReport,
    config_path: str | None = None
) -> dict[str, Any]:

    return {
        "schema_version": SCHEMA_VERSION,
        "config": config_path,
        "target": report.target,
        "started_at": report.started_at.isoformat(),
        "finished_at": report.finished_at.isoformat(),
        "summary": summarize(report),
        "cases": [case_to_dict(case) for case in report.cases],
    }


def case_to_dict(case: CaseResult) -> dict[str, Any]:

    execution = case.execution

    return {
        "id": case.test_case.id,
        "difficulty": case.test_case.difficulty,
        "input": case.test_case.input,
        "expected": case.test_case.expected,
        "passed": case.passed,
        "error": case.error,
        "output": execution.output if execution else None,
        "latency_ms": execution.latency_ms if execution else None,
        "input_tokens": execution.input_tokens if execution else None,
        "output_tokens": execution.output_tokens if execution else None,
        "cost": execution.cost if execution else None,
        "retrieved_docs": execution.retrieved_docs if execution else None,
        "steps": execution.steps if execution else None,
        "metadata": execution.metadata if execution else {},
        "checks": [
            {
                "name": check.name,
                "score": check.score,
                "passed": check.passed,
                "reason": check.reason,
            }
            for check in case.checks
        ],
    }


def save_report(
    report: RunReport,
    output_dir: str | Path = "runs",
    config_path: str | None = None
) -> Path:
    """Write the run to output_dir/<start time>.json and return the path."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = report.started_at.astimezone().strftime("%Y-%m-%d_%H%M%S")
    path = output_dir / f"{stem}.json"

    number = 2
    while path.exists():
        path = output_dir / f"{stem}_{number}.json"
        number += 1

    path.write_text(
        # default=str keeps the run saved even if an output isn't JSON-friendly.
        json.dumps(
            report_to_dict(report, config_path),
            indent=2,
            ensure_ascii=False,
            default=str
        ),
        encoding="utf-8"
    )

    return path
