"""Install and uninstall the mod in a game folder.

Before changing anything, the original files are copied to tzar-widescreen-backup/ in the game folder, with a
manifest of what was done, so uninstalling restores the game exactly. Installing again (for example after Steam
reverted the exe in an update) works from those backups.
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from tzar_widescreen import __version__, cnc_ddraw, exe_patch, frame, ini
from tzar_widescreen.game import resolve

WIDTH, HEIGHT = 1832, 768
LAYOUT = "LAYOUT1024L"
VIEW = f"150,30,{WIDTH - 150},{HEIGHT - 30}"  # the map view, right of the 150 px panel and below the 30 px top bar

BACKUP_DIR = "tzar-widescreen-backup"
MANIFEST = "manifest.json"
EXE = "Tzar_.exe"
TZAR_INI = "tzar.ini"
LAYOUT_INI = "DATA/LAYOUT.INI"
FRAME = "IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP"
BACKED_UP = [EXE, LAYOUT_INI, FRAME]
# tzar.ini also holds the player's settings, so only these keys are changed, and put back on uninstall.
TZAR_INI_KEYS = [
    ("DEFAULTS", "LAYOUT", LAYOUT),
    ("VIDEO", "DIRECTXDEVICE", "0"),             # DirectDraw (cnc-ddraw) instead of GDI
    ("VIDEO", "DIRECTDRAW_DEVICESNUMBER", "2"),  # what the game expects when cnc-ddraw reports its one device
]


class InstallError(Exception):
    pass


@dataclass
class Status:
    installed: bool
    version: str | None
    exe: exe_patch.ExeState | None
    exe_error: str | None


def _backup(game_dir: Path) -> Path:
    return game_dir / BACKUP_DIR


def _manifest(game_dir: Path) -> dict | None:
    try:
        return json.loads((_backup(game_dir) / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def status(game_dir: Path) -> Status:
    manifest = _manifest(game_dir)
    try:
        exe = exe_patch.inspect(resolve(game_dir, EXE).read_bytes())
        error = None
    except (OSError, exe_patch.UnknownExe) as e:
        exe, error = None, str(e)
    return Status(manifest is not None, manifest.get("version") if manifest else None, exe, error)


def _write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tzar-widescreen-tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def install(game_dir: Path, log=print) -> None:
    if not cnc_ddraw.available():
        raise InstallError("cnc-ddraw's files are missing from this build of the mod")
    paths = {rel: resolve(game_dir, rel) for rel in [EXE, TZAR_INI, LAYOUT_INI, FRAME]}
    missing = [rel for rel, path in paths.items() if not path.is_file()]
    if missing:
        raise InstallError(f"not a complete Tzar folder, missing: {', '.join(missing)}")
    try:
        exe_patch.inspect(paths[EXE].read_bytes())
    except exe_patch.UnknownExe as e:
        raise InstallError(f"this version of the game isn't supported yet ({e})") from e

    backup = _backup(game_dir)
    manifest = _manifest(game_dir)
    if manifest is None:
        if frame.size(paths[FRAME].read_bytes())[0] != 1024:
            raise InstallError("the game's files were already changed by something else. Restore them first "
                               "(in Steam: Properties, Installed Files, Verify integrity of game files)")
        log(f"Backing up the original files to {backup.name}/")
        backup.mkdir(exist_ok=True)
        for rel in BACKED_UP:
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            data = paths[rel].read_bytes()
            if rel == EXE:
                data = exe_patch.original(data)  # in case it was patched by hand before
            dst.write_bytes(data)
        tzar_ini = ini.read(paths[TZAR_INI])
        manifest = {
            "version": __version__,
            "tzar_ini": {f"{s}/{k}": ini.get_key(tzar_ini, s, k) for s, k, _ in TZAR_INI_KEYS},
            "moved_aside": [],
        }
        for name in cnc_ddraw.FILES:  # someone else's ddraw.dll and the like: keep them to put back later
            existing = game_dir / name
            if existing.exists():
                shutil.move(existing, backup / name)
                manifest["moved_aside"].append(name)

    log(f"Patching {EXE}")
    _write(paths[EXE], exe_patch.apply((backup / EXE).read_bytes(), WIDTH, HEIGHT))
    log(f"Widening the map view in {LAYOUT_INI}")
    layout = ini.set_key(ini.read(backup / LAYOUT_INI), LAYOUT, "view", VIEW)
    _write(paths[LAYOUT_INI], layout.encode("latin-1"))
    log("Widening the frame around the map")
    _write(paths[FRAME], frame.widen((backup / FRAME).read_bytes(), WIDTH))
    log(f"Updating {TZAR_INI}")
    text = ini.read(paths[TZAR_INI])
    for section, key, value in TZAR_INI_KEYS:
        text = ini.set_key(text, section, key, value)
    _write(paths[TZAR_INI], text.encode("latin-1"))
    log("Installing cnc-ddraw")
    cnc_ddraw.install(game_dir, WIDTH, HEIGHT)

    manifest["version"] = __version__
    (backup / MANIFEST).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def uninstall(game_dir: Path, log=print) -> None:
    backup = _backup(game_dir)
    manifest = _manifest(game_dir)
    if manifest is None:
        raise InstallError("the mod isn't installed here (no backup folder found)")
    for rel in BACKED_UP:
        log(f"Restoring {rel}")
        _write(resolve(game_dir, rel), (backup / rel).read_bytes())
    tzar_ini = resolve(game_dir, TZAR_INI)
    if tzar_ini.is_file():
        log(f"Restoring the settings the mod changed in {TZAR_INI}")
        text = ini.read(tzar_ini)
        for section, key, _ in TZAR_INI_KEYS:
            old = manifest.get("tzar_ini", {}).get(f"{section}/{key}")
            if old is not None:
                text = ini.set_key(text, section, key, old)
        _write(tzar_ini, text.encode("latin-1"))
    log("Removing cnc-ddraw")
    for name in cnc_ddraw.FILES:
        path = game_dir / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for name in manifest.get("moved_aside", []):
        shutil.move(backup / name, game_dir / name)
    shutil.rmtree(backup)
