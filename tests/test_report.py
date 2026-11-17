import hashlib
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from conftest import IMAGE_BASE, STEAM_EXE

from tzar_widescreen import __version__, cli, exe_patch, report


def fields(url: str) -> dict[str, str]:
    assert url.startswith(f"{report.ISSUES}/new?")
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def unknown_build(game: Path) -> None:
    """Another build of the game: different code where the first patch goes."""
    exe = game / STEAM_EXE
    data = bytearray(exe.read_bytes())
    offset = exe_patch.SIZE_PATCHES[0].va - IMAGE_BASE
    data[offset:offset + 9] = bytes.fromhex("4325ffff000081c7ac")  # what #65's exe has there
    exe.write_bytes(data)


def run_main(monkeypatch, capsys, *args) -> tuple[int, str]:
    monkeypatch.setattr(sys, "argv", ["tzar-widescreen", *map(str, args)])
    with pytest.raises(SystemExit) as exit_:
        cli.main()
    return exit_.value.code, capsys.readouterr().out


def link_in(output: str) -> str:
    return next(line for line in output.splitlines() if line.startswith(f"{report.ISSUES}/new?"))


def test_scrub_takes_the_user_name_out_of_paths(monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: Path("/home/someone"))
    assert report.scrub("/home/someone/.steam/steam/steamapps") == "~/.steam/steam/steamapps"
    assert report.scrub(r"C:\Users\rekram\Desktop\mod.exe") == r"C:\Users\<user>\Desktop\mod.exe"
    assert report.scrub("/home/other/Games/Tzar") == "~/Games/Tzar"
    assert report.scrub(r"C:\Program Files (x86)\Infinite Loop\Tzar") == r"C:\Program Files (x86)\Infinite Loop\Tzar"


def test_the_issue_tells_the_build_apart(game):
    report.game_dir = game
    data = (game / STEAM_EXE).read_bytes()
    issue = fields(report.issue_url("this version of the game isn't supported yet (unexpected bytes)"))
    assert issue["title"] == "Installer: this version of the game isn't supported yet (unexpected bytes)"
    body = issue["body"]
    assert body.startswith("## Impact") and "## Details" in body
    assert f"Mod: {__version__} (from source)" in body
    assert f"Game folder: {report.scrub(str(game))}" in body  # on Windows, the temp folder is in the home folder
    assert f"{STEAM_EXE}, {len(data):,} bytes, SHA-256 {hashlib.sha256(data).hexdigest()}, PE timestamp 0" in body


def test_without_a_game_folder_it_still_reports():
    body = fields(report.issue_url("couldn't find the game"))["body"]
    assert "couldn't find the game" in body and "Game folder" not in body


def test_a_long_traceback_keeps_its_end_and_fits():
    trace = "Traceback (most recent call last):\n" + "".join(
        f'  File "/somewhere/module{i}.py", line {i}, in function{i}\n    do_something({i})\n' for i in range(500))
    trace += "RuntimeError: the actual problem\n"
    url = report.issue_url("RuntimeError: the actual problem", trace)
    assert len(url) <= report.MAX_URL
    body = fields(url)["body"]
    assert "RuntimeError: the actual problem\n```" in body and "module499" in body and "module0.py" not in body
    assert "Traceback (most recent call last):\n  ...\n  File " in body  # whole frames cut, not half of one


def test_an_unknown_build_gets_a_filled_in_link(game, monkeypatch, capsys):
    unknown_build(game)
    code, output = run_main(monkeypatch, capsys, "status", "--game-dir", game)
    assert code == 1
    assert "Can't continue: this version of the game isn't supported yet" in output
    body = fields(link_in(output))["body"]
    assert "unexpected bytes at 0x43bb31: 43 25 ff ff 00 00 81 c7 ac" in body
    assert "SHA-256" in body


def test_every_failure_gets_the_link(tmp_path, monkeypatch, capsys):
    code, output = run_main(monkeypatch, capsys, "uninstall", "--game-dir", tmp_path)
    assert code == 1 and "doesn't look like the Tzar folder" in output
    assert "doesn't look like the Tzar folder" in fields(link_in(output))["body"]


def test_a_crash_shows_the_traceback_and_the_link_and_waits(game, monkeypatch, capsys):
    def crash(_):
        raise RuntimeError("something the mod didn't expect")
    monkeypatch.setattr(cli.install, "status", crash)
    monkeypatch.setattr(cli.game, "find", lambda: [game])
    monkeypatch.setattr(sys, "platform", "win32")  # a double-click start on Windows
    paused = []
    monkeypatch.setattr(cli.click, "pause", lambda info: paused.append(info))
    code, output = run_main(monkeypatch, capsys)
    assert code == 1
    assert "Traceback (most recent call last)" in output and "a bug in it" in output
    issue = fields(link_in(output))
    assert issue["title"] == "Installer: RuntimeError: something the mod didn't expect"
    assert "<summary>Traceback</summary>" in issue["body"] and "raise RuntimeError" in issue["body"]
    assert paused, "the window must stay open"


def test_usage_errors_get_no_link(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tzar-widescreen", "install", "--width", "5"])
    with pytest.raises(SystemExit) as exit_:
        cli.main()
    assert exit_.value.code == 2
    assert report.ISSUES not in capsys.readouterr().out
