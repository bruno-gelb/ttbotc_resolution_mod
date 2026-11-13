import struct

import pytest

from conftest import KEY, ORNAMENT_PERIOD, make_frame
from tzar_widescreen import frame


def pixels(data: bytes) -> list[list[int]]:
    _, _, _, rows = frame._read16(data)
    return rows


def test_size():
    assert frame.size(make_frame()) == (1024, 768)


def test_widen_sets_the_new_size():
    wide = frame.widen(make_frame(), 1832)
    assert frame.size(wide) == (1832, 768)
    stride = 1832 * 2
    assert len(wide) == 54 + stride * 768
    assert struct.unpack_from("<I", wide, 2)[0] == len(wide)


def test_widen_keeps_the_left_part_and_the_ornament_end():
    rows, wide = pixels(make_frame()), pixels(frame.widen(make_frame(), 1832))
    for y in (0, 15, 29):
        assert wide[y][:frame.ORNAMENT_X] == rows[y][:frame.ORNAMENT_X]
        assert wide[y][-(1024 - frame.ORNAMENT_X):] == rows[y][frame.ORNAMENT_X:]
    for y in (30, 400, 767):
        assert wide[y][:1024] == rows[y]


def test_widen_repeats_the_ornament_and_extends_the_map_view():
    wide = pixels(frame.widen(make_frame(), 1832))
    top = wide[10]
    filled = top[frame.ORNAMENT_X:1832 - (1024 - frame.ORNAMENT_X)]
    assert all(filled[x] == filled[x % ORNAMENT_PERIOD] for x in range(len(filled)))
    assert set(wide[400][1024:]) == {KEY}


@pytest.mark.parametrize("width", [1032, 1368, 2198])
def test_widen_any_supported_width(width):
    assert frame.size(frame.widen(make_frame(), width)) == (width, 768)


def test_widen_refuses_a_narrower_width():
    with pytest.raises(frame.BadBitmap):
        frame.widen(make_frame(), 1024)


def test_refuses_other_bitmaps():
    with pytest.raises(frame.BadBitmap):
        frame.size(b"GIF89a")
    data = bytearray(make_frame())
    struct.pack_into("<H", data, 28, 24)  # 24 bits per pixel
    with pytest.raises(frame.BadBitmap):
        frame.widen(bytes(data), 1832)
