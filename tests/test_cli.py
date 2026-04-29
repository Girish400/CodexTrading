from gstrading.cli import parse_args, parse_config


def test_parse_config_normalizes_symbols_and_generic_ticks() -> None:
    args = parse_args(
        [
            "--symbols",
            "aapl",
            "msft",
            "--generic-tick",
            "233",
            "236",
            "",
            "--duration",
            "30",
        ]
    )

    config = parse_config(args)

    assert config.symbols == {"AAPL", "MSFT"}
    assert config.generic_ticks == {"233", "236"}
    assert config.duration_seconds == 30
    assert args.command == "run"


def test_parse_args_supports_memory_subcommand() -> None:
    args = parse_args(
        [
            "memory",
            "start",
            "--project",
            "GSTrading",
            "--title",
            "Sprint handoff",
            "--objective",
            "Capture verified tool outputs",
        ]
    )

    assert args.command == "memory"
    assert args.memory_command == "start"
    assert args.project == "GSTrading"


def test_parse_args_supports_dev_subcommand() -> None:
    args = parse_args(
        [
            "dev",
            "test",
            "--project",
            "GSTrading",
            "--close-session",
            "--",
            "tests/test_cli.py",
        ]
    )

    assert args.command == "dev"
    assert args.dev_command == "test"
    assert args.project == "GSTrading"
    assert args.close_session is True
