import json
import textwrap

from ai_evaluator.cli import main


def test_runs_quickstart_example_and_saves_report(capsys, tmp_path):

    exit_code = main([
        "run", "examples/quickstart/eval.yaml", "-o", str(tmp_path)
    ])

    output = capsys.readouterr().out
    (saved,) = tmp_path.glob("*.json")

    assert exit_code == 0
    assert "Running 4 test cases" in output
    assert "4/4 passed (100%)" in output
    assert f"Saved run to {saved}" in output
    assert json.loads(saved.read_text())["summary"]["total"] == 4


def test_failures_exit_with_1(capsys, tmp_path):

    (tmp_path / "cases.yaml").write_text(textwrap.dedent("""
        - id: wrong
          input: What is the capital of Sweden?
          expected: Oslo
          checks: [contains_expected]
    """))
    (tmp_path / "eval.yaml").write_text(
        "target: examples.quickstart.bot:ask\ndataset: cases.yaml\n"
    )

    exit_code = main(["run", str(tmp_path / "eval.yaml"), "--no-save"])

    assert exit_code == 1
    assert "Missing from output: ['Oslo']" in capsys.readouterr().out
    assert not list(tmp_path.glob("*.json"))


def test_config_error_exits_with_2(capsys, tmp_path):

    exit_code = main(["run", str(tmp_path / "missing.yaml")])

    assert exit_code == 2
    assert "Config error: File not found" in capsys.readouterr().err
