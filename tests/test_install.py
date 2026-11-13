import json

import pytest

from conftest import GOG_EXE, STEAM_EXE, STRINGS_INI, USER_REG, make_exe, make_frame, snapshot
from tzar_widescreen import __version__, exe_patch, frame, ini, install, proton, resolutions
from tzar_widescreen.manifest import FILE, Manifest


def quiet(_line):
    pass


def check_installed(game, width):
    assert exe_patch.inspect((game / STEAM_EXE).read_bytes()).width == width
    layout = ini.read(game / install.LAYOUT_INI)
    assert ini.get_key(layout, "LAYOUT1024L", "view") == f"150,30,{width - 150},738"
    assert frame.size((game / install.FRAME).read_bytes()) == (width, 768)
    ddraw = ini.read(game / "ddraw.ini")
    assert ini.get_key(ddraw, "ddraw", "inject_resolution") == f"{width}x768"
    assert ini.get_key(ddraw, "Tzar_", "adjmouse") == "true"
    assert Manifest.load(game / install.BACKUP_DIR).width == width


def test_install(game):
    original = snapshot(game)
    install.install(game, 1832, log=quiet)
    check_installed(game, 1832)
    tzar_ini = ini.read(game / install.TZAR_INI)
    assert ini.get_key(tzar_ini, "DEFAULTS", "LAYOUT") == "LAYOUT1024L"
    assert ini.get_key(tzar_ini, "VIDEO", "DIRECTXDEVICE") == "0"
    assert (game / "ddraw.dll").read_bytes() == b"not really cnc-ddraw"
    assert (game / "Shaders" / "test.glsl").is_file()
    backup = snapshot(game / install.BACKUP_DIR)
    for rel in install.BACKED_UP:
        assert backup[rel] == original[rel]  # the backup holds the originals
    manifest = Manifest.load(game / install.BACKUP_DIR)
    assert manifest.tzar_ini == {"DEFAULTS/LAYOUT": "LAYOUT800L", "VIDEO/DIRECTXDEVICE": "-1",
                                 "VIDEO/DIRECTDRAW_DEVICESNUMBER": "2"}
    assert manifest.moved_aside == []


def test_changing_the_width_works_from_the_backups(game):
    install.install(game, 1832, log=quiet)
    backup = snapshot(game / install.BACKUP_DIR)
    install.install(game, 1368, log=quiet)
    check_installed(game, 1368)
    after = snapshot(game / install.BACKUP_DIR)
    assert {k: v for k, v in after.items() if k != FILE} == {k: v for k, v in backup.items() if k != FILE}


def test_uninstall_restores_everything(game):
    original = snapshot(game)
    install.install(game, 2198, log=quiet)
    install.uninstall(game, log=quiet)
    assert snapshot(game) == original
    assert not (game / install.BACKUP_DIR).exists()


def test_uninstall_keeps_the_players_own_settings(game):
    install.install(game, 1832, log=quiet)
    path = game / install.TZAR_INI
    ini.write(path, ini.set_key(ini.read(path), "DEFAULTS", "SCROLLSPEED", "5"))  # changed in the game
    install.uninstall(game, log=quiet)
    text = ini.read(path)
    assert ini.get_key(text, "DEFAULTS", "SCROLLSPEED") == "5"
    assert ini.get_key(text, "VIDEO", "DIRECTXDEVICE") == "-1"
    assert ini.get_key(text, "DEFAULTS", "LAYOUT") == "LAYOUT800L"


def test_someone_elses_ddraw_is_kept_and_put_back(game):
    (game / "ddraw.dll").write_bytes(b"another wrapper")
    install.install(game, 1832, log=quiet)
    assert (game / "ddraw.dll").read_bytes() == b"not really cnc-ddraw"
    assert Manifest.load(game / install.BACKUP_DIR).moved_aside == ["ddraw.dll"]
    install.uninstall(game, log=quiet)
    assert (game / "ddraw.dll").read_bytes() == b"another wrapper"


def test_an_exe_patched_by_hand_is_backed_up_as_the_original(game):
    (game / STEAM_EXE).write_bytes(exe_patch.apply(make_exe(), 1832, 768))
    install.install(game, 1832, log=quiet)
    assert (game / install.BACKUP_DIR / STEAM_EXE).read_bytes() == make_exe()


LABEL = f"ttbotc_resolution_mod {__version__}. game Version"


def menu_label(game):
    return ini.get_key(ini.read(game / install.STRINGS_INI), "general", "version")


def test_main_menu_shows_the_mods_version(game):
    install.install(game, 1832, log=quiet)
    assert menu_label(game) == LABEL
    # only that value changed
    assert ini.read(game / install.STRINGS_INI) == STRINGS_INI.replace("= Version", f"= {LABEL}")
    assert (game / install.BACKUP_DIR / install.STRINGS_INI).read_bytes() == STRINGS_INI.encode("latin-1")


def test_the_menu_label_isnt_added_twice(game):
    install.install(game, 1832, log=quiet)
    install.install(game, 1368, log=quiet)
    assert menu_label(game) == LABEL


def test_an_install_from_before_the_label_gets_it(game):
    install.install(game, 1832, log=quiet)
    # what 0.3.0 left: STRINGS.INI untouched and not in the backup
    saved = game / install.BACKUP_DIR / install.STRINGS_INI
    (game / install.STRINGS_INI).write_bytes(saved.read_bytes())
    saved.unlink()
    install.install(game, 1832, log=quiet)
    assert menu_label(game) == LABEL
    assert saved.read_bytes() == STRINGS_INI.encode("latin-1")
    install.uninstall(game, log=quiet)
    assert (game / install.STRINGS_INI).read_bytes() == STRINGS_INI.encode("latin-1")


def test_uninstall_from_before_the_label_leaves_strings_ini_alone(game):
    install.install(game, 1832, log=quiet)
    saved = game / install.BACKUP_DIR / install.STRINGS_INI
    (game / install.STRINGS_INI).write_bytes(saved.read_bytes())
    saved.unlink()
    install.uninstall(game, log=quiet)
    assert (game / install.STRINGS_INI).read_bytes() == STRINGS_INI.encode("latin-1")


def test_a_label_left_behind_is_not_kept_as_the_original(game):
    # an older version of the mod removed itself without knowing about the label
    path = game / install.STRINGS_INI
    ini.write(path, ini.set_key(ini.read(path), "general", "version", "ttbotc_resolution_mod 0.4.0. game Version"))
    install.install(game, 1832, log=quiet)
    assert menu_label(game) == LABEL
    install.uninstall(game, log=quiet)
    assert path.read_bytes() == STRINGS_INI.encode("latin-1")


def test_a_game_without_strings_ini(game):
    (game / install.STRINGS_INI).unlink()
    original = snapshot(game)
    install.install(game, 1832, log=quiet)
    assert not (game / install.BACKUP_DIR / install.STRINGS_INI).exists()
    install.uninstall(game, log=quiet)
    assert snapshot(game) == original


def test_status(game):
    state = install.status(game)
    assert not state.installed and state.exe.is_original
    install.install(game, 1368, log=quiet)
    state = install.status(game)
    assert state.installed and state.width == 1368 and state.exe.width == 1368


def test_a_steam_update_is_detected_and_fixed(game):
    install.install(game, 1832, log=quiet)
    (game / STEAM_EXE).write_bytes(make_exe())  # Steam put the original back
    state = install.status(game)
    assert state.installed and state.exe.is_original
    install.install(game, state.width, log=quiet)
    check_installed(game, 1832)


def test_refuses_files_changed_by_something_else(game):
    (game / install.FRAME).write_bytes(make_frame(1280))
    with pytest.raises(install.InstallError, match="already changed"):
        install.install(game, 1832, log=quiet)


def test_refuses_an_unknown_exe(game):
    (game / STEAM_EXE).write_bytes(b"MZ something else")
    with pytest.raises(install.InstallError, match="isn't supported"):
        install.install(game, 1832, log=quiet)


def test_refuses_a_width_out_of_range(game):
    with pytest.raises(resolutions.BadWidth):
        install.install(game, 3000, log=quiet)
    assert not (game / install.BACKUP_DIR).exists()


def test_refuses_an_incomplete_folder(game):
    (game / install.LAYOUT_INI).unlink()
    with pytest.raises(install.InstallError, match="missing"):
        install.install(game, 1832, log=quiet)


def test_a_damaged_manifest_stops_everything(game):
    install.install(game, 1832, log=quiet)
    (game / install.BACKUP_DIR / FILE).write_text("{oops")
    with pytest.raises(install.InstallError, match="damaged"):
        install.status(game)
    with pytest.raises(install.InstallError, match="damaged"):
        install.uninstall(game, log=quiet)


def test_uninstall_without_the_mod(game):
    with pytest.raises(install.InstallError, match="isn't installed"):
        install.uninstall(game, log=quiet)


def test_linux_sets_and_removes_the_proton_override(game, prefix):
    original = prefix.read_bytes()
    assert install.install(game, 1832, log=quiet) is True
    text = proton.read(prefix)
    assert proton.current(text, STEAM_EXE) == proton.VALUE
    manifest = Manifest.load(game / install.BACKUP_DIR)
    assert manifest.proton_override is True and manifest.proton_previous is None
    assert not install.status(game).proton_missing
    install.install(game, 1368, log=quiet)  # changing the width leaves it alone
    assert proton.read(prefix) == text
    install.uninstall(game, log=quiet)
    assert prefix.read_bytes() == original


def test_linux_puts_back_an_override_that_was_there(game, prefix):
    before = proton.add(proton.read(prefix), 7, STEAM_EXE).replace(proton.VALUE, '"ddraw"="builtin"')
    prefix.write_bytes(before.encode("latin-1"))
    install.install(game, 1832, log=quiet)
    assert proton.current(proton.read(prefix), STEAM_EXE) == proton.VALUE
    install.uninstall(game, log=quiet)
    assert proton.read(prefix) == before


def test_linux_leaves_alone_an_override_the_player_set(game, prefix):
    before = proton.add(proton.read(prefix), 7, STEAM_EXE)
    prefix.write_bytes(before.encode("latin-1"))
    install.install(game, 1832, log=quiet)
    assert Manifest.load(game / install.BACKUP_DIR).proton_override is False
    install.uninstall(game, log=quiet)
    assert proton.read(prefix) == before


def test_linux_without_a_prefix_yet(game, prefix):
    prefix.unlink()
    assert install.install(game, 1832, log=quiet) is False
    check_installed(game, 1832)  # the game's files are done anyway
    assert install.status(game).proton_missing
    prefix.write_bytes(USER_REG.encode("latin-1"))  # the player started the game once
    assert install.install(game, 1832, log=quiet) is True
    assert not install.status(game).proton_missing
    install.uninstall(game, log=quiet)
    assert prefix.read_bytes() == USER_REG.encode("latin-1")


def test_windows_never_touches_a_prefix(game, prefix, monkeypatch):
    monkeypatch.setattr(proton, "ENABLED", False)
    install.install(game, 1832, log=quiet)
    assert prefix.read_bytes() == USER_REG.encode("latin-1")
    assert not install.status(game).proton_missing


def test_refuses_while_the_game_runs(game, prefix, monkeypatch):
    monkeypatch.setattr(proton, "game_running", lambda: True)
    original = snapshot(game)
    with pytest.raises(install.InstallError, match="quit the game"):
        install.install(game, 1832, log=quiet)
    assert snapshot(game) == original


# GOG: the same files, with the game as Tzar.exe; on Linux, Heroic runs it in a Wine prefix of its own. It all goes
# through the same code as Steam: only the exe's name and the prefix differ.


def test_gog_install_and_uninstall(gog_game):
    original = snapshot(gog_game)
    install.install(gog_game, 1832, log=quiet)
    assert exe_patch.inspect((gog_game / GOG_EXE).read_bytes()).width == 1832
    assert not (gog_game / STEAM_EXE).exists()
    assert Manifest.load(gog_game / install.BACKUP_DIR).exe == GOG_EXE
    assert (gog_game / install.BACKUP_DIR / GOG_EXE).read_bytes() == make_exe()
    assert ini.get_key(ini.read(gog_game / "ddraw.ini"), "Tzar", "adjmouse") == "true"  # cnc-ddraw's own preset
    assert install.status(gog_game).exe_name == GOG_EXE
    install.install(gog_game, 1368, log=quiet)
    assert exe_patch.inspect((gog_game / GOG_EXE).read_bytes()).width == 1368
    install.uninstall(gog_game, log=quiet)
    assert snapshot(gog_game) == original


def test_steam_leaves_its_launcher_alone(game):
    launcher = (game / GOG_EXE).read_bytes()
    install.install(game, 1832, log=quiet)
    assert (game / GOG_EXE).read_bytes() == launcher
    assert Manifest.load(game / install.BACKUP_DIR).exe == STEAM_EXE
    assert install.status(game).exe_name == STEAM_EXE
    assert not (game / install.BACKUP_DIR / GOG_EXE).exists()


def test_heroic_sets_and_removes_the_override(gog_game, heroic_prefix):
    original = heroic_prefix.read_bytes()
    assert install.install(gog_game, 1832, log=quiet) is True
    text = proton.read(heroic_prefix)
    assert proton.current(text, GOG_EXE) == proton.VALUE
    assert proton.current(text, STEAM_EXE) is None
    assert Manifest.load(gog_game / install.BACKUP_DIR).proton_user_reg == str(heroic_prefix)
    assert not install.status(gog_game).proton_missing
    install.uninstall(gog_game, log=quiet)
    assert heroic_prefix.read_bytes() == original


def test_heroic_without_a_prefix_yet(gog_game, heroic_prefix):
    heroic_prefix.unlink()
    assert install.install(gog_game, 1832, log=quiet) is False
    assert install.status(gog_game).proton_missing
    heroic_prefix.write_bytes(USER_REG.encode("latin-1"))  # the player started the game once from Heroic
    assert install.install(gog_game, 1832, log=quiet) is True
    assert not install.status(gog_game).proton_missing
    install.uninstall(gog_game, log=quiet)
    assert heroic_prefix.read_bytes() == USER_REG.encode("latin-1")


def test_linux_with_a_launcher_the_mod_doesnt_know(gog_game, monkeypatch):
    monkeypatch.setattr(proton, "ENABLED", True)
    original = snapshot(gog_game)
    lines = []
    assert install.install(gog_game, 1832, log=lines.append) is True
    assert any('WINEDLLOVERRIDES="ddraw=n,b"' in line for line in lines)
    assert not install.status(gog_game).proton_missing
    install.uninstall(gog_game, log=quiet)
    assert snapshot(gog_game) == original


def as_installed_by_0_4_0(game):
    """Rewrite the manifest the way 0.4.0 wrote it: no exe, no user.reg."""
    path = game / install.BACKUP_DIR / FILE
    data = json.loads(path.read_text())
    del data["exe"], data["proton_user_reg"]
    data["version"] = "0.4.0"
    path.write_text(json.dumps(data))


def test_upgrading_a_steam_install_from_0_4_0(game, prefix):
    original = snapshot(game)
    install.install(game, 1832, log=quiet)
    as_installed_by_0_4_0(game)
    manifest = Manifest.load(game / install.BACKUP_DIR)
    assert manifest.exe == STEAM_EXE and manifest.proton_user_reg is None
    state = install.status(game)
    assert state.installed and state.exe_name == STEAM_EXE and not state.proton_missing
    install.install(game, 1368, log=quiet)
    check_installed(game, 1368)
    assert Manifest.load(game / install.BACKUP_DIR).proton_user_reg == str(prefix)
    install.uninstall(game, log=quiet)
    assert snapshot(game) == original
    assert prefix.read_bytes() == USER_REG.encode("latin-1")


def test_uninstalling_a_0_4_0_steam_install(game, prefix):
    original = snapshot(game)
    install.install(game, 1832, log=quiet)
    as_installed_by_0_4_0(game)
    install.uninstall(game, log=quiet)
    assert snapshot(game) == original
    assert prefix.read_bytes() == USER_REG.encode("latin-1")
