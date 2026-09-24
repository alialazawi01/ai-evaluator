from .base import GRADE_SCHEMA, Judge, JudgeError, get_json, post_json


class OllamaJudge(Judge):
    """A model running locally in Ollama. Free, no rate limits."""

    name = "ollama"

    def __init__(
        self,
        model: str,
        url: str = "http://localhost:11434",
        timeout_s: float = 120,
        max_retries: int = 2
    ):
        super().__init__(model, max_retries)
        self.url = url.rstrip("/")
        self.timeout_s = timeout_s

    def check_ready(self) -> None:

        try:
            data = get_json(f"{self.url}/api/tags", timeout_s=5)
        except JudgeError:
            raise JudgeError(
                f"Can't reach Ollama at {self.url}. "
                "Is it running? Start it with: ollama serve"
            )

        names = {m.get("name") for m in data.get("models", [])}
        # "qwen2.5" and "qwen2.5:latest" are the same model.
        if self.model not in names and f"{self.model}:latest" not in names:
            raise JudgeError(
                f"Ollama model '{self.model}' is not downloaded. "
                f"Run: ollama pull {self.model}"
            )

    def chat(self, messages: list[dict[str, str]]) -> str:

        data = post_json(
            f"{self.url}/api/chat",
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                # Ollama constrains the reply to this JSON schema.
                "format": GRADE_SCHEMA,
                "options": {"temperature": 0},
            },
            timeout_s=self.timeout_s
        )

        try:
            return data["message"]["content"]
        except (KeyError, TypeError):
            raise JudgeError(f"Unexpected reply from Ollama: {str(data)[:300]}")
