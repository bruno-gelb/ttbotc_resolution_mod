import pytest

from conftest import GOG_EXE, STEAM_EXE, USER_REG, heroic_config
from tzar_widescreen import heroic, proton

HEADER = r"[Software\\Wine\\AppDefaults\\Tzar_.exe\\DllOverrides]"
EXE = STEAM_EXE


def test_add_appends_the_section():
    text = proton.add(USER_REG, 1794532075, EXE)
    assert text.startswith(USER_REG)
    assert text[len(USER_REG):] == f"\n{HEADER} 1794532075\n" + '"ddraw"="native,builtin"\n'
    assert proton.current(text, EXE) == proton.VALUE


def test_add_then_remove_gives_back_the_same_bytes():
    assert proton.remove(proton.add(USER_REG, 1, EXE), None, EXE) == USER_REG


def test_add_is_idempotent():
    once = proton.add(USER_REG, 1, EXE)
    assert proton.add(once, 2, EXE) == once


def test_add_to_a_file_without_a_final_newline():
    text = proton.add(USER_REG.rstrip("\n"), 1, EXE)
    assert '"USERPROFILE"="C:\\\\users\\\\steamuser"\n\n' + HEADER in text


@pytest.fixture
def existing():
    """Tzar's section already there, Wine-style, with another override and a section after it."""
    return USER_REG.replace("[Volatile Environment]",
                            f'{HEADER} 5\n#time=1dd\n"ddraw"="builtin"\n"dinput"="native"\n\n[Volatile Environment]')


def test_add_replaces_an_existing_ddraw_line(existing):
    assert proton.current(existing, EXE) == '"ddraw"="builtin"'
    text = proton.add(existing, 1, EXE)
    assert proton.current(text, EXE) == proton.VALUE
    assert text == existing.replace('"ddraw"="builtin"', proton.VALUE)


def test_remove_puts_the_previous_line_back(existing):
    text = proton.add(existing, 1, EXE)
    assert proton.remove(text, '"ddraw"="builtin"', EXE) == existing


def test_remove_keeps_a_section_with_other_overrides(existing):
    text = proton.remove(existing, None, EXE)
    assert proton.current(text, EXE) is None
    assert f'{HEADER} 5\n#time=1dd\n"dinput"="native"\n\n[Volatile Environment]' in text


def test_add_to_a_section_without_ddraw_goes_under_its_time_line():
    text = USER_REG.replace("[Volatile Environment]", f"{HEADER} 5\n#time=1dd\n\n[Volatile Environment]")
    added = proton.add(text, 1, EXE)
    assert f'{HEADER} 5\n#time=1dd\n"ddraw"="native,builtin"\n\n[Volatile' in added
    assert proton.remove(added, None, EXE) == USER_REG  # the section had nothing else: it goes, cleanly


def test_remove_without_the_section_changes_nothing():
    assert proton.remove(USER_REG, None, EXE) == USER_REG


def test_other_exes_sections_are_not_mistaken_for_tzars():
    text = USER_REG.replace("Avengers.exe", "Tzar_.exe.bak")
    assert proton.current(text, EXE) is None


def test_the_section_is_named_after_the_games_exe():
    assert proton.section(STEAM_EXE) == HEADER
    assert proton.section(GOG_EXE) == r"[Software\\Wine\\AppDefaults\\Tzar.exe\\DllOverrides]"


def test_steam_and_gog_sections_dont_mix():
    text = proton.add(USER_REG, 1, GOG_EXE)
    assert proton.current(text, GOG_EXE) == proton.VALUE
    assert proton.current(text, STEAM_EXE) is None
    assert proton.remove(text, None, GOG_EXE) == USER_REG


def test_steams_prefix(tmp_path):
    game = tmp_path / "steamapps" / "common" / "Tzar"
    game.mkdir(parents=True)
    prefix = proton.find_prefix(game)
    assert prefix.user_reg == tmp_path / "steamapps" / "compatdata" / "825730" / "pfx" / "user.reg"
    assert prefix.launcher == "Steam"


@pytest.mark.parametrize("wine_type, user_reg", [("proton", "pfx/user.reg"), ("wine", "user.reg")])
def test_heroics_prefix(gog_game, tmp_path, monkeypatch, wine_type, user_reg):
    config = tmp_path / "heroic"
    monkeypatch.setattr(heroic, "CONFIG_DIRS", [config])
    heroic_config(config, gog_game, tmp_path / "prefix", wine_type)
    prefix = proton.find_prefix(gog_game)
    assert prefix.user_reg == tmp_path / "prefix" / user_reg
    assert prefix.launcher == "Heroic"


def test_no_prefix_for_a_folder_no_launcher_knows(gog_game):
    assert proton.find_prefix(gog_game) is None


def test_no_prefix_when_heroic_doesnt_say(gog_game, tmp_path, monkeypatch):
    config = tmp_path / "heroic"
    monkeypatch.setattr(heroic, "CONFIG_DIRS", [config])
    heroic_config(config, gog_game, None)
    assert proton.find_prefix(gog_game) is None
