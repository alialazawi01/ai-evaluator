import time

from src.core.adapter import Adapter
from src.core.models import TestCase, ExecutionResult


class ChatbotAdapter(Adapter):

    def __init__(self, chatbot):
        self.chatbot = chatbot

    def run(self, test_case: TestCase) -> ExecutionResult:

        start = time.perf_counter()

        output = self.chatbot(test_case.input)

        end = time.perf_counter()

        latency_ms = (end - start) * 1000

        return ExecutionResult(
            test_case_id=test_case.id,
            output=output,
            latency_ms=latency_ms
        )