from conftest import LAYOUT_INI, TZAR_INI
from tzar_widescreen import ini


def test_get_key():
    assert ini.get_key(TZAR_INI, "VIDEO", "DIRECTXDEVICE") == "-1"
    assert ini.get_key(LAYOUT_INI, "LAYOUT1024L", "view") == "150,30,874,738"


def test_get_key_is_case_insensitive():
    assert ini.get_key(TZAR_INI, "video", "directxdevice") == "-1"


def test_get_missing_key_or_section():
    assert ini.get_key(TZAR_INI, "VIDEO", "NOPE") is None
    assert ini.get_key(TZAR_INI, "NOPE", "DIRECTXDEVICE") is None


def test_get_key_looks_only_in_its_section():
    # LAYOUT1024H has a view too; the L section's must be found
    assert ini.get_key(LAYOUT_INI, "LAYOUT1024H", "view") == "0,30,1024,584"


def test_set_key_keeps_everything_else():
    text = ini.set_key(TZAR_INI, "VIDEO", "DIRECTXDEVICE", "0")
    assert text == TZAR_INI.replace("DIRECTXDEVICE=-1", "DIRECTXDEVICE=0")


def test_set_key_keeps_spacing_and_line_endings():
    text = ini.set_key(LAYOUT_INI, "LAYOUT1024L", "view", "150,30,1682,738")
    assert "view = 150,30,1682,738\r\n" in text
    assert "view = 0,30,1024,584\r\n" in text  # the other section's view is untouched
    assert "\n" not in text.replace("\r\n", "")


def test_set_missing_key_goes_right_under_the_header():
    text = ini.set_key(TZAR_INI, "VIDEO", "FORCE16", "1")
    assert "[VIDEO]\r\nFORCE16=1\r\nBUFFER_IN_VIDEO_MEMORY=0\r\n" in text
    assert ini.get_key(text, "VIDEO", "FORCE16") == "1"


def test_set_key_in_a_missing_section_appends_it():
    text = ini.set_key(TZAR_INI, "Tzar_", "adjmouse", "true")
    assert text.endswith("[Tzar_]\r\nadjmouse=true\r\n")
    assert text.startswith(TZAR_INI)


def test_set_key_in_a_file_without_final_newline():
    text = ini.set_key("[a]\nx=1", "b", "y", "2")
    assert text == "[a]\nx=1\n[b]\ny=2\n"
