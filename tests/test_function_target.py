import pytest

from ai_evaluator import FunctionTarget, TestCase


def echo(text):
    return text


def test_plain_return_value_becomes_output():

    result = FunctionTarget(echo).run(TestCase(id="t1", input="hello"))

    assert result.output == "hello"
    assert result.latency_ms >= 0
    assert result.metadata == {}


def test_dict_with_output_fills_fields():

    def rag_bot(question):
        return {
            "output": "Stockholm",
            "retrieved_docs": ["sweden.md"],
            "input_tokens": 12,
            "source": "kb",
        }

    result = FunctionTarget(rag_bot).run(TestCase(id="t1", input="?"))

    assert result.output == "Stockholm"
    assert result.retrieved_docs == ["sweden.md"]
    assert result.input_tokens == 12
    assert result.metadata == {"source": "kb"}


def test_dict_without_output_key_is_the_output():

    def classifier(text):
        return {"spam": 0.9, "ham": 0.1}

    result = FunctionTarget(classifier).run(TestCase(id="t1", input="x"))

    assert result.output == {"spam": 0.9, "ham": 0.1}


def test_from_path_loads_function():

    target = FunctionTarget.from_path("tests.test_function_target:echo")

    assert target.name == "tests.test_function_target:echo"
    assert target.run(TestCase(id="t1", input="hi")).output == "hi"


@pytest.mark.parametrize(
    "path",
    ["no_colon", ":echo", "tests.test_function_target:", "tests.test_function_target:pytest"]
)
def test_from_path_rejects_bad_paths(path):

    with pytest.raises(ValueError):
        FunctionTarget.from_path(path)
