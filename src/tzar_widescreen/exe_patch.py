"""Patches to Tzar_.exe (Steam version 1.10). See docs/findings.md for what each one does and how it was found.

Every patch knows the original bytes. Before anything is written, each spot must hold either the original or the
patched bytes; anything else means an unknown version of the exe, and nothing is changed.
"""

import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import pefile


@dataclass(frozen=True)
class SizePatch:
    """An instruction with a screen size in it: only the value slot changes."""

    va: int
    original: bytes
    value_offset: int
    fmt: str
    which: str  # "width" or "height"


@dataclass(frozen=True)
class FixedPatch:
    """Bytes replaced with other bytes, whatever the screen size."""

    va: int
    original: bytes
    patched: bytes


SIZE_PATCHES = [
    # mov word ptr [0x587732], 1024: screen width when the layout name contains "1024"
    SizePatch(0x43BB31, bytes.fromhex("66c705327758000004"), 7, "<H", "width"),
    # mov word ptr [0x587734], 768: screen height, same place
    SizePatch(0x43BB3A, bytes.fromhex("66c705347758000003"), 7, "<H", "height"),
    # cmp bx, 1024 in the width-to-height helper: "is this the big mode?"
    SizePatch(0x474398, bytes.fromhex("6681fb0004"), 3, "<H", "width"),
    # mov edi, 768 in the same helper: then the height is this
    SizePatch(0x4743A4, bytes.fromhex("bf00030000"), 1, "<I", "height"),
]

FIXED_PATCHES = [
    # The map view marks what to redraw in a 64-bit mask per row, one bit per 16 px column, so nothing past 1024 px
    # from the view's left edge was ever redrawn. These make each bit cover 32 px, up to 2048 px. Rows stay 16 px.
    FixedPatch(0x4F9A1D, bytes.fromhex("c1f804"), bytes.fromhex("c1f805")),  # rect left x -> column
    FixedPatch(0x4F9A78, bytes.fromhex("c1f904"), bytes.fromhex("c1f905")),  # rect right x -> column
    FixedPatch(0x4F3864, bytes.fromhex("6683c510"), bytes.fromhex("6683c520")),  # skip a clear bit
    FixedPatch(0x4F3887, bytes.fromhex("668344241c10"), bytes.fromhex("668344241c20")),  # extend right edge
    FixedPatch(0x4F38A7, bytes.fromhex("668344241c10"), bytes.fromhex("668344241c20")),  # same, 2nd mask
    FixedPatch(0x4F38B9, bytes.fromhex("6681c50002"), bytes.fromhex("6681c50004")),  # skip the 1st mask
    FixedPatch(0x4F38CA, bytes.fromhex("6683c510"), bytes.fromhex("6683c520")),  # skip a clear bit, 2nd mask
    FixedPatch(0x4F38EF, bytes.fromhex("668344241c10"), bytes.fromhex("668344241c20")),  # extend right, 2nd mask
    # At startup the game refuses to run when the sound devices it finds differ from the counts in tzar.ini: on any
    # machine but the one that wrote tzar.ini, and whenever headphones or HDMI audio come or go. Its fix, Setup.exe,
    # doesn't start under Proton. The check (0x4d07e0) still runs and still counts the devices; only "refuse if
    # they differ" (jne at 0x4558d0) is skipped. The game uses the default sound device anyway.
    FixedPatch(0x4558D0, bytes.fromhex("750a"), bytes.fromhex("9090")),
]


class UnknownExe(Exception):
    """The exe isn't the Steam version 1.10, original or patched by this mod."""


@dataclass
class ExeState:
    patched: int  # how many of the fixed patches are applied
    total: int
    width: int
    height: int

    @property
    def is_original(self) -> bool:
        return self.patched == 0 and (self.width, self.height) == (1024, 768)


def _offsets(data: bytes) -> dict[int, int]:
    try:
        pe = pefile.PE(data=bytes(data), fast_load=True)
        base = pe.OPTIONAL_HEADER.ImageBase
        vas = [p.va for p in SIZE_PATCHES] + [p.va for p in FIXED_PATCHES]
        offsets = {va: pe.get_offset_from_rva(va - base) for va in vas}
    except Exception as error:  # not a PE file, or the spots are outside it
        raise UnknownExe(f"not a Tzar_.exe this mod knows ({error})") from error
    if any(off is None or off + 9 > len(data) for off in offsets.values()):
        raise UnknownExe("not a Tzar_.exe this mod knows (too small)")
    return offsets


def inspect(data: bytes) -> ExeState:
    """Check every patch spot. Raises UnknownExe if any of them holds unexpected bytes."""
    offsets = _offsets(data)
    sizes = {}
    for p in SIZE_PATCHES:
        off = offsets[p.va]
        cur = bytes(data[off:off + len(p.original)])
        size = struct.calcsize(p.fmt)
        if cur[:p.value_offset] != p.original[:p.value_offset] or \
                cur[p.value_offset + size:] != p.original[p.value_offset + size:]:
            raise UnknownExe(f"unexpected bytes at {p.va:#x}: {cur.hex(' ')}")
        sizes[p.which] = struct.unpack_from(p.fmt, cur, p.value_offset)[0]
    patched = 0
    for p in FIXED_PATCHES:
        off = offsets[p.va]
        cur = bytes(data[off:off + len(p.original)])
        if cur == p.patched:
            patched += 1
        elif cur != p.original:
            raise UnknownExe(f"unexpected bytes at {p.va:#x}: {cur.hex(' ')}")
    return ExeState(patched, len(FIXED_PATCHES), sizes["width"], sizes["height"])


def apply(data: bytes, width: int, height: int) -> bytes:
    """Return the exe with every patch applied for this screen size."""
    inspect(data)
    offsets = _offsets(data)
    out = bytearray(data)
    values = {"width": width, "height": height}
    for p in SIZE_PATCHES:
        struct.pack_into(p.fmt, out, offsets[p.va] + p.value_offset, values[p.which])
    for p in FIXED_PATCHES:
        out[offsets[p.va]:offsets[p.va] + len(p.patched)] = p.patched
    return bytes(out)


def original(data: bytes) -> bytes:
    """Return the exe with every patch spot put back as in the original game."""
    inspect(data)
    offsets = _offsets(data)
    out = bytearray(data)
    for p in [*SIZE_PATCHES, *FIXED_PATCHES]:
        out[offsets[p.va]:offsets[p.va] + len(p.original)] = p.original
    return bytes(out)


def main() -> None:
    """For development: python -m tzar_widescreen.exe_patch <Tzar_.exe> [<width> <height>]"""
    path = Path(sys.argv[1])
    data = path.read_bytes()
    if len(sys.argv) > 2:
        data = apply(data, int(sys.argv[2]), int(sys.argv[3]))
        path.write_bytes(data)
    print(inspect(data))


if __name__ == "__main__":
    main()
