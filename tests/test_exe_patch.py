import struct

import pytest

from conftest import IMAGE_BASE, make_exe
from tzar_widescreen import exe_patch


def test_original_exe_is_recognized():
    state = exe_patch.inspect(make_exe())
    assert state.is_original
    assert (state.width, state.height) == (1024, 768)
    assert state.patched == 0
    assert state.total == len(exe_patch.FIXED_PATCHES)


def test_apply_sets_the_size_and_every_fix():
    patched = exe_patch.apply(make_exe(), 1832, 768)
    state = exe_patch.inspect(patched)
    assert (state.width, state.height) == (1832, 768)
    assert state.patched == state.total
    assert not state.is_original


def test_apply_changes_only_the_patch_spots():
    original = make_exe()
    patched = exe_patch.apply(original, 1832, 768)
    changed = sum(a != b for a, b in zip(original, patched))
    assert changed == 14  # 4 bytes of screen size, 8 of redraw tracking, 2 of the sound check


def test_original_undoes_apply_exactly():
    original = make_exe()
    assert exe_patch.original(exe_patch.apply(original, 2198, 768)) == original


def test_apply_again_with_another_size():
    once = exe_patch.apply(make_exe(), 1832, 768)
    twice = exe_patch.apply(once, 1368, 768)
    assert exe_patch.inspect(twice).width == 1368
    assert twice == exe_patch.apply(make_exe(), 1368, 768)


def test_partly_patched_exe_is_counted():
    data = bytearray(make_exe())
    fix = exe_patch.FIXED_PATCHES[0]
    data[fix.va - IMAGE_BASE:fix.va - IMAGE_BASE + len(fix.patched)] = fix.patched
    assert exe_patch.inspect(bytes(data)).patched == 1


def test_unexpected_bytes_are_refused():
    data = bytearray(make_exe())
    fix = exe_patch.FIXED_PATCHES[-1]
    data[fix.va - IMAGE_BASE] ^= 0xFF
    with pytest.raises(exe_patch.UnknownExe, match="unexpected bytes"):
        exe_patch.inspect(bytes(data))
    with pytest.raises(exe_patch.UnknownExe):
        exe_patch.apply(bytes(data), 1832, 768)


def test_size_instruction_with_other_opcode_is_refused():
    data = bytearray(make_exe())
    size = exe_patch.SIZE_PATCHES[0]
    data[size.va - IMAGE_BASE] = 0x90
    with pytest.raises(exe_patch.UnknownExe):
        exe_patch.inspect(bytes(data))


@pytest.mark.parametrize("data", [b"", b"not an exe at all", b"MZ" + b"\0" * 100])
def test_not_an_exe_is_refused(data):
    with pytest.raises(exe_patch.UnknownExe):
        exe_patch.inspect(data)


def test_width_value_lands_in_the_instruction():
    patched = exe_patch.apply(make_exe(), 1500, 768)
    size = exe_patch.SIZE_PATCHES[0]
    offset = size.va - IMAGE_BASE + size.value_offset
    assert struct.unpack_from("<H", patched, offset)[0] == 1500


def test_the_music_patch_renames_winmm_and_comes_off():
    data = make_exe()
    patched = exe_patch.apply(data, 1832, 768, music=True)
    assert exe_patch.inspect(patched).music and not exe_patch.inspect(data).music
    off = exe_patch.MUSIC_PATCH.va - 0x400000
    assert patched[off:off + 10] == b"TZMUS.dll\0"
    assert not exe_patch.inspect(exe_patch.apply(patched, 1832, 768)).music  # without music: back to WINMM.dll
    assert exe_patch.original(patched) == data


def test_an_unknown_import_name_is_refused():
    data = bytearray(make_exe())
    off = exe_patch.MUSIC_PATCH.va - 0x400000
    data[off:off + 9] = b"OTHER.dll"
    with pytest.raises(exe_patch.UnknownExe):
        exe_patch.inspect(bytes(data))
