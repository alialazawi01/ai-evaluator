from typing import Any

from .base import Grade, Judge, JudgeError, parse_grade
from .huggingface import HuggingFaceJudge
from .ollama import OllamaJudge


JUDGES: dict[str, type[Judge]] = {
    "ollama": OllamaJudge,
    "huggingface": HuggingFaceJudge,
}


def build_judge(spec: dict[str, Any]) -> Judge:
    """Build a judge from a config mapping like {provider: ollama, model: ...}."""

    if not isinstance(spec, dict):
        raise ValueError(f"judge must be a mapping, got {spec!r}")

    options = dict(spec)
    provider = options.pop("provider", None)

    if provider not in JUDGES:
        raise ValueError(
            f"judge provider must be one of: {', '.join(JUDGES)} "
            f"(got {provider!r})"
        )

    if not options.get("model"):
        raise ValueError("judge 'model' is required")

    try:
        return JUDGES[provider](**options)
    except TypeError as error:
        raise ValueError(f"invalid options for judge '{provider}': {error}")


__all__ = [
    "Grade",
    "Judge",
    "JudgeError",
    "parse_grade",
    "HuggingFaceJudge",
    "OllamaJudge",
    "JUDGES",
    "build_judge",
]
