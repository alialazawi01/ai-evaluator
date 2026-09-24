# Temporary demo until the `ai-eval` CLI exists (build step 3).
import json

from ai_evaluator import FunctionTarget, Runner, TestCase
from ai_evaluator.checks import ExactMatchCheck, LatencyCheck


def fake_chatbot(prompt: str) -> str:

    answers = {
        "What is the capital of Sweden?": "Stockholm",
        "What is 25 * 17?": "425",
        "What is the capital of France?": "Paris"
    }

    return answers.get(prompt, "I don't know")


def load_test_cases():

    with open("datasets/chatbot_tests.json") as file:
        data = json.load(file)

    return [
        TestCase(**test)
        for test in data
    ]


def main():

    runner = Runner(
        target=FunctionTarget(fake_chatbot),
        checks=[
            ExactMatchCheck(),
            LatencyCheck(max_ms=100)
        ]
    )

    report = runner.run(load_test_cases())

    for case in report.cases:

        print(f"\n{case.test_case.id}")

        if case.error:
            print(f"  ERROR: {case.error}")
            continue

        for check in case.checks:

            status = "PASS" if check.passed else "FAIL"

            print(
                f"  {check.name}: "
                f"{status} "
                f"score={check.score:.2f}"
            )

            print(f"    {check.reason}")

    print(
        f"\nPassed {report.passed}/{report.total} "
        f"({report.pass_rate:.0%})"
    )


if __name__ == "__main__":
    main()
