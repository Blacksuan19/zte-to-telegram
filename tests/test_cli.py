from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cli import cli


def test_cli_runs_once_with_required_options():
    runner = CliRunner()
    with (
        patch("cli.ZteConnection") as conn_cls,
        patch("cli.TelegramClient") as tg_cls,
        patch("cli.Forwarder") as fwd_cls,
    ):
        fwd = MagicMock()
        fwd_cls.return_value = fwd
        result = runner.invoke(cli, ["--password", "pw", "--bot", "B", "--chat", "C"])

    assert result.exit_code == 0, result.output
    conn_cls.assert_called_once()
    tg_cls.assert_called_once()
    fwd.run_once.assert_called_once()
    fwd.run_loop.assert_not_called()


def test_cli_loop_mode_calls_run_loop():
    runner = CliRunner()
    with (
        patch("cli.ZteConnection"),
        patch("cli.TelegramClient"),
        patch("cli.Forwarder") as fwd_cls,
    ):
        fwd = MagicMock()
        fwd_cls.return_value = fwd
        result = runner.invoke(cli, ["--password", "pw", "--bot", "B", "--chat", "C", "--loop", "--interval", "5"])

    assert result.exit_code == 0, result.output
    fwd.run_loop.assert_called_once_with(5)


def test_cli_requires_password():
    runner = CliRunner()
    result = runner.invoke(cli, ["--bot", "B", "--chat", "C"])
    assert result.exit_code != 0
