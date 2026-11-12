"""tzar-widescreen: install or remove the widescreen mod.

Run it with no arguments (double-click on Windows) and it finds the game, says what it will do and asks first.
"""

import argparse
import sys
from pathlib import Path

from tzar_widescreen import __version__, game, install

ISSUES = "https://github.com/bruno-gelb/ttbotc_resolution_mod/issues"
LAUNCH_OPTIONS = 'WINEDLLOVERRIDES="ddraw=n,b" %command%'


def _ask(question: str, default: bool) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{question} {hint} ").strip().lower()
    except EOFError:
        return default
    return default if not answer else answer in ("y", "yes")


def _pick_game_dir(given: Path | None) -> Path:
    if given:
        if not game.is_game_dir(given):
            raise install.InstallError(f"{given} doesn't look like the Tzar folder (no {game.EXE} in it)")
        return given.resolve()
    found = game.find()
    if not found:
        raise install.InstallError(
            "couldn't find the game. Put this program in the Tzar folder and run it from there, "
            "or pass the folder: --game-dir \"<path to Tzar>\"")
    if len(found) == 1:
        return found[0]
    print("Found more than one Tzar folder:")
    for i, path in enumerate(found, 1):
        print(f"  {i}. {path}")
    while True:
        choice = input(f"Which one? [1-{len(found)}] ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(found):
            return found[int(choice) - 1]


def _after_install() -> None:
    print("\nDone. Start the game as usual. Keep the in-game layout with the panel on the left.")
    if sys.platform != "win32":
        print("\nOn Linux, the game runs through Proton and needs one more thing, once:")
        print("in Steam, right-click Tzar, Properties, General, and set Launch Options to:\n")
        print(f"    {LAUNCH_OPTIONS}\n")
        print("It tells Proton to use the mod's DirectDraw (cnc-ddraw) instead of its own.")


def _after_uninstall() -> None:
    print("\nDone: the game is back to how it was.")
    if sys.platform != "win32":
        print("You can clear Tzar's Launch Options in Steam now.")


def run(args: argparse.Namespace) -> int:
    print(f"Tzar widescreen mod {__version__}\n")
    game_dir = _pick_game_dir(args.game_dir)
    state = install.status(game_dir)
    print(f"Game folder: {game_dir}")
    if state.exe_error and not state.installed:
        raise install.InstallError(f"this version of the game isn't supported yet ({state.exe_error}). "
                                   f"Please tell us about it: {ISSUES}")
    print(f"Mod: {'installed (version ' + str(state.version) + ')' if state.installed else 'not installed'}\n")

    command = args.command
    if command == "status":
        if state.exe:
            print(f"Tzar_.exe: {state.exe.width}x{state.exe.height}, "
                  f"{state.exe.patched} of {state.exe.total} fixes applied")
        return 0
    if command is None:
        reverted = state.exe is not None and (state.exe.patched < state.exe.total or
                                              (state.exe.width, state.exe.height) != (install.WIDTH, install.HEIGHT))
        if state.installed and reverted:
            print("The mod is installed, but the game's files were put back, probably by a Steam update.")
            if _ask("Apply the mod again?", default=True):
                command = "install"
            elif _ask("Remove the mod completely instead?", default=False):
                command = "uninstall"
            else:
                return 0
        elif state.installed:
            print("Remove the mod and put the game's original files back?")
            if not _ask("Remove it?", default=False):
                return 0
            command = "uninstall"
        else:
            print(f"This will make the game run at {install.WIDTH}x{install.HEIGHT} (21:9), scaled to your screen.")
            print(f"It changes a few of the game's files and keeps the originals in {install.BACKUP_DIR}/,")
            print("so running this program again can remove the mod.\n")
            if not _ask("Install the mod?", default=True):
                return 0
            command = "install"
    elif not args.yes:
        question = "Install the mod?" if command == "install" else "Remove the mod?"
        if not _ask(question, default=True):
            return 0

    if command == "install":
        install.install(game_dir, log=lambda line: print(f"  {line}"))
        _after_install()
    else:
        install.uninstall(game_dir, log=lambda line: print(f"  {line}"))
        _after_uninstall()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="tzar-widescreen", description="Widescreen mod for Tzar: The Burden of "
                                     "the Crown. With no command, it asks what to do.")
    parser.add_argument("command", nargs="?", choices=["install", "uninstall", "status"])
    parser.add_argument("--game-dir", type=Path, help="the Tzar folder, if it isn't found on its own")
    parser.add_argument("--yes", "-y", action="store_true", help="don't ask for confirmation")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()
    # Started by double-click on Windows: keep the window open at the end so the result can be read.
    pause = sys.platform == "win32" and len(sys.argv) == 1
    try:
        code = run(args)
    except install.InstallError as error:
        print(f"\nCan't continue: {error}")
        code = 1
    except KeyboardInterrupt:
        print("\nStopped.")
        code = 1
    if pause:
        input("\nPress Enter to close this window.")
    sys.exit(code)
