"""The game's music on Linux: TZMUS.dll, a stand-in for winmm with a built-in MIDI synthesizer, and its soundfont.

Tzar plays its music as MIDI, which Windows synthesizes itself, but Wine needs a synthesizer from Linux and a desktop
usually has none, so the music is silent there. The installer copies these files into the game folder and renames
the exe's winmm import to TZMUS.dll (exe_patch.MUSIC_PATCH), on Linux only. See native/tzmus/ for the DLL and
docs/findings.md, "Music".

The files are bundled with the Linux release build; in a source tree, make them with src/tools/fetch_soundfont.py
and src/tools/build_music.py.
"""

import shutil
import sys
from pathlib import Path

BUNDLED = Path(__file__).parent / "music"
FILES = ["TZMUS.dll", "TZMUS.sf2", "TZMUS-LICENSES.txt"]
# Windows has a MIDI synthesizer of its own, and plays the music already.
ENABLED = sys.platform != "win32"


def available() -> bool:
    return all((BUNDLED / name).is_file() for name in FILES)


def install(game_dir: Path) -> None:
    for name in FILES:
        shutil.copy2(BUNDLED / name, game_dir / name)
