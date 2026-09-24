from ai_evaluator import (
    Check,
    CheckResult,
    FunctionTarget,
    Runner,
    TestCase,
)


class EqualsExpected(Check):

    name = "equals_expected"

    def evaluate(self, test_case, result):
        passed = result.output == test_case.expected
        return CheckResult(self.name, float(passed), passed)


class Broken(Check):

    name = "broken"

    def evaluate(self, test_case, result):
        raise RuntimeError("boom")


def upper(text):
    if text == "crash":
        raise ValueError("bad input")
    return text.upper()


def test_runs_every_case_and_summarises():

    runner = Runner(FunctionTarget(upper), [EqualsExpected()])

    report = runner.run([
        TestCase(id="ok", input="a", expected="A"),
        TestCase(id="wrong", input="b", expected="X"),
    ])

    assert [case.passed for case in report.cases] == [True, False]
    assert report.total == 2
    assert report.passed == 1
    assert report.pass_rate == 0.5
    assert report.finished_at >= report.started_at


def test_target_error_is_recorded_and_run_continues():

    runner = Runner(FunctionTarget(upper), [EqualsExpected()])

    report = runner.run([
        TestCase(id="crash", input="crash"),
        TestCase(id="ok", input="a", expected="A"),
    ])

    crashed, ok = report.cases

    assert crashed.error == "ValueError: bad input"
    assert crashed.execution is None
    assert crashed.checks == []
    assert not crashed.passed
    assert ok.passed


def test_check_error_fails_only_that_check():

    runner = Runner(FunctionTarget(upper), [Broken(), EqualsExpected()])

    case = runner.run([TestCase(id="t1", input="a", expected="A")]).cases[0]

    broken, equals = case.checks

    assert broken.name == "broken"
    assert not broken.passed
    assert "RuntimeError: boom" in broken.reason
    assert equals.passed
    assert not case.passed


def test_empty_run():

    report = Runner(FunctionTarget(upper), []).run([])

    assert report.total == 0
    assert report.pass_rate == 0.0
