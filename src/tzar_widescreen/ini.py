"""Edit keys in the game's INI files (tzar.ini, DATA/LAYOUT.INI) without touching anything else in them.

The files are Windows text (CRLF line endings, Latin-1); both are kept as they are.
"""

import re
from pathlib import Path


def _section_body(text: str, section: str) -> tuple[int, int] | None:
    """Start and end of a section's body: from the newline after its [header] to the next [header]."""
    header = re.search(rf"(?im)^\[{re.escape(section)}\][ \t]*\r?$", text)
    if not header:
        return None
    nxt = re.search(r"(?m)^\[", text[header.end():])
    return header.end(), header.end() + nxt.start() if nxt else len(text)


def _key_pattern(key: str) -> re.Pattern:
    return re.compile(rf"(?im)^([ \t]*{re.escape(key)}[ \t]*=[ \t]*)([^\r\n]*)")


def get_key(text: str, section: str, key: str) -> str | None:
    span = _section_body(text, section)
    if not span:
        return None
    match = _key_pattern(key).search(text, span[0], span[1])
    return match.group(2).strip() if match else None


def set_key(text: str, section: str, key: str, value: str) -> str:
    """Set key in section, keeping the line's spacing. Adds the key, or the whole section, when missing."""
    nl = "\r\n" if "\r\n" in text else "\n"
    span = _section_body(text, section)
    if not span:
        sep = nl if text and not text.endswith("\n") else ""
        return f"{text}{sep}[{section}]{nl}{key}={value}{nl}"
    start, end = span
    match = _key_pattern(key).search(text, start, end)
    if match:
        return text[:match.start(2)] + value + text[match.end(2):]
    # start points at the "\n" ending the header line: insert the key right after it
    return text[:start + 1] + f"{key}={value}{nl}" + text[start + 1:]


def read(path: Path) -> str:
    return path.read_bytes().decode("latin-1")


def write(path: Path, text: str) -> None:
    path.write_bytes(text.encode("latin-1"))
