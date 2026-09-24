import json
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class JudgeError(Exception):
    """The judge could not be reached or kept giving unusable answers."""


@dataclass
class Grade:
    score: float        # 0 to 1
    reason: str


# Small models follow a 0-10 whole number scale more reliably than 0-1.
MAX_SCORE = 10

GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": MAX_SCORE},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
}


class Judge(ABC):
    """An LLM that grades answers. Backends only implement chat()."""

    name: str = "judge"

    def __init__(self, model: str, max_retries: int = 2):
        self.model = model
        self.max_retries = max_retries

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        """Send chat messages and return the reply text."""

    def check_ready(self) -> None:
        """Raise JudgeError with a helpful message if the judge can't be used."""

    def grade(self, messages: list[dict[str, str]]) -> Grade:
        """Ask for a grade, retrying when the reply isn't valid."""

        problem = ""

        for _ in range(self.max_retries + 1):

            reply = self.chat(messages)

            try:
                return parse_grade(reply)
            except ValueError as error:
                problem = str(error)

        raise JudgeError(
            f"{self.name} gave no valid grade after "
            f"{self.max_retries + 1} tries: {problem}"
        )


def parse_grade(reply: str) -> Grade:
    """Read {"score": 0-10, "reason": "..."} from a reply, allowing extra text."""

    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in reply: {reply[:200]!r}")

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        raise ValueError(f"invalid JSON in reply: {reply[:200]!r}")

    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object, got {data!r}")

    try:
        score = float(data["score"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"missing or non-numeric score: {data!r}")

    if not 0 <= score <= MAX_SCORE:
        raise ValueError(f"score {score} is outside 0-{MAX_SCORE}")

    return Grade(
        score=score / MAX_SCORE,
        reason=str(data.get("reason", "")).strip()
    )


def post_json(
    url: str,
    body: dict[str, Any],
    timeout_s: float,
    headers: dict[str, str] | None = None
) -> Any:
    """POST JSON and return the decoded response. Raises JudgeError."""

    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST"
    )

    return send(request, timeout_s)


def get_json(
    url: str,
    timeout_s: float,
    headers: dict[str, str] | None = None
) -> Any:

    return send(urllib.request.Request(url, headers=headers or {}), timeout_s)


def send(request: urllib.request.Request, timeout_s: float) -> Any:

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:300]
        raise JudgeError(f"HTTP {error.code} from {request.full_url}: {detail}")
    except urllib.error.URLError as error:
        raise JudgeError(f"could not reach {request.full_url}: {error.reason}")
    except TimeoutError:
        raise JudgeError(f"{request.full_url} timed out after {timeout_s:g} s")
    except json.JSONDecodeError:
        raise JudgeError(f"{request.full_url} did not return JSON")
