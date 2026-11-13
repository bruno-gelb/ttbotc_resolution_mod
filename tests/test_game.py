from conftest import GOG_EXE, STEAM_EXE, heroic_config
from tzar_widescreen import heroic
from tzar_widescreen.game import exe_name, find, is_game_dir


def test_on_steam_the_game_is_tzar_underscore_not_the_launcher(game):
    assert exe_name(game) == STEAM_EXE


def test_on_gog_the_game_is_tzar_exe(gog_game):
    assert exe_name(gog_game) == GOG_EXE


def test_steams_launcher_alone_isnt_the_game(game):
    (game / STEAM_EXE).unlink()
    assert exe_name(game) is None and not is_game_dir(game)


def test_heroic_installs_are_found(gog_game, tmp_path, monkeypatch):
    config = tmp_path / "heroic"
    monkeypatch.setattr(heroic, "CONFIG_DIRS", [config])
    heroic_config(config, gog_game, tmp_path / "prefix")
    monkeypatch.chdir(tmp_path)
    assert gog_game.resolve() in find()
    assert heroic.find(gog_game).wine_prefix == tmp_path / "prefix"


def test_other_heroic_games_and_broken_settings_are_ignored(tmp_path, monkeypatch):
    good, broken = tmp_path / "good", tmp_path / "broken"
    (good / "gog_store").mkdir(parents=True)
    (good / "gog_store" / "installed.json").write_text('{"installed": [{"appName": "1", "install_path": "/x"}]}')
    (broken / "gog_store").mkdir(parents=True)
    (broken / "gog_store" / "installed.json").write_text("{not json")
    monkeypatch.setattr(heroic, "CONFIG_DIRS", [good, broken, tmp_path / "missing"])
    assert heroic.installs() == []
