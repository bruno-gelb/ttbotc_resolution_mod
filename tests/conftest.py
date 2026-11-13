"""Synthetic game files for the tests: the game's own files can't go into the repository.

The exe is a minimal 32-bit PE laid out like Tzar_.exe (file offset = address - 0x400000) with the original bytes at
every patch address. The frame bitmap, tzar.ini, LAYOUT.INI and STRINGS.INI are small stand-ins with the same
structure.
"""

import hashlib
import struct
from pathlib import Path

import pytest

from tzar_widescreen import cnc_ddraw, exe_patch, install, proton, resolutions

IMAGE_BASE = 0x400000
TEXT_RVA = 0x1000
TEXT_RAW = 0x159000  # big enough for every patch address, like the real .text section
KEY = 0x03E0         # the green color key in the map view area
ORNAMENT_PERIOD = 42

TZAR_INI = (
    "[DEFAULTS]\r\nLAYOUT=LAYOUT800L\r\nHWCURSOR=0\r\nSCROLLSPEED=2\r\n\r\n"
    "[VIDEO]\r\nBUFFER_IN_VIDEO_MEMORY=0\r\nDIRECTXDEVICE=-1\r\nDIRECTDRAW_DEVICESNUMBER=2\r\n\r\n"
    "[SOUND]\r\nSOUNDDEVICENUMBER=3\r\nSOUNDDEVICEDXNUMBER=3\r\nSOUNDDEVICEMIDINUMBER=2\r\n"
)
LAYOUT_INI = (
    "; layout: 1 = down, 2 = left, 3 = right\r\n\r\n"
    "[LAYOUT1024H]\r\nlayout = 1\r\nview = 0,30,1024,584\r\n\r\n"
    "[LAYOUT1024L]\r\nlayout = 2\r\nimage = screen 1024 left.bmp\r\nview = 150,30,874,738\r\n"
    "minimap = 4, 31, 128, 128\r\n"
)
STRINGS_INI = (
    "[general]\r\ndefgamename = Default\r\ngamename = The TZAR game\r\nversion = Version\r\n"
    "net_title = TZAR NETWORK\r\n\r\n[options]\r\ntitle = Options\r\n"
)
DDRAW_INI = (
    "; cnc-ddraw\r\n[ddraw]\r\nwidth=0\r\nheight=0\r\nfullscreen=false\r\nmaintas=false\r\nrenderer=auto\r\n"
    "inject_resolution=\r\nresolutions=0\r\n\r\n; Tzar: The Burden of the Crown\r\n[Tzar]\r\nadjmouse=true\r\n"
)


def make_exe() -> bytes:
    """A minimal PE32 file whose .text section maps the way Tzar_.exe's does, with the original patch bytes."""
    headers = bytearray(0x1000)
    headers[0:2] = b"MZ"
    struct.pack_into("<I", headers, 0x3C, 0x40)  # e_lfanew
    headers[0x40:0x44] = b"PE\0\0"
    # COFF header: machine i386, 1 section, no symbols, optional header size, executable 32-bit
    struct.pack_into("<HHIIIHH", headers, 0x44, 0x14C, 1, 0, 0, 0, 0xE0, 0x0102)
    opt = 0x58
    struct.pack_into("<HBB", headers, opt, 0x10B, 6, 0)  # PE32
    # code size, data sizes, entry point, base of code, base of data
    struct.pack_into("<IIIIII", headers, opt + 4, TEXT_RAW, 0, 0, TEXT_RVA, TEXT_RVA, TEXT_RVA + TEXT_RAW)
    struct.pack_into("<III", headers, opt + 28, IMAGE_BASE, 0x1000, 0x200)  # image base, alignments
    struct.pack_into("<HHHHHH", headers, opt + 40, 4, 0, 0, 0, 4, 0)  # OS, image and subsystem versions
    struct.pack_into("<IIII", headers, opt + 52, 0, TEXT_RVA + TEXT_RAW, 0x1000, 0)  # image and headers size
    struct.pack_into("<HH", headers, opt + 68, 2, 0)  # Windows GUI
    struct.pack_into("<IIIIII", headers, opt + 72, 0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    section = opt + 0xE0
    headers[section:section + 8] = b".text\0\0\0"
    struct.pack_into("<IIIIIIHHI", headers, section + 8, TEXT_RAW, TEXT_RVA, TEXT_RAW, 0x1000, 0, 0, 0, 0,
                     0x60000020)
    data = headers + bytearray(TEXT_RAW)
    for patch in [*exe_patch.SIZE_PATCHES, *exe_patch.FIXED_PATCHES]:
        offset = patch.va - IMAGE_BASE
        data[offset:offset + len(patch.original)] = patch.original
    return bytes(data)


def make_frame(width: int = 1024, height: int = 768) -> bytes:
    """A 16-bit BMP shaped like the game's frame: top bar with a repeating ornament, left panel, green map view."""
    rows = []
    for y in range(height):
        if y < 30:
            row = [(x * 7 + y) & 0x7FFF for x in range(810)]
            row += [0x2000 + (x - 810) % ORNAMENT_PERIOD for x in range(810, width)]
        else:
            row = [(x + y * 3) & 0x7FFF for x in range(150)] + [KEY] * (width - 150)
        rows.append(row)
    stride = (width * 2 + 3) & ~3
    image = bytearray()
    for y in range(height - 1, -1, -1):  # bottom-up
        image += struct.pack(f"<{width}H", *rows[y]) + b"\0" * (stride - width * 2)
    header = b"BM" + struct.pack("<IHHI", 54 + len(image), 0, 0, 54)
    header += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 16, 0, len(image), 2835, 2835, 0, 0)
    return header + bytes(image)


def snapshot(folder: Path) -> dict[str, str]:
    """Every file under folder, by relative path, with its SHA-256."""
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.fixture(autouse=True)
def bundled_cnc_ddraw(tmp_path, monkeypatch):
    """Stand-ins for cnc-ddraw's files, so the tests don't need the real download."""
    bundle = tmp_path / "cnc_ddraw"
    (bundle / "Shaders").mkdir(parents=True)
    (bundle / "ddraw.dll").write_bytes(b"not really cnc-ddraw")
    (bundle / "ddraw.ini").write_bytes(DDRAW_INI.encode("latin-1"))
    (bundle / "Shaders" / "test.glsl").write_text("// shader")
    monkeypatch.setattr(cnc_ddraw, "BUNDLED", bundle)
    return bundle


@pytest.fixture(autouse=True)
def screen(monkeypatch):
    """A fixed 3440x1440 screen, so the tests don't depend on the machine's."""
    monkeypatch.setattr(resolutions, "detect_screen", lambda: (3440, 1440))


@pytest.fixture(autouse=True)
def no_proton(monkeypatch):
    """Windows behaviour by default, whatever runs the tests: the proton fixture turns Proton on."""
    monkeypatch.setattr(proton, "ENABLED", False)
    monkeypatch.setattr(proton, "game_running", lambda: False)


# The tail of a real user.reg: Proton's own per-game overrides look like this.
USER_REG = """WINE REGISTRY Version 2
;; All keys relative to REGISTRY\\\\User\\\\S-1-5-21-0-0-1000-1000

#arch=win64

[Software\\\\Wine\\\\AppDefaults\\\\Avengers.exe\\\\DllOverrides] 1793987668
#time=1dd6e17de46e4a0
"atiadlxx"="builtin"

[Volatile Environment] 1793987668
#time=1dd6e17de47b7c4
"USERPROFILE"="C:\\\\users\\\\steamuser"
"""


@pytest.fixture
def prefix(game, monkeypatch) -> Path:
    """Linux: Tzar's Proton prefix next to the game folder, as Steam lays it out. Returns its user.reg."""
    monkeypatch.setattr(proton, "ENABLED", True)
    reg = game.parent.parent / "compatdata" / proton.APP_ID / "pfx" / "user.reg"
    reg.parent.mkdir(parents=True)
    reg.write_bytes(USER_REG.encode("latin-1"))
    return reg


@pytest.fixture
def game(tmp_path) -> Path:
    """A synthetic, unmodded game folder, in a Steam library's steamapps/common."""
    folder = tmp_path / "steamapps" / "common" / "Tzar"
    (folder / "DATA").mkdir(parents=True)
    (folder / "IMAGES/SCREENS/S_VIEW").mkdir(parents=True)
    (folder / "LOCAL").mkdir()
    (folder / install.EXE).write_bytes(make_exe())
    (folder / install.TZAR_INI).write_bytes(TZAR_INI.encode("latin-1"))
    (folder / install.LAYOUT_INI).write_bytes(LAYOUT_INI.encode("latin-1"))
    (folder / install.FRAME).write_bytes(make_frame())
    (folder / install.STRINGS_INI).write_bytes(STRINGS_INI.encode("latin-1"))
    return folder
