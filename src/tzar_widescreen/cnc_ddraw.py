"""cnc-ddraw (https://github.com/FunkyFr3sh/cnc-ddraw, MIT): a DirectDraw replacement that offers the game a display
mode no monitor has and scales the picture to the screen.

Its files are bundled with the mod's release builds; in a source tree, fetch them with src/tools/fetch_cnc_ddraw.py.
"""

import shutil
from pathlib import Path

from tzar_widescreen import ini

BUNDLED = Path(__file__).parent / "cnc_ddraw"
FILES = ["ddraw.dll", "ddraw.ini", "Shaders"]


def available() -> bool:
    return all((BUNDLED / name).exists() for name in FILES)


def install(game_dir: Path, width: int, height: int, exe: str) -> None:
    """Copy cnc-ddraw into the game folder and configure it for this screen size and the game's exe."""
    shutil.copy2(BUNDLED / "ddraw.dll", game_dir / "ddraw.dll")
    shutil.copytree(BUNDLED / "Shaders", game_dir / "Shaders", dirs_exist_ok=True)
    text = ini.read(BUNDLED / "ddraw.ini")
    for key, value in [
        ("fullscreen", "true"),               # fill the screen
        ("maintas", "true"),                  # keep the aspect ratio
        ("inject_resolution", f"{width}x{height}"),  # the display mode the game asks for
        ("resolutions", "2"),                 # the full list of modes
        ("renderer", "opengl"),
    ]:
        text = ini.set_key(text, "ddraw", key, value)
    # cnc-ddraw's per-game sections are named after the exe. Its own [Tzar] preset covers GOG's Tzar.exe; on Steam
    # the game is Tzar_.exe (Tzar.exe is the launcher), so the preset's setting goes into a [Tzar_] section too.
    text = ini.set_key(text, Path(exe).stem, "adjmouse", "true")
    ini.write(game_dir / "ddraw.ini", text)
