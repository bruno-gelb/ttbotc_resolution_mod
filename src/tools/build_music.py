"""Build TZMUS.dll, the Linux music fix, into src/tzar_widescreen/music/ (which git ignores), with its licenses.

Usage: uv run python src/tools/build_music.py
Needs the soundfont first: uv run python src/tools/fetch_soundfont.py

Compiled with Zig (the ziglang package, pinned in pyproject.toml) for 32-bit Windows, since the game is a 32-bit
Windows program that Wine runs. --render also builds the native test program, which plays a MIDI file through the same
core into a WAV file: render <soundfont.sf2> <music.mid> <out.wav> [seconds].
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native"
OUT = ROOT / "src" / "tzar_widescreen" / "music"
FLAGS = ["-O2", "-std=c99", "-Wall", "-Wextra", "-Wno-unused-function", "-Wno-unused-parameter", "-Werror"]


def zig_cc(*args: str) -> None:
    # TinySoundFont as a system include: strict warnings for the mod's code, not for the vendored library's
    subprocess.run([sys.executable, "-m", "ziglang", "cc", *FLAGS, "-isystem", str(NATIVE / "third_party"), *args],
                   check=True, cwd=ROOT)


def build_dll(out: Path = OUT) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    dll = out / "TZMUS.dll"
    zig_cc("-target", "x86-windows-gnu", "-shared", "-s", "-o", str(dll),
           str(NATIVE / "tzmus" / "tzmus.c"), str(NATIVE / "tzmus" / "core.c"), str(NATIVE / "tzmus" / "tzmus.def"))
    for leftover in out.iterdir():  # the linker's import library and the like: not needed
        if leftover.suffix.lower() in (".lib", ".pdb", ".a"):
            leftover.unlink()
    return dll


def build_render(out: Path) -> Path:
    zig_cc("-o", str(out), str(NATIVE / "tzmus" / "render.c"), str(NATIVE / "tzmus" / "core.c"), "-lm")
    return out


def write_licenses() -> None:
    fluid = OUT / "FluidR3-LICENSE.txt"
    if not fluid.is_file():
        sys.exit("the soundfont's license is missing: run src/tools/fetch_soundfont.py first")
    tsf = (NATIVE / "third_party" / "tinysoundfont" / "LICENSE").read_text(encoding="utf-8")
    (OUT / "TZMUS-LICENSES.txt").write_text(
        "TZMUS.dll and TZMUS.sf2 play Tzar's music on Linux, for the Tzar widescreen mod\n"
        "(https://github.com/bruno-gelb/ttbotc_resolution_mod, MIT license).\n\n"
        "TZMUS.dll includes TinySoundFont (https://github.com/schellingb/TinySoundFont):\n\n"
        f"{tsf}\n\n"
        f"{fluid.read_text(encoding='utf-8')}", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--render", type=Path, help="also build the native test program, to this path")
    args = parser.parse_args()
    dll = build_dll()
    write_licenses()
    print(f"built {dll} ({dll.stat().st_size // 1024} KB)")
    if args.render:
        print(f"built {build_render(args.render)}")


if __name__ == "__main__":
    main()
