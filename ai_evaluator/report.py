from ai_evaluator.core.models import RunReport


def print_report(report: RunReport) -> None:

    for case in report.cases:

        status = "PASS" if case.passed else "FAIL"
        print(f"\n{status}  {case.test_case.id}  [{case.test_case.difficulty}]")

        if case.error:
            print(f"  ERROR: {case.error}")
            continue

        for check in case.checks:

            mark = "✓" if check.passed else "✗"

            print(f"  {mark} {check.name}  score={check.score:.2f}")
            print(f"      {check.reason}")

    print(
        f"\nPassed {report.passed}/{report.total} "
        f"({report.pass_rate:.0%})"
    )
