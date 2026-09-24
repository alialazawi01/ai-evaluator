import pytest

from ai_evaluator import Check, CheckResult
from ai_evaluator.checks import (
    CHECKS,
    ContainsExpectedCheck,
    ExactMatchCheck,
    LatencyCheck,
    build_check,
    build_checks,
    register_check,
)


def test_builds_check_from_name():
    assert isinstance(build_check("exact_match"), ExactMatchCheck)


def test_builds_check_with_options():
    check = build_check({"latency": {"max_ms": 3000}})
    assert isinstance(check, LatencyCheck)
    assert check.max_ms == 3000


def test_empty_options_are_allowed():
    # YAML "- contains_expected:" with nothing after it gives None.
    assert isinstance(build_check({"contains_expected": None}), ContainsExpectedCheck)


def test_builds_list():
    checks = build_checks(["exact_match", {"latency": {"max_ms": 1}}])
    assert [c.name for c in checks] == ["exact_match", "latency"]


@pytest.mark.parametrize(
    "spec, message",
    [
        ("nope", "Unknown check 'nope'"),
        ({"latency": {"max_seconds": 3}}, "Invalid options for check 'latency'"),
        ({"latency": 3000}, "must be a mapping"),
        ({"a": {}, "b": {}}, "Invalid check"),
        (42, "Invalid check"),
    ],
)
def test_bad_specs_give_clear_errors(spec, message):
    with pytest.raises(ValueError, match=message):
        build_check(spec)


def test_register_custom_check():

    @register_check
    class AlwaysPass(Check):
        name = "always_pass"

        def evaluate(self, test_case, result):
            return CheckResult(self.name, 1.0, True)

    try:
        assert isinstance(build_check("always_pass"), AlwaysPass)
    finally:
        del CHECKS["always_pass"]
