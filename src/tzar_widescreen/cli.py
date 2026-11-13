"""tzar-widescreen: install the widescreen mod, change its resolution, or remove it.

Run it with no arguments (double-click on Windows) and it finds the game, asks what to do and asks before changing
anything.
"""

import sys
from pathlib import Path

import click

from tzar_widescreen import __version__, game, install, resolutions

ISSUES = "https://github.com/bruno-gelb/ttbotc_resolution_mod/issues"
WIDTH = click.IntRange(resolutions.MIN_WIDTH, resolutions.MAX_WIDTH)
HEIGHT = resolutions.HEIGHT

width_option = click.option(
    "--width", type=WIDTH,
    help=f"The game's width in pixels, {resolutions.MIN_WIDTH} to {resolutions.MAX_WIDTH}; the height stays {HEIGHT}. "
         "Default: your screen's shape.")
game_dir_option = click.option(
    "--game-dir", type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="The Tzar folder, if it isn't found on its own.")
yes_option = click.option("--yes", "-y", is_flag=True, help="Don't ask anything.")


def _menu(title: str, options: list[str], default: int = 1) -> int:
    """A numbered choice; Enter picks the default. Returns it 1-based."""
    click.echo(title)
    for i, option in enumerate(options, 1):
        click.echo(f"  {i}. {option}")
    return click.prompt("Choose", type=click.IntRange(1, len(options)), default=default)


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
    click.echo(note)
    click.echo(f"The height stays {HEIGHT}; the width sets the shape. The picture is scaled to fill your screen.")
    options = [f"{w}x{HEIGHT} ({label})" + (" (now)" if w == current else "") for w, label in choices]
    options.append(f"another width, from {resolutions.MIN_WIDTH} to {resolutions.MAX_WIDTH}")
    picked = _menu("Which resolution?", options)
    if picked <= len(choices):
        return choices[picked - 1][0]
    return click.prompt("Width", type=WIDTH)


def _default_width() -> int:
    screen = resolutions.detect_screen()
    return resolutions.for_screen(*screen) if screen else resolutions.DEFAULT_WIDTH


def _open_game(game_dir: Path | None) -> tuple[Path, install.Status]:
    click.echo(f"Tzar widescreen mod {__version__}\n")
    path = _pick_game_dir(game_dir)
    state = install.status(path)
    click.echo(f"Game folder: {path}")
    if state.exe_error and not state.installed:
        raise install.InstallError(f"this version of the game isn't supported yet ({state.exe_error}). "
                                   f"Please tell us about it: {ISSUES}")
    if state.installed:
        size = f", {state.width}x{HEIGHT}" if state.width else ""
        click.echo(f"Mod: installed (version {state.version}{size})\n")
    else:
        click.echo("Mod: not installed\n")
    return path, state


def _do_install(path: Path, width: int) -> None:
    ready = install.install(path, width, log=lambda line: click.echo(f"  {line}"))
    if not ready:
        click.echo(f"\nAlmost done: the game's files are set for {width}x{HEIGHT}, but Proton hasn't set the game up")
        click.echo("yet, so it would still use its own DirectDraw. Start Tzar once from Steam, quit it, and run this")
        click.echo("program again.")
        return
    click.echo(f"\nDone: the game runs at {width}x{HEIGHT}. Start it as usual.")
    click.echo("Keep the game's Menu Layout with the panel on the left: the other two don't work with the mod yet.")
    click.echo("To change the resolution or remove the mod, run this program again.")


def _do_uninstall(path: Path) -> None:
    install.uninstall(path, log=lambda line: click.echo(f"  {line}"))
    click.echo("\nDone: the game is back to how it was.")


def _interactive(path: Path, state: install.Status) -> None:
    exe = state.exe
    reverted = exe is not None and (exe.patched < exe.total or exe.width == 1024)
    if state.installed and (reverted or state.proton_missing):
        if reverted:
            click.echo("The mod is installed, but the game's files were put back, probably by a Steam update.\n")
        else:
            click.echo("The mod is installed, but Tzar's Proton prefix doesn't have its setting yet.\n")
        picked = _menu("What now?", ["apply the mod again", "change the resolution and apply it",
                                     "remove the mod", "nothing"])
        if picked == 1:
            _do_install(path, state.width or resolutions.DEFAULT_WIDTH)
        elif picked == 2:
            _do_install(path, _choose_width(state.width))
        elif picked == 3:
            _do_uninstall(path)
        return
    if state.installed:
        picked = _menu("What now?", ["change the resolution", "remove the mod and put the original files back",
                                     "nothing"], default=3)
        if picked == 1:
            click.echo()
            _do_install(path, _choose_width(state.width))
        elif picked == 2:
            _do_uninstall(path)
        return
    click.echo("This makes the game run at a widescreen resolution, scaled to your screen. It changes a few of the")
    click.echo(f"game's files and keeps the originals in {install.BACKUP_DIR}/, so running this program again")
    click.echo("can change the resolution or remove the mod.\n")
    width = _choose_width()
    click.echo()
    if click.confirm(f"Install the mod at {width}x{HEIGHT}?", default=True):
        _do_install(path, width)


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@width_option
@game_dir_option
@yes_option
@click.version_option(__version__, prog_name="tzar-widescreen")
@click.pass_context
def cli(ctx: click.Context, width: int | None, game_dir: Path | None, yes: bool) -> None:
    """Widescreen mod for Tzar: The Burden of the Crown.

    With no command, it finds the game and asks what to do. --width alone installs at that width.
    """
    ctx.obj = {"game_dir": game_dir, "yes": yes}
    if ctx.invoked_subcommand is not None:
        return
    if width is not None:
        ctx.invoke(install_command, width=width, game_dir=game_dir, yes=yes)
        return
    _interactive(*_open_game(game_dir))


@cli.command("install")
@width_option
@game_dir_option
@yes_option
@click.pass_context
def install_command(ctx: click.Context, width: int | None, game_dir: Path | None, yes: bool) -> None:
    """Install the mod, or change the resolution of an installed one."""
    yes = yes or ctx.obj["yes"]
    path, state = _open_game(game_dir or ctx.obj["game_dir"])
    if width is None:
        width = _default_width() if yes else _choose_width(state.width)
    if yes or click.confirm(f"Install the mod at {width}x{HEIGHT}?", default=True):
        _do_install(path, width)


@cli.command("uninstall")
@game_dir_option
@yes_option
@click.pass_context
def uninstall_command(ctx: click.Context, game_dir: Path | None, yes: bool) -> None:
    """Remove the mod and put the game's original files back."""
    path, _ = _open_game(game_dir or ctx.obj["game_dir"])
    if yes or ctx.obj["yes"] or click.confirm("Remove the mod?", default=True):
        _do_uninstall(path)


@cli.command("status")
@game_dir_option
@click.pass_context
def status_command(ctx: click.Context, game_dir: Path | None) -> None:
    """Show what's installed, without changing anything."""
    _, state = _open_game(game_dir or ctx.obj["game_dir"])
    if state.exe:
        click.echo(f"Tzar_.exe: {state.exe.width}x{state.exe.height}, "
                   f"{state.exe.patched} of {state.exe.total} fixes applied")


def main() -> None:
    # Started by double-click on Windows: keep the window open at the end so the result can be read.
    pause = sys.platform == "win32" and len(sys.argv) == 1
    try:
        code = cli.main(prog_name="tzar-widescreen", standalone_mode=False)
        code = code if isinstance(code, int) else 0
    except click.exceptions.Abort:
        click.echo("\nStopped.")
        code = 1
    except click.ClickException as error:
        error.show()
        code = error.exit_code
    except install.InstallError as error:
        click.echo(f"\nCan't continue: {error}")
        code = 1
    if pause:
        click.pause("\nPress any key to close this window.")
    sys.exit(code)
