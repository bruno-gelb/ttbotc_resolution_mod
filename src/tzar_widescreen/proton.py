"""Make Proton load cnc-ddraw, with a DLL override in Tzar's Proton prefix.

Wine prefers its own ddraw.dll to the one in the game folder. Under Proton each game has its own Wine prefix, with
its own registry, in steamapps/compatdata/<app id>/pfx. The override goes into that registry's user.reg, limited to
Tzar_.exe, in the same AppDefaults section Proton uses for its own per-game overrides. It does what the launch
option WINEDLLOVERRIDES="ddraw=n,b" did, without the player touching Steam. Windows doesn't need any of this.

Wine writes its registry back when the game exits, so it must not run while user.reg is changed.
"""

import sys
from pathlib import Path

APP_ID = "825730"
# On Windows the game loads ddraw.dll from its folder anyway.
ENABLED = sys.platform != "win32"
PROCESS = "Tzar_.exe"
SECTION = r"[Software\\Wine\\AppDefaults\\Tzar_.exe\\DllOverrides]"
NAME = '"ddraw"='
VALUE = '"ddraw"="native,builtin"'


def user_reg(game_dir: Path) -> Path:
    """Tzar's user.reg: the game is in steamapps/common/<folder>, its prefix in steamapps/compatdata/<app id>/pfx."""
    return game_dir.resolve().parent.parent / "compatdata" / APP_ID / "pfx" / "user.reg"


def game_running() -> bool:
    """Whether Tzar's process is running, as Wine names it: Tzar_.exe."""
    for comm in Path("/proc").glob("[0-9]*/comm"):
        try:
            if comm.read_text().strip() == PROCESS:
                return True
        except OSError:  # the process ended meanwhile
            pass
    return False


def read(path: Path) -> str:
    return path.read_bytes().decode("latin-1")  # byte for byte: Wine escapes anything outside ASCII anyway


def _find(lines: list[str]) -> tuple[int, int, int | None] | None:
    """(header, end, ddraw line) of the section in lines, or None. end is the index after the section's last line."""
    for start, line in enumerate(lines):
        if line.rstrip("\n").split(" ")[0] == SECTION:
            end = start + 1
            while end < len(lines) and not lines[end].startswith("["):
                end += 1
            value = next((i for i in range(start + 1, end) if lines[i].startswith(NAME)), None)
            return start, end, value
    return None


def current(text: str) -> str | None:
    """The ddraw line in the section, like '"ddraw"="native,builtin"', or None."""
    lines = text.splitlines(keepends=True)
    found = _find(lines)
    if found is None or found[2] is None:
        return None
    return lines[found[2]].rstrip("\n")


def add(text: str, now: int) -> str:
    """text with the override set. now is the time Wine stamps on the section header, in Unix seconds."""
    lines = text.splitlines(keepends=True)
    found = _find(lines)
    if found is None:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        return "".join(lines) + f"\n{SECTION} {now}\n{VALUE}\n"
    start, _, value = found
    if value is not None:
        lines[value] = VALUE + "\n"
    else:
        insert = start + 1
        while insert < len(lines) and lines[insert].startswith("#"):  # #time= and the like stay right under it
            insert += 1
        lines.insert(insert, VALUE + "\n")
    return "".join(lines)


def remove(text: str, previous: str | None) -> str:
    """text with the ddraw line put back to previous, or taken out (and the section with it, if that leaves it empty)."""
    lines = text.splitlines(keepends=True)
    found = _find(lines)
    if found is None or found[2] is None:
        return text
    start, end, value = found
    if previous is not None:
        lines[value] = previous + "\n"
        return "".join(lines)
    del lines[value]
    end -= 1
    if all(not line.strip() or line.startswith("#") for line in lines[start + 1:end]):
        # A section in the middle takes its trailing blank line along. The last one has none: take the blank line
        # before it instead, the one add() put there.
        if end == len(lines) and start > 0 and not lines[start - 1].strip():
            start -= 1
        del lines[start:end]
    return "".join(lines)
