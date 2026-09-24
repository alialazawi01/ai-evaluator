"""
A fake support bot for a Swedish energy company, with some deliberately bad
answers, to see how the LLM judge grades them.
"""

ANSWERS = {
    "How do I report a power outage?":
        "You can report an outage on our website under 'Driftinformation' "
        "or call our 24/7 support line.",
    "What is the capital of Sweden?":
        "Stockholm is the capital, but I can only help with questions about "
        "your electricity and heating services.",
    "Can you write me a poem about cats?":
        "Soft paws at dawn, a purring song, the cat decides where it belongs.",
    "Why is my bill so high?":
        "Figure it out yourself.",
}


def ask(question: str) -> str:
    return ANSWERS.get(question, "Sorry, I don't know.")
