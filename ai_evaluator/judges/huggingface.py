import os

from .base import Judge, JudgeError, post_json


class HuggingFaceJudge(Judge):
    """
    A model on Hugging Face Inference Providers. Needs a free access token
    in the HF_TOKEN environment variable. The free tier is rate limited.
    """

    name = "huggingface"

    def __init__(
        self,
        model: str,
        url: str = "https://router.huggingface.co/v1",
        token_env: str = "HF_TOKEN",
        timeout_s: float = 60,
        max_retries: int = 2
    ):
        super().__init__(model, max_retries)
        self.url = url.rstrip("/")
        self.token_env = token_env
        self.timeout_s = timeout_s

    def check_ready(self) -> None:

        if not os.environ.get(self.token_env):
            raise JudgeError(
                f"Set the {self.token_env} environment variable to your "
                "Hugging Face access token "
                "(https://huggingface.co/settings/tokens)"
            )

    def chat(self, messages: list[dict[str, str]]) -> str:

        self.check_ready()

        # OpenAI-compatible chat endpoint.
        data = post_json(
            f"{self.url}/chat/completions",
            {
                "model": self.model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": 300,
            },
            timeout_s=self.timeout_s,
            headers={"Authorization": f"Bearer {os.environ[self.token_env]}"}
        )

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise JudgeError(
                f"Unexpected reply from Hugging Face: {str(data)[:300]}"
            )
