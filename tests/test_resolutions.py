import pytest

from tzar_widescreen import resolutions


@pytest.mark.parametrize("screen, width", [
    ((3440, 1440), 1832),  # 21:9 ultrawide
    ((5160, 2160), 1832),  # the same screen at 150% scaling under GNOME
    ((2560, 1080), 1824),  # 64:27 ultrawide
    ((1920, 1080), 1368),  # 16:9
    ((2560, 1600), 1232),  # 16:10
    ((1024, 768), 1032),   # 4:3: as narrow as the mod goes
    ((5120, 1440), 2198),  # 32:9: as wide as the mod goes
])
def test_width_for_screen(screen, width):
    assert resolutions.for_screen(*screen) == width


def test_presets_are_within_the_limits():
    for width, _ in resolutions.PRESETS:
        assert resolutions.check(width) == width
    assert resolutions.check(resolutions.DEFAULT_WIDTH) == resolutions.DEFAULT_WIDTH


@pytest.mark.parametrize("width", [1024, 1031, 2199, 4000])
def test_widths_outside_the_limits_are_refused(width):
    with pytest.raises(resolutions.BadWidth):
        resolutions.check(width)
