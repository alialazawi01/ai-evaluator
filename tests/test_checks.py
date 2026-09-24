import pytest

from ai_evaluator import ExecutionResult, TestCase
from ai_evaluator.checks import (
    ContainsExpectedCheck,
    ExactMatchCheck,
    LatencyCheck,
)


def run(check, output, expected=None, latency_ms=10.0):
    case = TestCase(id="t1", input="q", expected=expected)
    return check.evaluate(case, ExecutionResult(output, latency_ms))


class TestExactMatch:

    def test_matches_ignoring_surrounding_whitespace(self):
        assert run(ExactMatchCheck(), " Paris\n", "Paris").passed

    def test_case_sensitive_by_default(self):
        assert not run(ExactMatchCheck(), "paris", "Paris").passed
        assert run(ExactMatchCheck(case_sensitive=False), "paris", "Paris").passed

    def test_non_string_values(self):
        assert run(ExactMatchCheck(), 425, 425).passed
        assert not run(ExactMatchCheck(), "425", 425).passed

    def test_mismatch_reason_shows_both_values(self):
        result = run(ExactMatchCheck(), "Oslo", "Paris")
        assert result.score == 0.0
        assert "'Paris'" in result.reason and "'Oslo'" in result.reason

    def test_missing_expected_fails_instead_of_crashing(self):
        result = run(ExactMatchCheck(), "Paris", None)
        assert not result.passed
        assert "no expected value" in result.reason


class TestContainsExpected:

    def test_finds_text_case_insensitive_by_default(self):
        assert run(ContainsExpectedCheck(), "The capital is STOCKHOLM.", "Stockholm").passed

    def test_case_sensitive_option(self):
        check = ContainsExpectedCheck(case_sensitive=True)
        assert not run(check, "stockholm", "Stockholm").passed

    def test_list_scores_share_found(self):
        result = run(ContainsExpectedCheck(), "Oslo and Stockholm", ["Stockholm", "Oslo", "Helsinki"])
        assert not result.passed
        assert result.score == pytest.approx(2 / 3)
        assert "Helsinki" in result.reason

    def test_non_string_output_is_converted(self):
        assert run(ContainsExpectedCheck(), 425, "425").passed

    @pytest.mark.parametrize("expected", [None, []])
    def test_missing_expected_fails(self, expected):
        assert not run(ContainsExpectedCheck(), "anything", expected).passed


class TestLatency:

    def test_within_limit_passes_with_full_score(self):
        result = run(LatencyCheck(max_ms=100), "x", latency_ms=50)
        assert result.passed and result.score == 1.0

    def test_over_limit_fails_with_lower_score(self):
        result = run(LatencyCheck(max_ms=100), "x", latency_ms=400)
        assert not result.passed
        assert result.score == 0.25

    def test_rejects_non_positive_limit(self):
        with pytest.raises(ValueError):
            LatencyCheck(max_ms=0)
