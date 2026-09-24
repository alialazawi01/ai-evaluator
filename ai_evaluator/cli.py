import argparse
import sys

from ai_evaluator.config import ConfigError, load_config
from ai_evaluator.core.runner import Runner
from ai_evaluator.report import print_report


def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(
        prog="ai-eval",
        description="Test and score AI systems."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser("run", help="Run an eval config")
    run_parser.add_argument("config", help="Path to the eval config file")

    args = parser.parse_args(argv)

    if args.command == "run":
        return run(args.config)

    return 0


def run(config_path: str) -> int:

    try:
        config = load_config(config_path)
    except ConfigError as error:
        print(f"Config error: {error}", file=sys.stderr)
        return 2

    print(
        f"Running {len(config.test_cases)} test cases "
        f"against {config.target.name}"
    )

    report = Runner(config.target, config.checks).run(config.test_cases)

    print_report(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
