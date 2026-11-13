"""Heroic Games Launcher: where it installed GOG's Tzar, and which Wine prefix runs it.

Heroic keeps its GOG installs in gog_store/installed.json (appName, install_path) and each game's settings in
GamesConfig/<appName>.json (winePrefix, and wineVersion, whose type is "proton" or "wine"). A Proton prefix has the
Wine prefix in its pfx folder, like Steam's compatdata/<app id>/pfx; a plain Wine prefix is the folder itself.
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

GOG_ID = "1207659252"


def _config_dirs() -> list[Path]:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return [Path(appdata) / "heroic"] if appdata else []
    home = Path.home()
    return [home / ".config/heroic", home / ".var/app/com.heroicgameslauncher.hgl/config/heroic"]  # .deb, Flatpak


CONFIG_DIRS = _config_dirs()


@dataclass
class Install:
    game_dir: Path
    wine_prefix: Path | None  # None: Heroic didn't say (or runs the game without Wine, on Windows)
    proton: bool

    @property
    def user_reg(self) -> Path | None:
        if self.wine_prefix is None:
            return None
        return self.wine_prefix / "pfx" / "user.reg" if self.proton else self.wine_prefix / "user.reg"


def _json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def installs() -> list[Install]:
    """Tzar's GOG installs that Heroic knows about."""
    found = []
    for config in CONFIG_DIRS:
        data = _json(config / "gog_store" / "installed.json")
        entries = data.get("installed") if isinstance(data, dict) else None
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict) or str(entry.get("appName")) != GOG_ID:
                continue
            path = entry.get("install_path")
            if not isinstance(path, str) or not path:
                continue
            settings = _json(config / "GamesConfig" / f"{GOG_ID}.json")
            settings = settings.get(GOG_ID) if isinstance(settings, dict) else None
            settings = settings if isinstance(settings, dict) else {}
            prefix = settings.get("winePrefix")
            version = settings.get("wineVersion")
            proton = isinstance(version, dict) and version.get("type") == "proton"
            found.append(Install(Path(path), Path(prefix) if isinstance(prefix, str) and prefix else None, proton))
    return found


def find(game_dir: Path) -> Install | None:
    """The Heroic install in game_dir, if Heroic installed it."""
    try:
        wanted = game_dir.resolve()
    except OSError:
        return None
    for install in installs():
        try:
            if install.game_dir.resolve() == wanted:
                return install
        except OSError:
            continue
    return None
