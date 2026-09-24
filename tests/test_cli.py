from ai_evaluator.cli import main


def test_runs_quickstart_example(capsys):

    exit_code = main(["run", "examples/quickstart/eval.yaml"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Running 4 test cases" in output
    assert "Passed 4/4 (100%)" in output


def test_config_error_exits_with_2(capsys, tmp_path):

    exit_code = main(["run", str(tmp_path / "missing.yaml")])

    assert exit_code == 2
    assert "Config error: File not found" in capsys.readouterr().err
