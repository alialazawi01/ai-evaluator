"""A fake chatbot to try the evaluator with. Replace it with your own AI."""

ANSWERS = {
    "What is the capital of Sweden?": "The capital of Sweden is Stockholm.",
    "What is 25 * 17?": "425",
    "What is the capital of France?": "Paris",
}


def ask(question: str) -> str:
    return ANSWERS.get(question, "I don't know.")
