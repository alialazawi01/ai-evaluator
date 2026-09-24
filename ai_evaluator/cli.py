import argparse
import sys

from ai_evaluator.config import ConfigError, load_config
from ai_evaluator.core.runner import Runner
from ai_evaluator.judges import JudgeError
from ai_evaluator.report import print_report, save_report


# Exit codes, so scripts and CI can tell the outcomes apart.
EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_CONFIG_ERROR = 2


def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(
        prog="ai-eval",
        description="Test and score AI systems."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser("run", help="Run an eval config")
    run_parser.add_argument("config", help="Path to the eval config file")
    run_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show every check, not only failed ones"
    )
    run_parser.add_argument(
        "-o", "--output-dir",
        default="runs",
        help="Folder to save the run report in (default: runs)"
    )
    run_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save the run report"
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        return run(args)

    return EXIT_PASSED


def run(args: argparse.Namespace) -> int:

    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"Config error: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    if config.judge and config.uses_judge:
        try:
            config.judge.check_ready()
        except JudgeError as error:
            print(f"Judge error: {error}", file=sys.stderr)
            return EXIT_CONFIG_ERROR

    print(
        f"Running {len(config.test_cases)} test cases "
        f"against {config.target.name}"
        + (
            f" (judge: {config.judge.name} {config.judge.model})"
            if config.judge and config.uses_judge else ""
        )
    )

    report = Runner(config.target, config.checks).run(
        config.test_cases,
        on_case_done=show_progress if sys.stderr.isatty() else None
    )

    if sys.stderr.isatty():
        # Clear the progress line.
        print("\r\033[K", end="", file=sys.stderr)

    print_report(report, verbose=args.verbose)

    if not args.no_save:
        path = save_report(report, args.output_dir, config_path=args.config)
        print(f"\nSaved run to {path}")

    return EXIT_PASSED if report.passed == report.total else EXIT_FAILED


def show_progress(number: int, total: int, case) -> None:
    print(
        f"\r\033[K  {number}/{total}  {case.test_case.id}",
        end="",
        file=sys.stderr,
        flush=True
    )


if __name__ == "__main__":
    sys.exit(main())
