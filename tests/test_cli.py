import io
import sys

import pytest
from click.testing import CliRunner

from conftest import make_exe, snapshot
from tzar_widescreen import __version__, cli, install


def run(*args, input=None):
    return CliRunner().invoke(cli.cli, [str(a) for a in args], input=input)


def width_of(game):
    return install.status(game).width


def test_version():
    result = run("--version")
    assert result.exit_code == 0 and __version__ in result.output


def test_help_lists_the_commands():
    result = run("--help")
    assert result.exit_code == 0
    for command in ("install", "uninstall", "status"):
        assert command in result.output


def test_status(game):
    result = run("status", "--game-dir", game)
    assert result.exit_code == 0
    assert "Mod: not installed" in result.output and "1024x768, 0 of" in result.output


def test_install_and_uninstall_with_options(game):
    original = snapshot(game)
    result = run("install", "--width", 1368, "--game-dir", game, "--yes")
    assert result.exit_code == 0, result.output
    assert width_of(game) == 1368
    result = run("uninstall", "--game-dir", game, "--yes")
    assert result.exit_code == 0, result.output
    assert snapshot(game) == original


def test_options_before_the_command(game):
    assert run("--game-dir", game, "--yes", "install", "--width", 2198).exit_code == 0
    assert width_of(game) == 2198


def test_width_alone_installs(game):
    assert run("--width", 1032, "--game-dir", game, "--yes").exit_code == 0
    assert width_of(game) == 1032


def test_yes_without_width_matches_the_screen(game):
    assert run("install", "--game-dir", game, "--yes").exit_code == 0
    assert width_of(game) == 1832  # the 3440x1440 test screen


@pytest.mark.parametrize("width", [1000, 2200, "wide"])
def test_wrong_width(game, width):
    result = run("install", "--width", width, "--game-dir", game, "--yes")
    assert result.exit_code == 2
    assert "--width" in result.output
    assert not (game / install.BACKUP_DIR).exists()


def test_interactive_install_with_enter(game):
    result = run("--game-dir", game, input="\n\n")
    assert result.exit_code == 0, result.output
    assert "1832x768 (matches your screen: 21:9, ultrawide)" in result.output
    assert width_of(game) == 1832


def test_interactive_change_to_a_preset_and_a_custom_width(game):
    run("install", "--width", 1832, "--game-dir", game, "--yes")
    assert run("--game-dir", game, input="1\n3\n").exit_code == 0  # change, 16:9
    assert width_of(game) == 1368
    assert run("--game-dir", game, input="1\n4\n1500\n").exit_code == 0  # change, another width
    assert width_of(game) == 1500


def test_interactive_remove(game):
    original = snapshot(game)
    run("install", "--game-dir", game, "--yes")
    assert run("--game-dir", game, input="2\n").exit_code == 0
    assert snapshot(game) == original


def test_interactive_nothing_is_the_default(game):
    run("install", "--width", 1368, "--game-dir", game, "--yes")
    assert run("--game-dir", game, input="\n").exit_code == 0
    assert width_of(game) == 1368


def test_declining_changes_nothing(game):
    original = snapshot(game)
    assert run("install", "--width", 1368, "--game-dir", game, input="n\n").exit_code == 0
    assert snapshot(game) == original


def test_after_a_steam_update_it_offers_to_apply_again(game):
    run("install", "--width", 1368, "--game-dir", game, "--yes")
    (game / install.EXE).write_bytes(make_exe())
    result = run("--game-dir", game, input="1\n")
    assert "put back" in result.output
    assert install.status(game).exe.width == 1368


def test_linux_asks_to_start_the_game_once_then_finishes(game, prefix):
    reg = prefix.read_bytes()
    prefix.unlink()
    result = run("install", "--width", 1368, "--game-dir", game, "--yes")
    assert result.exit_code == 0
    assert "Start Tzar once from Steam" in result.output
    prefix.write_bytes(reg)
    result = run("--game-dir", game, input="1\n")
    assert "doesn't have its setting yet" in result.output
    assert "Done" in result.output
    assert not install.status(game).proton_missing


def test_linux_install_says_done_with_a_prefix(game, prefix):
    result = run("install", "--width", 1368, "--game-dir", game, "--yes")
    assert "Done: the game runs at 1368x768" in result.output
    assert "Launch Options" not in result.output


def test_main_reports_problems_and_exits_with_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tzar-widescreen", "status", "--game-dir", str(tmp_path)])
    with pytest.raises(SystemExit) as exit_:
        cli.main()
    assert exit_.value.code == 1
    assert "Can't continue" in capsys.readouterr().out


def test_main_stops_cleanly_on_ctrl_d(game, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tzar-widescreen", "--game-dir", str(game)])
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))  # Ctrl-D at the first question
    with pytest.raises(SystemExit) as exit_:
        cli.main()
    assert exit_.value.code == 1
    assert "Stopped" in capsys.readouterr().out
