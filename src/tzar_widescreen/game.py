"""Find the game folder: Steam libraries, GOG installs (Heroic, and GOG's own installer on Windows), or the folder
the program runs from. And which exe in it is the game.
"""

import os
import re
import sys
from pathlib import Path

from tzar_widescreen import heroic

STEAM_APP_ID = 825730
# The game's own exe. On Steam it's Tzar_.exe, and Tzar.exe is a 21 KB launcher for it. On GOG, Tzar.exe is the
# game: the same build as Steam's Tzar_.exe, without Steam's signature.
EXES = ["Tzar_.exe", "Tzar.exe"]
LAUNCHER_SIZE = 100_000  # bytes: Steam's launcher is smaller, the game's 1.7 MB exe bigger


def resolve(root: Path, relative: str) -> Path:
    """root / relative, matching each part case-insensitively (the game's own files use mixed case)."""
    path = root
    for part in Path(relative).parts:
        exact = path / part
        if exact.exists():
            path = exact
            continue
        try:
            match = next((p for p in path.iterdir() if p.name.lower() == part.lower()), None)
        except OSError:
            match = None
        path = match if match else exact
    return path


def exe_name(path: Path) -> str | None:
    """The game's exe in the folder: Tzar_.exe (Steam) or Tzar.exe (GOG). None if neither is there."""
    for name in EXES:
        exe = resolve(path, name)
        try:
            if exe.is_file() and exe.stat().st_size > LAUNCHER_SIZE:
                return name
        except OSError:
            pass
    return None


def is_game_dir(path: Path) -> bool:
    return exe_name(path) is not None


def _steam_roots() -> list[Path]:
    roots = []
    if sys.platform == "win32":
        import winreg

        for hive, key, value in [
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        ]:
            try:
                with winreg.OpenKey(hive, key) as k:
                    roots.append(Path(winreg.QueryValueEx(k, value)[0]))
            except OSError:
                pass
        roots.append(Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam")
    else:
        home = Path.home()
        roots += [
            home / ".steam/steam",
            home / ".steam/root",
            home / ".steam/debian-installation",
            home / ".local/share/Steam",
            home / ".var/app/com.valvesoftware.Steam/.local/share/Steam",  # Flatpak
            home / "snap/steam/common/.local/share/Steam",                 # Snap
        ]
    return roots


def _libraries(root: Path) -> list[Path]:
    libraries = [root]
    vdf = resolve(root, "steamapps/libraryfolders.vdf")
    try:
        text = vdf.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return libraries
    for raw in re.findall(r'"path"\s+"([^"]+)"', text):
        libraries.append(Path(raw.replace("\\\\", "\\")))
    return libraries


def _steam_game_dirs() -> list[Path]:
    found = []
    for root in _steam_roots():
        for library in _libraries(root):
            installdir = "Tzar"
            manifest = resolve(library, f"steamapps/appmanifest_{STEAM_APP_ID}.acf")
            try:
                match = re.search(r'"installdir"\s+"([^"]+)"', manifest.read_text(errors="replace"))
                if match:
                    installdir = match.group(1)
            except OSError:
                pass
            found.append(resolve(library, f"steamapps/common/{installdir}"))
    return found


def _gog_windows_dirs() -> list[Path]:
    """Windows: where GOG's installer put the game. Its install script sets Haemimont's own Path value, and GOG
    Galaxy keeps its games under GOG.com\\Games\\<game id>."""
    if sys.platform != "win32":
        return []
    import winreg

    found = []
    for hive, key, value in [
        (winreg.HKEY_CURRENT_USER, r"Software\Haemimont\Tzar", "Path"),
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\GOG.com\Games\{heroic.GOG_ID}", "path"),
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\GOG.com\Games\{heroic.GOG_ID}", "path"),
    ]:
        try:
            with winreg.OpenKey(hive, key) as k:
                found.append(Path(winreg.QueryValueEx(k, value)[0]))
        except OSError:
            pass
    return found


def find() -> list[Path]:
    """Game folders found on this machine: the program's own folder and the working folder first, then Steam, then
    GOG (Heroic, and GOG's installer on Windows)."""
    here = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]).resolve().parent
    candidates = [here, Path.cwd(), *_steam_game_dirs(), *(i.game_dir for i in heroic.installs()), *_gog_windows_dirs()]
    seen, result = set(), []
    for path in candidates:
        try:
            key = path.resolve()
        except OSError:
            continue
        if key not in seen and is_game_dir(key):
            seen.add(key)
            result.append(key)
    return result
