import pytest

from conftest import USER_REG
from tzar_widescreen import proton

HEADER = r"[Software\\Wine\\AppDefaults\\Tzar_.exe\\DllOverrides]"


def test_add_appends_the_section():
    text = proton.add(USER_REG, 1794532075)
    assert text.startswith(USER_REG)
    assert text[len(USER_REG):] == f"\n{HEADER} 1794532075\n" + '"ddraw"="native,builtin"\n'
    assert proton.current(text) == proton.VALUE


def test_add_then_remove_gives_back_the_same_bytes():
    assert proton.remove(proton.add(USER_REG, 1), None) == USER_REG


def test_add_is_idempotent():
    once = proton.add(USER_REG, 1)
    assert proton.add(once, 2) == once


def test_add_to_a_file_without_a_final_newline():
    text = proton.add(USER_REG.rstrip("\n"), 1)
    assert '"USERPROFILE"="C:\\\\users\\\\steamuser"\n\n' + HEADER in text


@pytest.fixture
def existing():
    """Tzar's section already there, Wine-style, with another override and a section after it."""
    return USER_REG.replace("[Volatile Environment]",
                            f'{HEADER} 5\n#time=1dd\n"ddraw"="builtin"\n"dinput"="native"\n\n[Volatile Environment]')


def test_add_replaces_an_existing_ddraw_line(existing):
    assert proton.current(existing) == '"ddraw"="builtin"'
    text = proton.add(existing, 1)
    assert proton.current(text) == proton.VALUE
    assert text == existing.replace('"ddraw"="builtin"', proton.VALUE)


def test_remove_puts_the_previous_line_back(existing):
    text = proton.add(existing, 1)
    assert proton.remove(text, '"ddraw"="builtin"') == existing


def test_remove_keeps_a_section_with_other_overrides(existing):
    text = proton.remove(existing, None)
    assert proton.current(text) is None
    assert f'{HEADER} 5\n#time=1dd\n"dinput"="native"\n\n[Volatile Environment]' in text


def test_add_to_a_section_without_ddraw_goes_under_its_time_line():
    text = USER_REG.replace("[Volatile Environment]", f"{HEADER} 5\n#time=1dd\n\n[Volatile Environment]")
    added = proton.add(text, 1)
    assert f'{HEADER} 5\n#time=1dd\n"ddraw"="native,builtin"\n\n[Volatile' in added
    assert proton.remove(added, None) == USER_REG  # the section had nothing else: it goes, cleanly


def test_remove_without_the_section_changes_nothing():
    assert proton.remove(USER_REG, None) == USER_REG


def test_other_exes_sections_are_not_mistaken_for_tzars():
    text = USER_REG.replace("Avengers.exe", "Tzar_.exe.bak")
    assert proton.current(text) is None


def test_user_reg_path(tmp_path):
    game = tmp_path / "steamapps" / "common" / "Tzar"
    assert proton.user_reg(game) == tmp_path / "steamapps" / "compatdata" / "825730" / "pfx" / "user.reg"
