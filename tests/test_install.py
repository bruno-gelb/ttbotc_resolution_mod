import pytest

from conftest import make_exe, make_frame, snapshot
from tzar_widescreen import exe_patch, frame, ini, install, resolutions
from tzar_widescreen.manifest import FILE, Manifest


def quiet(_line):
    pass


def check_installed(game, width):
    assert exe_patch.inspect((game / install.EXE).read_bytes()).width == width
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
    (game / install.EXE).write_bytes(exe_patch.apply(make_exe(), 1832, 768))
    install.install(game, 1832, log=quiet)
    assert (game / install.BACKUP_DIR / install.EXE).read_bytes() == make_exe()


def test_status(game):
    state = install.status(game)
    assert not state.installed and state.exe.is_original
    install.install(game, 1368, log=quiet)
    state = install.status(game)
    assert state.installed and state.width == 1368 and state.exe.width == 1368


def test_a_steam_update_is_detected_and_fixed(game):
    install.install(game, 1832, log=quiet)
    (game / install.EXE).write_bytes(make_exe())  # Steam put the original back
    state = install.status(game)
    assert state.installed and state.exe.is_original
    install.install(game, state.width, log=quiet)
    check_installed(game, 1832)


def test_refuses_files_changed_by_something_else(game):
    (game / install.FRAME).write_bytes(make_frame(1280))
    with pytest.raises(install.InstallError, match="already changed"):
        install.install(game, 1832, log=quiet)


def test_refuses_an_unknown_exe(game):
    (game / install.EXE).write_bytes(b"MZ something else")
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
