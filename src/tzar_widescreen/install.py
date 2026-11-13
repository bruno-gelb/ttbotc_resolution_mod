"""Install and uninstall the mod in a game folder.

Before changing anything, the original files are copied to tzar-widescreen-backup/ in the game folder, with a
manifest of what was done, so uninstalling restores the game exactly. Installing again (for example after Steam
reverted the exe in an update) works from those backups.
"""

import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from tzar_widescreen import __version__, cnc_ddraw, exe_patch, frame, game, ini, music, proton, resolutions
from tzar_widescreen.game import resolve
from tzar_widescreen.manifest import DamagedManifest, Manifest

HEIGHT = resolutions.HEIGHT
LAYOUT = "LAYOUT1024L"

BACKUP_DIR = "tzar-widescreen-backup"
TZAR_INI = "tzar.ini"
LAYOUT_INI = "DATA/LAYOUT.INI"
FRAME = "IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP"
# Backed up next to the game's exe, which is Tzar_.exe on Steam and Tzar.exe on GOG (see game.py). Everything else
# is the same for both: GOG ships the same files.
BACKED_UP = [LAYOUT_INI, FRAME]
# The main menu shows "<[general] version> <the game's version>" in its bottom-right corner, "Version 1.10, 2/03/2002":
# the mod puts its own name and version in front. No "|" in it: the game reads "text| hint" and shows only the text.
# Unlike the files above, it's optional, since a copy of the game could lack it. Versions before 0.4.0 didn't change
# it, so their backups don't have it: then it's still the original.
STRINGS_INI = "LOCAL/STRINGS.INI"
MENU_LABEL = "ttbotc_resolution_mod {version}. game {original}"
LABELLED = re.compile(r"ttbotc_resolution_mod \S+\. game (.*)")
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
    width: int | None  # what the mod was installed with
    exe: exe_patch.ExeState | None
    exe_error: str | None
    exe_name: str | None = None  # Tzar_.exe (Steam) or Tzar.exe (GOG)
    # Linux: installed, but the ddraw override isn't in Tzar's Proton prefix (it didn't exist yet, or was recreated).
    proton_missing: bool = False


def _backup(game_dir: Path) -> Path:
    return game_dir / BACKUP_DIR


def _manifest(game_dir: Path) -> Manifest | None:
    try:
        return Manifest.load(_backup(game_dir))
    except DamagedManifest as error:
        raise InstallError(f"the mod's backup record is damaged: {error}. The original files are still in "
                           f"{BACKUP_DIR}/; restore them by hand, or have Steam or Heroic verify the game's files "
                           f"and delete that folder") from error


def _exe_name(game_dir: Path, manifest: Manifest | None) -> str | None:
    return manifest.exe if manifest else game.exe_name(game_dir)


def _user_reg(game_dir: Path, manifest: Manifest | None) -> Path | None:
    """The user.reg the override goes into: the one the mod already set it in, or the launcher's prefix."""
    if manifest is not None and manifest.proton_user_reg:
        return Path(manifest.proton_user_reg)
    prefix = proton.find_prefix(game_dir)
    return prefix.user_reg if prefix else None


def status(game_dir: Path) -> Status:
    manifest = _manifest(game_dir)
    name = _exe_name(game_dir, manifest)
    try:
        if name is None:
            raise OSError(f"no {' or '.join(game.EXES)} here")
        exe = exe_patch.inspect(resolve(game_dir, name).read_bytes())
        error = None
    except (OSError, exe_patch.UnknownExe) as e:
        exe, error = None, str(e)
    proton_missing = False
    if manifest is not None and proton.ENABLED:
        reg = _user_reg(game_dir, manifest)
        if reg is not None:  # None: a launcher the mod doesn't know, so it can't tell
            proton_missing = not reg.is_file() or proton.current(proton.read(reg), manifest.exe) != proton.VALUE
    return Status(manifest is not None, manifest.version if manifest else None,
                  manifest.width if manifest else None, exe, error, name, proton_missing)


def _write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tzar-widescreen-tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _view(width: int) -> str:
    """The map view in LAYOUT.INI: right of the 150 px panel, below the 30 px top bar."""
    return f"150,30,{width - 150},{HEIGHT - 30}"


def _check_not_running() -> None:
    if proton.ENABLED and proton.game_running():
        raise InstallError("Tzar is running: quit the game first")


def _set_proton_override(game_dir: Path, manifest: Manifest, log) -> bool:
    """Set the ddraw override in the prefix that runs the game (Steam's or Heroic's). False if the prefix isn't
    there yet: the launcher creates it when the game first starts."""
    reg = _user_reg(game_dir, manifest)
    if reg is None:
        log("Couldn't tell which Wine prefix runs the game, so Wine may still use its own DirectDraw. If the game "
            'doesn\'t fill the screen, add WINEDLLOVERRIDES="ddraw=n,b" to its launch options')
        return True
    if not reg.is_file():
        return False
    text = proton.read(reg)
    found = proton.current(text, manifest.exe)
    if found != proton.VALUE:  # when it's set already, it's from an earlier install, or the player set it
        log("Telling Wine to use cnc-ddraw, in the game's Wine prefix")
        if not manifest.proton_override:
            manifest.proton_override, manifest.proton_previous = True, found
        _write(reg, proton.add(text, int(time.time()), manifest.exe).encode("latin-1"))
    if manifest.proton_override:
        manifest.proton_user_reg = str(reg)  # also for installs from before 0.5.0, which didn't record it
    return True


def _label_main_menu(game_dir: Path, backup: Path, log) -> None:
    path = resolve(game_dir, STRINGS_INI)
    if not path.is_file():
        return
    saved = backup / STRINGS_INI
    if not saved.is_file():
        text = ini.read(path)
        current = ini.get_key(text, "general", "version")
        label = LABELLED.fullmatch(current or "")
        if label:  # left over from a mod version that didn't put it back: keep what the game had
            text = ini.set_key(text, "general", "version", label.group(1))
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(text.encode("latin-1"))
    text = ini.read(saved)
    original = ini.get_key(text, "general", "version")
    if original is None:
        return
    log("Adding the mod's version to the main menu")
    text = ini.set_key(text, "general", "version", MENU_LABEL.format(version=__version__, original=original))
    _write(path, text.encode("latin-1"))


def install(game_dir: Path, width: int = resolutions.DEFAULT_WIDTH, log=print) -> bool:
    """Install the mod, or change its width. On Linux, False if the launcher still needs to start the game once first,
    to create its Wine prefix."""
    resolutions.check(width)
    _check_not_running()
    if not cnc_ddraw.available():
        raise InstallError("cnc-ddraw's files are missing from this build of the mod")
    if music.ENABLED and not music.available():
        raise InstallError("the music files are missing from this build of the mod")
    backup = _backup(game_dir)
    manifest = _manifest(game_dir)
    exe = _exe_name(game_dir, manifest) or game.EXES[0]
    paths = {rel: resolve(game_dir, rel) for rel in [exe, TZAR_INI, LAYOUT_INI, FRAME]}
    missing = [rel for rel, path in paths.items() if not path.is_file()]
    if missing:
        if exe in missing:
            missing[missing.index(exe)] = " or ".join(game.EXES)
        raise InstallError(f"not a complete Tzar folder, missing: {', '.join(missing)}")
    try:
        exe_patch.inspect(paths[exe].read_bytes())
    except exe_patch.UnknownExe as e:
        raise InstallError(f"this version of the game isn't supported yet ({e})") from e

    if manifest is None:
        if frame.size(paths[FRAME].read_bytes())[0] != 1024:
            raise InstallError("the game's files were already changed by something else. Restore them first "
                               "(in Steam: Properties, Installed Files, Verify integrity of game files; in Heroic: "
                               "the game's Verify and Repair)")
        log(f"Backing up the original files to {backup.name}/")
        backup.mkdir(exist_ok=True)
        for rel in [exe, *BACKED_UP]:
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            data = paths[rel].read_bytes()
            if rel == exe:
                data = exe_patch.original(data)  # in case it was patched by hand before
            dst.write_bytes(data)
        tzar_ini = ini.read(paths[TZAR_INI])
        manifest = Manifest(
            version=__version__,
            exe=exe,
            width=width,
            tzar_ini={f"{s}/{k}": ini.get_key(tzar_ini, s, k) for s, k, _ in TZAR_INI_KEYS},
        )
        for name in cnc_ddraw.FILES:  # someone else's ddraw.dll and the like: keep them to put back later
            existing = game_dir / name
            if existing.exists():
                shutil.move(existing, backup / name)
                manifest.moved_aside.append(name)

    log(f"Patching {exe}")
    _write(paths[exe], exe_patch.apply((backup / exe).read_bytes(), width, HEIGHT, music=music.ENABLED))
    log(f"Widening the map view in {LAYOUT_INI}")
    layout = ini.set_key(ini.read(backup / LAYOUT_INI), LAYOUT, "view", _view(width))
    _write(paths[LAYOUT_INI], layout.encode("latin-1"))
    log("Widening the frame around the map")
    _write(paths[FRAME], frame.widen((backup / FRAME).read_bytes(), width))
    log(f"Updating {TZAR_INI}")
    text = ini.read(paths[TZAR_INI])
    for section, key, value in TZAR_INI_KEYS:
        text = ini.set_key(text, section, key, value)
    _write(paths[TZAR_INI], text.encode("latin-1"))
    _label_main_menu(game_dir, backup, log)
    log("Installing cnc-ddraw")
    cnc_ddraw.install(game_dir, width, HEIGHT, exe)
    if music.ENABLED:
        log("Adding a MIDI synthesizer for the game's music, which Wine doesn't have")
        music.install(game_dir)
    ready = _set_proton_override(game_dir, manifest, log) if proton.ENABLED else True

    manifest.version = __version__
    manifest.width = width
    manifest.save(backup)
    return ready


def uninstall(game_dir: Path, log=print) -> None:
    backup = _backup(game_dir)
    manifest = _manifest(game_dir)
    if manifest is None:
        raise InstallError("the mod isn't installed here (no backup folder found)")
    _check_not_running()
    for rel in [manifest.exe, *BACKED_UP]:
        log(f"Restoring {rel}")
        _write(resolve(game_dir, rel), (backup / rel).read_bytes())
    if (backup / STRINGS_INI).is_file():
        log(f"Restoring {STRINGS_INI}")
        _write(resolve(game_dir, STRINGS_INI), (backup / STRINGS_INI).read_bytes())
    tzar_ini = resolve(game_dir, TZAR_INI)
    if tzar_ini.is_file():
        log(f"Restoring the settings the mod changed in {TZAR_INI}")
        text = ini.read(tzar_ini)
        for section, key, _ in TZAR_INI_KEYS:
            old = manifest.tzar_ini.get(f"{section}/{key}")
            if old is not None:
                text = ini.set_key(text, section, key, old)
        _write(tzar_ini, text.encode("latin-1"))
    log("Removing cnc-ddraw" + (" and the music synthesizer" if (game_dir / music.FILES[0]).exists() else ""))
    for name in cnc_ddraw.FILES + music.FILES:
        path = game_dir / name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for name in manifest.moved_aside:
        shutil.move(backup / name, game_dir / name)
    reg = _user_reg(game_dir, manifest) if manifest.proton_override else None
    if reg is not None and reg.is_file():
        log("Removing the override from the game's Wine prefix")
        _write(reg, proton.remove(proton.read(reg), manifest.proton_previous, manifest.exe).encode("latin-1"))
    shutil.rmtree(backup)
