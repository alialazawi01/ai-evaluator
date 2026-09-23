import json

from src.core.models import TestCase
from src.core.evaluator import Evaluator

from src.adapters.chatbot import ChatbotAdapter

from src.checks.exact_match import ExactMatchCheck
from src.checks.latency import LatencyCheck


def fake_chatbot(prompt: str) -> str:

    answers = {
        "What is the capital of Sweden?": "Stockholm",
        "What is 25 * 17?": "425",
        "What is the capital of France?": "Paris"
    }

    return answers.get(prompt, "I don't know")


def load_test_cases():

    with open("tests/chatbot_tests.json") as file:
        data = json.load(file)

    return [
        TestCase(**test)
        for test in data
    ]


def main():

    test_cases = load_test_cases()

    adapter = ChatbotAdapter(
        chatbot=fake_chatbot
    )

    checks = [
        ExactMatchCheck(),
        LatencyCheck(max_ms=100)
    ]

    evaluator = Evaluator(
        adapter=adapter,
        checks=checks
    )

    results = evaluator.run(test_cases)

    for result in results:

        print(f"\n{result.test_case_id}")

        for check in result.checks:

            status = "PASS" if check.passed else "FAIL"

            print(
                f"  {check.name}: "
                f"{status} "
                f"score={check.score:.2f}"
            )

            print(f"    {check.reason}")


if __name__ == "__main__":
    main()