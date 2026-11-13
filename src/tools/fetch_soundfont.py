"""Fetch the FluidR3 GM soundfont and trim it to the instruments Tzar's music uses, for the Linux music DLL.

Usage: uv run python src/tools/fetch_soundfont.py [--deb <a local copy of the package>]

FluidR3 GM (Frank Wen, MIT license) comes from Debian's fluid-soundfont-gm package, pinned by version and checksum.
The whole bank is 148 MB; Tzar's 14 MIDI files play 22 General MIDI instruments and the standard drum kit, so only
the zones those notes reach go into src/tzar_widescreen/music/TZMUS.sf2 (35 MB), which git ignores. See
docs/findings.md, "Music".
"""

import argparse
import hashlib
import io
import lzma
import sys
import tarfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import soundfont  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "src" / "tzar_widescreen" / "music"
URL = "https://deb.debian.org/debian/pool/main/f/fluid-soundfont/fluid-soundfont-gm_3.1-5.3_all.deb"
SHA256 = "6f531493ac4e4d9772fd96b2488ea1790af81c196135fbdd25997da0781fc60e"
MEMBER = "./usr/share/sounds/sf2/FluidR3_GM.sf2"
COPYRIGHT = "./usr/share/doc/fluid-soundfont-gm/copyright"

# What Tzar's music plays: (bank, program) -> the lowest and highest note, across its 14 MIDI files, widened by the
# pitch bend range (the default 2 semitones; the files don't change it). Bank 0 is General MIDI, bank 128 program 0
# the standard drum kit, where each note is a different drum. Measured 2026-11-13 by merging each file's tracks in
# time and following each channel's program changes; Violin (40) is selected but never plays.
RANGES = {
    (0, 14): (53, 83),    # Tubular Bells
    (0, 19): (14, 71),    # Church Organ
    (0, 20): (65, 76),    # Reed Organ
    (0, 24): (26, 90),    # Nylon Guitar
    (0, 25): (41, 73),    # Steel Guitar
    (0, 44): (51, 86),    # Tremolo Strings
    (0, 45): (31, 78),    # Pizzicato Strings
    (0, 46): (50, 74),    # Orchestral Harp
    (0, 47): (26, 59),    # Timpani
    (0, 48): (19, 95),    # String Ensemble 1
    (0, 49): (50, 74),    # String Ensemble 2
    (0, 52): (29, 78),    # Choir Aahs
    (0, 54): (36, 86),    # Synth Voice
    (0, 57): (36, 87),    # Trombone
    (0, 58): (26, 81),    # Tuba
    (0, 60): (31, 86),    # French Horn
    (0, 68): (50, 88),    # Oboe
    (0, 69): (34, 76),    # English Horn
    (0, 73): (43, 79),    # Flute
    (0, 75): (51, 95),    # Pan Flute
    (0, 104): (50, 71),   # Sitar
    (0, 111): (50, 83),   # Shanai
}
DRUMS = {38, 40, 49, 52, 54, 57, 60, 61, 62, 64, 69, 84, 87}  # snare, cymbals, toms, bongos, triangle...
KEEP = {key: set(range(lo, hi + 1)) for key, (lo, hi) in RANGES.items()} | {(128, 0): DRUMS}


def deb_member(deb: bytes, wanted: set[str]) -> dict[str, bytes]:
    """Files from a .deb's data.tar.xz: an ar archive, whose data member is an xz-compressed tar."""
    if deb[:8] != b"!<arch>\n":
        sys.exit("not a .deb (ar) archive")
    i = 8
    while i + 60 <= len(deb):
        name, size = deb[i:i + 16].decode().strip().rstrip("/"), int(deb[i + 48:i + 58].decode().strip())
        body = deb[i + 60:i + 60 + size]
        i += 60 + size + (size & 1)
        if name == "data.tar.xz":
            with tarfile.open(fileobj=io.BytesIO(lzma.decompress(body))) as tar:
                return {m: tar.extractfile(m).read() for m in wanted}
    sys.exit("no data.tar.xz in the package")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deb", type=Path, help="a local copy of the package, instead of downloading it")
    args = parser.parse_args()
    if args.deb:
        deb = args.deb.read_bytes()
    else:
        print(f"downloading {URL}")
        with urllib.request.urlopen(URL) as response:
            deb = response.read()
    if hashlib.sha256(deb).hexdigest() != SHA256:
        sys.exit("the package's checksum doesn't match: refusing to use it")
    files = deb_member(deb, {MEMBER, COPYRIGHT})
    del deb
    full = files[MEMBER]
    trimmed = soundfont.trim(full, KEEP)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "TZMUS.sf2").write_bytes(trimmed)
    (OUT / "FluidR3-LICENSE.txt").write_bytes(
        b"FluidR3 GM, trimmed to the instruments Tzar's music uses: TZMUS.sf2\n\n" + files[COPYRIGHT])
    print(f"wrote {OUT / 'TZMUS.sf2'}: {len(trimmed) // 1024} KB of {len(full) // 1024} KB, "
          f"{len(soundfont.presets(trimmed))} presets")


if __name__ == "__main__":
    main()
