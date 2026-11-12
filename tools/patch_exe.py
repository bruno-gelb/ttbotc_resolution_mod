"""Patch Tzar_.exe (Steam version 1.10) so the "1024" layouts use a different screen size.

Usage: uv run tools/patch_exe.py <Tzar_.exe> <width> <height>

Every patch checks the bytes first: the original instruction, or one this script already patched. Anything else
stops the script without writing, so it can't damage an unknown version of the exe.
"""

import struct
import sys

import pefile

# Screen size. (VA of the instruction, its original bytes, offset of the value inside it, value format, which size)
SIZE_PATCHES = [
    # 0x43bb31: mov word ptr [0x587732], 1024  -- screen width when the layout name contains "1024"
    (0x43BB31, bytes.fromhex("66c705327758000004"), 7, "<H", "width"),
    # 0x43bb3a: mov word ptr [0x587734], 768   -- screen height, same place
    (0x43BB3A, bytes.fromhex("66c705347758000003"), 7, "<H", "height"),
    # 0x474398: cmp bx, 1024                   -- width-to-height helper: "is this the big mode?"
    (0x474398, bytes.fromhex("6681fb0004"), 3, "<H", "width"),
    # 0x4743a4: mov edi, 768                   -- ...then the height is this
    (0x4743A4, bytes.fromhex("bf00030000"), 1, "<I", "height"),
]

# Dirty rectangles: the map view marks what to redraw in a 64-bit mask per row, one bit per 16 px column, so
# nothing past 1024 px from the view's left edge was ever redrawn. These make each bit cover 32 px (up to 2048 px).
# Rows stay 16 px. (VA, original bytes, patched bytes, what it is)
FIXED_PATCHES = [
    (0x4F9A1D, "c1f804", "c1f805", "rect left x -> column: sar eax, 4 -> 5"),
    (0x4F9A78, "c1f904", "c1f905", "rect right x -> column: sar ecx, 4 -> 5"),
    (0x4F3864, "6683c510", "6683c520", "redraw: skip a clear bit, add bp, 16 -> 32"),
    (0x4F3887, "668344241c10", "668344241c20", "redraw: extend right edge, 16 -> 32"),
    (0x4F38A7, "668344241c10", "668344241c20", "redraw: extend right edge (2nd mask), 16 -> 32"),
    (0x4F38B9, "6681c50002", "6681c50004", "redraw: skip the 1st mask, add bp, 512 -> 1024"),
    (0x4F38CA, "6683c510", "6683c520", "redraw: skip a clear bit (2nd mask), 16 -> 32"),
    (0x4F38EF, "668344241c10", "668344241c20", "redraw: extend right edge (2nd mask), 16 -> 32"),
]


def main():
    path, width, height = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    pe = pefile.PE(path, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    data = bytearray(open(path, "rb").read())
    values = {"width": width, "height": height}
    planned = []

    for va, orig, val_off, fmt, which in SIZE_PATCHES:
        off = pe.get_offset_from_rva(va - base)
        cur = bytes(data[off:off + len(orig)])
        size = struct.calcsize(fmt)
        # Same instruction with any value in the value slot = original or already patched.
        if cur[:val_off] != orig[:val_off] or cur[val_off + size:] != orig[val_off + size:]:
            sys.exit(f"{va:#x}: unexpected bytes {cur.hex(' ')}; is this the Steam 1.10 Tzar_.exe? Nothing written.")
        old = struct.unpack_from(fmt, cur, val_off)[0]
        new = struct.pack(fmt, values[which])
        planned.append((off + val_off, new, f"{va:#x} {which}: {old} -> {values[which]}"))

    for va, orig_hex, new_hex, what in FIXED_PATCHES:
        orig, new = bytes.fromhex(orig_hex), bytes.fromhex(new_hex)
        off = pe.get_offset_from_rva(va - base)
        cur = bytes(data[off:off + len(orig)])
        if cur not in (orig, new):
            sys.exit(f"{va:#x}: unexpected bytes {cur.hex(' ')}; is this the Steam 1.10 Tzar_.exe? Nothing written.")
        planned.append((off, new, f"{va:#x} {what}" + (" (already)" if cur == new else "")))

    for off, new, msg in planned:
        data[off:off + len(new)] = new
        print(msg)
    open(path, "wb").write(data)


if __name__ == "__main__":
    main()
