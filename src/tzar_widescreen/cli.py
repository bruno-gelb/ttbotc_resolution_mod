"""tzar-widescreen: install the widescreen mod, change its resolution, or remove it.

Run it with no arguments (double-click on Windows) and it finds the game, asks what to do and asks before changing
anything.
"""

import argparse
import sys
from pathlib import Path

from tzar_widescreen import __version__, game, install, resolutions

ISSUES = "https://github.com/bruno-gelb/ttbotc_resolution_mod/issues"
LAUNCH_OPTIONS = 'WINEDLLOVERRIDES="ddraw=n,b" %command%'


def _input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def _ask(question: str, default: bool) -> bool:
    answer = _input(f"{question} {'[Y/n]' if default else '[y/N]'} ").lower()
    return default if not answer else answer in ("y", "yes")


def _menu(title: str, options: list[str], default: int = 1) -> int:
    """Numbered choice; Enter picks the default. Returns 1-based."""
    print(title)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    while True:
        answer = _input(f"Choose 1-{len(options)} [{default}]: ")
        if not answer:
            return default
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer)


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
    return found[_menu("Found more than one Tzar folder:", [str(p) for p in found]) - 1]


def _resolution_choices() -> tuple[list[tuple[int, str]], str]:
    """Widths to offer, the first one being the default, and a line about the screen."""
    screen = resolutions.detect_screen()
    choices = []
    if screen:
        width = resolutions.for_screen(*screen)
        note = f"Your screen: {screen[0]}x{screen[1]}."
        if width == resolutions.MIN_WIDTH and screen[0] / screen[1] <= 4 / 3:
            note += " It's 4:3 or narrower, so the original game already fits it; the mod won't add much."
        elif width == resolutions.MAX_WIDTH:
            note += f" It's wider than the mod can go, so {width} px is the widest; expect bars above and below."
        preset = next((label for w, label in resolutions.PRESETS if w == width), None)
        choices.append((width, f"matches your screen: {preset}" if preset else "matches your screen"))
    else:
        note = "Couldn't tell your screen's size."
    for width, label in resolutions.PRESETS:
        if all(width != w for w, _ in choices):
            choices.append((width, label))
    if not screen:
        choices.sort(key=lambda c: c[0] != 1368)  # 16:9, the most common screen shape, first
    return choices, note


def _choose_width(current: int | None = None) -> int:
    choices, note = _resolution_choices()
    print(note)
    print(f"The height stays {resolutions.HEIGHT}; the width sets the shape. "
          "The picture is scaled to fill your screen.")
    options = [f"{w}x{resolutions.HEIGHT} ({label})" + (" (now)" if w == current else "") for w, label in choices]
    options.append(f"another width, from {resolutions.MIN_WIDTH} to {resolutions.MAX_WIDTH}")
    picked = _menu("Which resolution?", options)
    if picked <= len(choices):
        return choices[picked - 1][0]
    while True:
        answer = _input("Width: ")
        try:
            return resolutions.check(int(answer))
        except ValueError as error:
            print(f"  {error}" if isinstance(error, resolutions.BadWidth) else "  a number, please")


def _default_width() -> int:
    screen = resolutions.detect_screen()
    return resolutions.for_screen(*screen) if screen else resolutions.DEFAULT_WIDTH


def _after_install(width: int) -> None:
    print(f"\nDone: the game runs at {width}x{resolutions.HEIGHT}. Start it as usual.")
    print("Keep the game's Menu Layout with the panel on the left: the other two don't work with the mod yet.")
    print("To change the resolution or remove the mod, run this program again.")
    if sys.platform != "win32":
        print("\nOn Linux, the game runs through Proton and needs one more thing, once:")
        print("in Steam, right-click Tzar, Properties, General, and set Launch Options to:\n")
        print(f"    {LAUNCH_OPTIONS}\n")
        print("It tells Proton to use the mod's DirectDraw (cnc-ddraw) instead of its own.")


def _after_uninstall() -> None:
    print("\nDone: the game is back to how it was.")
    if sys.platform != "win32":
        print("You can clear Tzar's Launch Options in Steam now.")


def _interactive(state: install.Status) -> tuple[str | None, int | None]:
    """Ask what to do. Returns (command, width), command None to do nothing."""
    exe = state.exe
    reverted = exe is not None and (exe.patched < exe.total or exe.width == 1024)
    if state.installed and reverted:
        print("The mod is installed, but the game's files were put back, probably by a Steam update.\n")
        picked = _menu("What now?", ["apply the mod again", "change the resolution and apply it",
                                     "remove the mod", "nothing"])
        if picked == 1:
            return "install", state.width or resolutions.DEFAULT_WIDTH
        if picked == 2:
            return "install", _choose_width(state.width)
        return ("uninstall", None) if picked == 3 else (None, None)
    if state.installed:
        picked = _menu("What now?", ["change the resolution", "remove the mod and put the original files back",
                                     "nothing"], default=3)
        if picked == 1:
            print()
            return "install", _choose_width(state.width)
        return ("uninstall", None) if picked == 2 else (None, None)
    print("This makes the game run at a widescreen resolution, scaled to your screen. It changes a few of the")
    print(f"game's files and keeps the originals in {install.BACKUP_DIR}/, so running this program again")
    print("can change the resolution or remove the mod.\n")
    width = _choose_width()
    print()
    return ("install", width) if _ask(f"Install the mod at {width}x{resolutions.HEIGHT}?", default=True) \
        else (None, None)


def run(args: argparse.Namespace) -> int:
    print(f"Tzar widescreen mod {__version__}\n")
    game_dir = _pick_game_dir(args.game_dir)
    state = install.status(game_dir)
    print(f"Game folder: {game_dir}")
    if state.exe_error and not state.installed:
        raise install.InstallError(f"this version of the game isn't supported yet ({state.exe_error}). "
                                   f"Please tell us about it: {ISSUES}")
    if state.installed:
        size = f", {state.width}x{resolutions.HEIGHT}" if state.width else ""
        print(f"Mod: installed (version {state.version}{size})\n")
    else:
        print("Mod: not installed\n")

    command, width = args.command, args.width
    if command == "status":
        if state.exe:
            print(f"Tzar_.exe: {state.exe.width}x{state.exe.height}, "
                  f"{state.exe.patched} of {state.exe.total} fixes applied")
        return 0
    if command is None:
        command, width = _interactive(state)
        if command is None:
            return 0
    elif command == "install":
        if width is None:
            width = _default_width() if args.yes else _choose_width(state.width)
        if not args.yes and not _ask(f"Install the mod at {width}x{resolutions.HEIGHT}?", default=True):
            return 0
    elif not args.yes and not _ask("Remove the mod?", default=True):
        return 0

    if command == "install":
        install.install(game_dir, width, log=lambda line: print(f"  {line}"))
        _after_install(width)
    else:
        install.uninstall(game_dir, log=lambda line: print(f"  {line}"))
        _after_uninstall()
    return 0


def _width(value: str) -> int:
    try:
        return resolutions.check(int(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error) if isinstance(error, resolutions.BadWidth) else
                                         "the width must be a number") from error


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tzar-widescreen",
        description="Widescreen mod for Tzar: The Burden of the Crown. With no command, it asks what to do.")
    parser.add_argument("command", nargs="?", choices=["install", "uninstall", "status"],
                        help="install also changes the resolution of an installed mod")
    parser.add_argument("--width", type=_width,
                        help=f"the game's width in pixels, {resolutions.MIN_WIDTH} to {resolutions.MAX_WIDTH} "
                             f"(the height stays {resolutions.HEIGHT}). Default: your screen's shape")
    parser.add_argument("--game-dir", type=Path, help="the Tzar folder, if it isn't found on its own")
    parser.add_argument("--yes", "-y", action="store_true", help="don't ask anything")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()
    if args.width is not None and args.command is None:
        args.command = "install"
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
