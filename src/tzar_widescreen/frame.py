"""Widen the in-game frame bitmap (IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP) to a new width.

Works on the raw 16-bit pixels, so every color stays exactly as in the original. The left panel and the top bar up to
the vine ornament are kept; the ornament (from ORNAMENT_X to the right edge) is repeated to fill the new width, and
the original right end closes the bar. The map view area is the game's green color key and is simply extended.
"""

import struct
import sys
from pathlib import Path

ORNAMENT_X = 810  # where the vine ornament on the top bar starts in the 1024-wide original
TOP_BAR_H = 30    # rows 0..29 are the top bar (LAYOUT.INI: the view starts at y = 30)


class BadBitmap(Exception):
    pass


def size(data: bytes) -> tuple[int, int]:
    """Width and height of a BMP."""
    if data[:2] != b"BM" or len(data) < 26:
        raise BadBitmap("not a BMP file")
    w, h = struct.unpack_from("<ii", data, 18)
    return w, abs(h)


def _read16(data: bytes):
    if data[:2] != b"BM":
        raise BadBitmap("not a BMP file")
    off = struct.unpack_from("<I", data, 10)[0]
    w, h = struct.unpack_from("<ii", data, 18)
    bpp, comp = struct.unpack_from("<HI", data, 28)
    if bpp != 16 or comp != 0:
        raise BadBitmap(f"expected an uncompressed 16-bit BMP, got {bpp} bpp, compression {comp}")
    stride = (w * 2 + 3) & ~3
    top_down = h < 0
    h = abs(h)
    rows = []
    for y in range(h):
        src = y if top_down else h - 1 - y
        rows.append(list(struct.unpack_from(f"<{w}H", data, off + src * stride)))
    return data[:off], w, h, rows  # rows[0] is the top row


def _write16(header: bytes, w: int, h: int, rows) -> bytes:
    stride = (w * 2 + 3) & ~3
    hdr = bytearray(header)
    struct.pack_into("<I", hdr, 2, len(header) + stride * h)  # file size
    struct.pack_into("<ii", hdr, 18, w, h)                      # bottom-up
    struct.pack_into("<I", hdr, 34, stride * h)                 # image size
    out = bytearray(hdr)
    pad = b"\0" * (stride - w * 2)
    for y in range(h - 1, -1, -1):
        out += struct.pack(f"<{w}H", *rows[y]) + pad
    return bytes(out)


def _ornament_period(rows, x0: int, x1: int) -> int:
    """The horizontal shift at which the ornament best matches itself (mean absolute difference)."""
    def chan(p):
        return (p >> 10) & 31, (p >> 5) & 31, p & 31

    best = None
    for period in range(40, (x1 - x0) // 2 + 1):
        diff = n = 0
        for y in range(TOP_BAR_H):
            r = rows[y]
            for x in range(x0, x1 - period):
                a, b = chan(r[x]), chan(r[x + period])
                diff += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
                n += 1
        if best is None or diff / n < best[1]:
            best = (period, diff / n)
    return best[0]


def widen(data: bytes, new_width: int) -> bytes:
    """Return the frame bitmap widened to new_width."""
    header, w, h, rows = _read16(data)
    if new_width <= w:
        raise BadBitmap(f"new width {new_width} must be larger than {w}")
    key = rows[h // 2][w // 2]  # the green color key in the middle of the view
    period = _ornament_period(rows, ORNAMENT_X, w)
    fill_to = new_width - (w - ORNAMENT_X)  # the original ornament stays as the right end
    out = []
    for y in range(h):
        r = rows[y]
        if y < TOP_BAR_H:
            row = r[:ORNAMENT_X]
            row += [r[ORNAMENT_X + (x - ORNAMENT_X) % period] for x in range(ORNAMENT_X, fill_to)]
            row += r[ORNAMENT_X:]
        else:
            row = r + [key] * (new_width - w)
        out.append(row)
    return _write16(header, new_width, h, out)


def main() -> None:
    """For development: python -m tzar_widescreen.frame <original bmp> <output bmp> <width>"""
    src, dst, new_width = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    dst.write_bytes(widen(src.read_bytes(), new_width))
    print(f"wrote {dst}: {size(dst.read_bytes())}")


if __name__ == "__main__":
    main()
