import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ai_evaluator.judges import (
    HuggingFaceJudge,
    Judge,
    JudgeError,
    OllamaJudge,
    build_judge,
    parse_grade,
)


# ------------------------------------------------------------- parse_grade


@pytest.mark.parametrize(
    "reply, score, reason",
    [
        ('{"score": 8, "reason": "Good."}', 0.8, "Good."),
        ('Sure!\n```json\n{"reason": "Wrong", "score": 0}\n```', 0.0, "Wrong"),
        ('{"score": "10", "reason": " ok "}', 1.0, "ok"),
        ('{"score": 7}', 0.7, ""),
    ],
)
def test_parse_grade_accepts(reply, score, reason):

    grade = parse_grade(reply)

    assert grade.score == pytest.approx(score)
    assert grade.reason == reason


@pytest.mark.parametrize(
    "reply, message",
    [
        ("I think it's a 7", "no JSON object"),
        ("{score: 7}", "invalid JSON"),
        ('{"reason": "no score"}', "missing or non-numeric score"),
        ('{"score": "high"}', "missing or non-numeric score"),
        ('{"score": 11}', "outside 0-10"),
        ('{"score": -1}', "outside 0-10"),
    ],
)
def test_parse_grade_rejects(reply, message):

    with pytest.raises(ValueError, match=message):
        parse_grade(reply)


# ------------------------------------------------------------------- grade


class ScriptedJudge(Judge):

    name = "scripted"

    def __init__(self, replies, max_retries=2):
        super().__init__("test-model", max_retries)
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages):
        self.calls += 1
        return self.replies.pop(0)


def test_grade_retries_until_valid():

    judge = ScriptedJudge(["nonsense", '{"score": 11}', '{"score": 9, "reason": "ok"}'])

    assert judge.grade([]).score == pytest.approx(0.9)
    assert judge.calls == 3


def test_grade_gives_up_after_retries():

    judge = ScriptedJudge(["bad"] * 5, max_retries=1)

    with pytest.raises(JudgeError, match="no valid grade after 2 tries"):
        judge.grade([])

    assert judge.calls == 2


# ------------------------------------------------------------- build_judge


def test_build_judge():

    judge = build_judge({"provider": "ollama", "model": "qwen2.5:7b", "timeout_s": 30})

    assert isinstance(judge, OllamaJudge)
    assert judge.model == "qwen2.5:7b"
    assert judge.timeout_s == 30


@pytest.mark.parametrize(
    "spec, message",
    [
        ("ollama", "must be a mapping"),
        ({"model": "x"}, "provider must be one of"),
        ({"provider": "openai", "model": "x"}, "provider must be one of"),
        ({"provider": "ollama"}, "'model' is required"),
        ({"provider": "ollama", "model": "x", "temp": 1}, "invalid options"),
    ],
)
def test_build_judge_errors(spec, message):

    with pytest.raises(ValueError, match=message):
        build_judge(spec)


# ------------------------------------------------- backends vs. fake server


class FakeServer:
    """Answers GET/POST with the next canned response and records requests."""

    def __init__(self):
        self.responses = []
        self.requests = []

        server = self

        class Handler(BaseHTTPRequestHandler):

            def handle_request(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                server.requests.append({
                    "method": self.command,
                    "path": self.path,
                    "headers": dict(self.headers),
                    "body": json.loads(body) if body else None,
                })
                status, payload = server.responses.pop(0)
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = handle_request

            def log_message(self, *args):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(
            target=self.httpd.serve_forever, args=(0.01,), daemon=True
        ).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def server():
    fake = FakeServer()
    yield fake
    fake.close()


MESSAGES = [{"role": "user", "content": "grade this"}]


def test_ollama_chat_request(server):

    server.responses.append((200, {"message": {"content": '{"score": 6, "reason": "meh"}'}}))

    grade = OllamaJudge("qwen2.5:7b", url=server.url).grade(MESSAGES)

    assert grade.score == pytest.approx(0.6)

    request = server.requests[0]
    assert request["path"] == "/api/chat"
    assert request["body"]["model"] == "qwen2.5:7b"
    assert request["body"]["messages"] == MESSAGES
    assert request["body"]["stream"] is False
    assert request["body"]["options"] == {"temperature": 0}
    assert request["body"]["format"]["required"] == ["score", "reason"]


def test_ollama_ready_when_model_pulled(server):

    server.responses.append((200, {"models": [{"name": "qwen2.5:7b"}]}))

    OllamaJudge("qwen2.5:7b", url=server.url).check_ready()

    assert server.requests[0]["path"] == "/api/tags"


def test_ollama_latest_tag_counts_as_pulled(server):

    server.responses.append((200, {"models": [{"name": "llama3.1:latest"}]}))

    OllamaJudge("llama3.1", url=server.url).check_ready()


def test_ollama_missing_model_says_how_to_pull(server):

    server.responses.append((200, {"models": [{"name": "other:1b"}]}))

    with pytest.raises(JudgeError, match="ollama pull qwen2.5:7b"):
        OllamaJudge("qwen2.5:7b", url=server.url).check_ready()


def test_ollama_not_running():

    # Nothing listens on port 9 (discard) on a normal machine.
    with pytest.raises(JudgeError, match="Can't reach Ollama.*ollama serve"):
        OllamaJudge("x", url="http://127.0.0.1:9").check_ready()


def test_ollama_http_error(server):

    server.responses.append((500, {"error": "model crashed"}))

    with pytest.raises(JudgeError, match="HTTP 500.*model crashed"):
        OllamaJudge("x", url=server.url).chat(MESSAGES)


def test_huggingface_chat_request(server, monkeypatch):

    monkeypatch.setenv("HF_TOKEN", "hf_secret")
    server.responses.append(
        (200, {"choices": [{"message": {"content": '{"score": 10, "reason": "ok"}'}}]})
    )

    judge = HuggingFaceJudge("Qwen/Qwen2.5-7B-Instruct", url=server.url)

    assert judge.grade(MESSAGES).score == 1.0

    request = server.requests[0]
    assert request["path"] == "/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer hf_secret"
    assert request["body"]["model"] == "Qwen/Qwen2.5-7B-Instruct"
    assert request["body"]["temperature"] == 0


def test_huggingface_needs_token(monkeypatch):

    monkeypatch.delenv("HF_TOKEN", raising=False)

    with pytest.raises(JudgeError, match="Set the HF_TOKEN environment variable"):
        HuggingFaceJudge("x").check_ready()
