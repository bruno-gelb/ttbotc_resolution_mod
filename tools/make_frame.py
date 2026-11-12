"""Widen the in-game frame bitmap (SCREEN 1024 LEFT.BMP) to a new width.

Usage: uv run tools/make_frame.py <original bmp> <output bmp> <width>

Works on the raw 16-bit pixels, so every color stays exactly as in the original. The left panel and the top bar up to
the vine ornament are kept; the ornament (from ORNAMENT_X to the right edge) is repeated to fill the new width, and
the original right end closes the bar. The map view area is the game's green color key and is simply extended.
"""

import struct
import sys

ORNAMENT_X = 810  # where the vine ornament on the top bar starts in the 1024-wide original
TOP_BAR_H = 30    # rows 0..29 are the top bar (LAYOUT.INI: view starts at y = 30)


def read_bmp16(path):
    data = open(path, "rb").read()
    if data[:2] != b"BM":
        sys.exit(f"{path}: not a BMP")
    off = struct.unpack_from("<I", data, 10)[0]
    w, h = struct.unpack_from("<ii", data, 18)
    bpp, comp = struct.unpack_from("<HI", data, 28)
    if bpp != 16 or comp != 0:
        sys.exit(f"{path}: expected an uncompressed 16-bit BMP, got {bpp} bpp, compression {comp}")
    stride = (w * 2 + 3) & ~3
    top_down = h < 0
    h = abs(h)
    rows = []
    for y in range(h):
        src = y if top_down else h - 1 - y
        start = off + src * stride
        rows.append(list(struct.unpack_from(f"<{w}H", data, start)))
    return data[:off], w, h, rows  # rows[0] is the top row


def write_bmp16(path, header, w, h, rows):
    stride = (w * 2 + 3) & ~3
    off = len(header)
    hdr = bytearray(header)
    struct.pack_into("<I", hdr, 2, off + stride * h)          # file size
    struct.pack_into("<ii", hdr, 18, w, h)                     # bottom-up
    struct.pack_into("<I", hdr, 34, stride * h)                # image size
    out = bytearray(hdr)
    pad = b"\0" * (stride - w * 2)
    for y in range(h - 1, -1, -1):
        out += struct.pack(f"<{w}H", *rows[y]) + pad
    open(path, "wb").write(out)


def ornament_period(rows, x0, x1):
    """Smallest horizontal shift at which the ornament best matches itself (mean absolute difference)."""
    def chan(p):
        return ((p >> 10) & 31, (p >> 5) & 31, p & 31)

    best = None
    for period in range(40, (x1 - x0) // 2 + 1):
        diff = 0
        n = 0
        for y in range(TOP_BAR_H):
            r = rows[y]
            for x in range(x0, x1 - period):
                a, b = chan(r[x]), chan(r[x + period])
                diff += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
                n += 1
        score = diff / n
        if best is None or score < best[1]:
            best = (period, score)
    return best


def main():
    src, dst, new_w = sys.argv[1], sys.argv[2], int(sys.argv[3])
    header, w, h, rows = read_bmp16(src)
    if new_w <= w:
        sys.exit(f"new width {new_w} must be larger than {w}")
    key = rows[h // 2][w // 2]  # the green color key in the middle of the view
    period, score = ornament_period(rows, ORNAMENT_X, w)
    print(f"original {w}x{h}, color key {key:#06x}, ornament period {period} px (match error {score:.2f})")

    tail_w = w - ORNAMENT_X              # the original ornament, kept as the right end
    fill_from, fill_to = ORNAMENT_X, new_w - tail_w
    out = []
    for y in range(h):
        r = rows[y]
        if y < TOP_BAR_H:
            row = r[:ORNAMENT_X]
            row += [r[ORNAMENT_X + (x - fill_from) % period] for x in range(fill_from, fill_to)]
            row += r[ORNAMENT_X:]
        else:
            row = r + [key] * (new_w - w)
        out.append(row)
    write_bmp16(dst, header, new_w, h, out)
    print(f"wrote {dst}: {new_w}x{h}")


if __name__ == "__main__":
    main()
