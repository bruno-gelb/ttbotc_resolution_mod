"""A link that opens a new GitHub issue with the details of a failure already filled in.

Nothing is sent anywhere: the player opens the link, reads what's in it and submits the issue, or doesn't. Paths
lose the user's name, the only personal detail in them.
"""

import hashlib
import platform
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode

import pefile

from tzar_widescreen import __version__, game

ISSUES = "https://github.com/bruno-gelb/ttbotc_resolution_mod/issues"
# GitHub fails on long issue links (checked 2026-11-17): the issue form from about 7,000 characters (500), and for a
# player who isn't signed in, its sign-in page, which encodes the whole link into its own a second time, from about
# 5,000 (414). Long tracebacks lose their first lines to fit.
MAX_URL = 4500

# The game folder the failure happened in, once the program knows it.
game_dir: Path | None = None


def scrub(text: str) -> str:
    """The text without the user's name: the home folder becomes ~, and other users' folders lose their names."""
    home = str(Path.home())
    if len(home) > 3:  # not "/" or "C:\"
        text = text.replace(home, "~")
    text = re.sub(r"(?i)\b([a-z]:[\\/]+(?:users|documents and settings)[\\/]+)[^\\/\s\"']+", r"\1<user>", text)
    return re.sub(r"/(?:home|Users)/[^/\s\"']+", "~", text)


def _exe(folder: Path) -> str | None:
    """The game's exe: name, size, SHA-256 and PE timestamp, enough to tell one build from another."""
    name = game.exe_name(folder)
    if name is None:
        return None
    data = game.resolve(folder, name).read_bytes()
    try:
        timestamp = pefile.PE(data=data, fast_load=True).FILE_HEADER.TimeDateStamp
    except pefile.PEFormatError:
        timestamp = "not a PE file"
    return f"{name}, {len(data):,} bytes, SHA-256 {hashlib.sha256(data).hexdigest()}, PE timestamp {timestamp}"


def facts() -> list[str]:
    """What the report says about the mod, the system and the game, one line each."""
    build = "release program" if getattr(sys, "frozen", False) else "from source"
    lines = [f"Mod: {__version__} ({build})", f"System: {platform.platform()}"]
    if game_dir is not None:
        lines.append(f"Game folder: {scrub(str(game_dir))}")
        try:
            exe = _exe(game_dir)
        except OSError as error:
            exe = f"can't read it ({error})"
        if exe:
            lines.append(f"Game exe: {scrub(exe)}")
    return lines


def _url(title: str, body: str) -> str:
    return f"{ISSUES}/new?" + urlencode({"title": title, "body": body}, quote_via=quote)


def issue_url(message: str, traceback: str | None = None) -> str:
    """A new issue for this failure. message is what the player saw; traceback, if there is one, goes under it."""
    message = scrub(message)
    first = message.splitlines()[0] if message else "error"
    title = f"Installer: {first}"
    if len(title) > 100:
        title = title[:99] + "…"

    details = "\n".join(f"- {line}" for line in facts())

    def body(trace: str | None) -> str:
        text = ("## Impact\n\n<!-- Optional: how much this stops you from playing. -->\n\n"
                f"## Details\n\n<!-- Optional: what you were doing. -->\n\nThe installer stopped with:\n\n"
                f"```\n{message}\n```\n\n{details}\n")
        if trace:
            text += f"\n<details><summary>Traceback</summary>\n\n```\n{trace}\n```\n\n</details>\n"
        return text

    if traceback is None:
        return _url(title, body(None))
    # The last frames and the error matter most: cut whole frames after the "Traceback" line until it fits.
    lines = scrub(traceback).rstrip().splitlines()
    cut = 1  # lines[1:cut] are left out
    while True:
        shown = lines if cut == 1 else [lines[0], "  ...", *lines[cut:]]
        url = _url(title, body("\n".join(shown)))
        if len(url) <= MAX_URL or cut >= len(lines) - 1:
            return url
        cut += 1
        while cut < len(lines) - 1 and not lines[cut].startswith("  File"):
            cut += 1
