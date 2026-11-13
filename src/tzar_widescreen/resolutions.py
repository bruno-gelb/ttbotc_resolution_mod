"""Which resolutions the mod can run the game at, and which one fits the player's screen.

The height stays 768, the height of the game's own panel art; the width sets the screen shape. cnc-ddraw scales the
picture up to the screen, keeping its shape.
"""

import os
import re
import subprocess
import sys

HEIGHT = 768
MIN_WIDTH = 1032  # anything wider than the original 1024
MAX_WIDTH = 2198  # the 150 px panel plus 2048 px of map: the reach of the patched redraw tracking
DEFAULT_WIDTH = 1832

# (width, label); widths are multiples of 8 close to each shape at 768 px high
PRESETS = [
    (1232, "16:10"),
    (1368, "16:9"),
    (1832, "21:9, ultrawide"),
]


class BadWidth(ValueError):
    pass


def check(width: int) -> int:
    if not MIN_WIDTH <= width <= MAX_WIDTH:
        raise BadWidth(f"the width must be from {MIN_WIDTH} to {MAX_WIDTH}, not {width}")
    return width


def for_screen(screen_width: int, screen_height: int) -> int:
    """The width with the same shape as the screen, rounded to a multiple of 8 and kept within the limits."""
    width = round(HEIGHT * screen_width / screen_height / 8) * 8
    return min(max(width, MIN_WIDTH), MAX_WIDTH)


def detect_screen() -> tuple[int, int] | None:
    """The main screen's size in pixels, or None if it can't be told. Only its shape matters."""
    try:
        if sys.platform == "win32":
            import ctypes

            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()  # real pixels, not the size Windows scaling pretends
            w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            return (w, h) if w > 0 and h > 0 else None
        env = dict(os.environ)
        if getattr(sys, "frozen", False):  # PyInstaller points LD_LIBRARY_PATH at its own libraries: undo that
            if "LD_LIBRARY_PATH_ORIG" in env:
                env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
            else:
                env.pop("LD_LIBRARY_PATH", None)
        out = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=5, env=env).stdout
        match = re.search(r" connected primary (\d+)x(\d+)", out) or re.search(r" connected (\d+)x(\d+)", out)
        return (int(match.group(1)), int(match.group(2))) if match else None
    except Exception:
        return None
