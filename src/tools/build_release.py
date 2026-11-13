"""Build the single-file tzar-widescreen program for this platform into dist/.

Usage: uv run python src/tools/build_release.py
Needs cnc-ddraw's files first: uv run python src/tools/fetch_cnc_ddraw.py
and on Linux the music synthesizer: uv run python src/tools/fetch_soundfont.py && uv run python src/tools/build_music.py

The version goes into the program's metadata too. On Windows it's a version resource, what Explorer shows under
Properties, Details. ELF has no such field and file managers show none, so the Linux program gets the nearest thing:
a .note.package section in systemd's package metadata format (https://systemd.io/ELF_PACKAGE_METADATA/), which
`readelf -n` shows. systemd's own tools only read notes that are linked into the program, which would mean building
PyInstaller's bootloader ourselves.
"""

import json
import os
import shutil
import subprocess
import sys
import struct
import tempfile
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "tzar_widescreen"
PRODUCT = "ttbotc_resolution_mod"
URL = "https://github.com/bruno-gelb/ttbotc_resolution_mod"

# PyInstaller's --version-file format: Python code it evaluates with the classes from
# PyInstaller.utils.win32.versioninfo. 0x0409, 1200: US English, Unicode, the same as the 040904B0 table.
VERSION_INFO = """\
VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}),
  kids=[
    StringFileInfo([StringTable('040904B0', [
{strings}
    ])]),
    VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
  ],
)
"""


def version_strings(v: str, filename: str) -> dict[str, str]:
    return {
        "ProductName": PRODUCT,
        "ProductVersion": v,
        "FileDescription": "Tzar widescreen mod installer",
        "FileVersion": v,
        "InternalName": "tzar-widescreen",
        "OriginalFilename": filename,
        "LegalCopyright": "Copyright (c) 2026 Bruno Gelb, MIT License",
    }


def version_info(v: str, filename: str) -> str:
    """The version resource for --version-file. v is X.Y.Z, as in pyproject.toml."""
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        sys.exit(f"version {v!r} isn't X.Y.Z: a Windows version resource needs plain numbers")
    numbers = (*map(int, parts), 0)
    strings = ",\n".join(f"      StringStruct({k!r}, {s!r})" for k, s in version_strings(v, filename).items())
    return VERSION_INFO.format(numbers=numbers, strings=strings)


def check_version_info(exe: Path, expected: dict[str, str]) -> None:
    """Fail the build if the exe's version resource isn't what was asked for."""
    import pefile

    pe = pefile.PE(str(exe))
    found = {
        key.decode(): value.decode()
        for info in getattr(pe, "FileInfo", None) or []
        for entry in info
        for table in getattr(entry, "StringTable", [])
        for key, value in table.entries.items()
    }
    pe.close()
    if found != expected:
        sys.exit(f"{exe.name}'s version resource is {found}, expected {expected}")


def package_metadata(v: str) -> dict[str, str]:
    return {"type": "github", "name": PRODUCT, "version": v, "url": URL}


def package_note(v: str) -> bytes:
    """The .note.package section: one ELF note, owner "FDO", type 0xcafe1a7e, holding the metadata as JSON."""
    name = b"FDO\0"
    desc = json.dumps(package_metadata(v), separators=(",", ":")).encode() + b"\0"
    desc += b"\0" * (-len(desc) % 4)  # notes are 4-byte aligned
    return struct.pack("<III", len(name), len(desc), 0xCAFE1A7E) + name + desc


def add_package_note(exe: Path, v: str, tmp: Path) -> None:
    """Add the note with objcopy, the same way PyInstaller adds its own data to the Linux program."""
    note = tmp / "package_note.bin"
    note.write_bytes(package_note(v))
    subprocess.run(["objcopy", "--add-section", f".note.package={note}",
                    "--set-section-flags", ".note.package=noload,readonly", str(exe)], check=True)
    notes = subprocess.run(["readelf", "-n", str(exe)], check=True, capture_output=True, text=True).stdout
    expected = json.dumps(package_metadata(v), separators=(",", ":"))
    if expected not in notes:
        sys.exit(f"{exe.name} has no package note with {expected}:\n{notes}")


def main() -> None:
    if not (PACKAGE / "cnc_ddraw" / "ddraw.dll").is_file():
        sys.exit("cnc-ddraw's files are missing: run src/tools/fetch_cnc_ddraw.py first")
    v = version("ttbotc-resolution-mod")
    platform = "windows" if sys.platform == "win32" else "linux"
    # The music synthesizer is for Linux only: Windows plays the game's MIDI music itself.
    music = []
    if platform == "linux":
        if not all((PACKAGE / "music" / name).is_file() for name in ("TZMUS.dll", "TZMUS.sf2", "TZMUS-LICENSES.txt")):
            sys.exit("the music files are missing: run src/tools/fetch_soundfont.py and src/tools/build_music.py first")
        music = ["--add-data", f"{PACKAGE / 'music'}{os.pathsep}tzar_widescreen/music"]
    # No version in the name: the README links to releases/latest/download/<name>, which always gets the newest one.
    # The program shows its version when it starts, and in its metadata (above).
    name = f"tzar-widescreen-{platform}"
    out = ROOT / "dist" / (name + (".exe" if platform == "windows" else ""))
    with tempfile.TemporaryDirectory() as tmp:
        extra = []
        if platform == "windows":
            version_file = Path(tmp) / "version_info.txt"
            version_file.write_text(version_info(v, out.name), encoding="utf-8")
            extra = ["--version-file", str(version_file)]
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--onefile", "--console", "--clean", "--noconfirm",
            "--name", name,
            "--add-data", f"{PACKAGE / 'cnc_ddraw'}{os.pathsep}tzar_widescreen/cnc_ddraw",
            *music,
            "--copy-metadata", "ttbotc-resolution-mod",
            *extra,
            "--distpath", str(ROOT / "dist"),
            "--workpath", str(ROOT / "build"),
            "--specpath", str(ROOT / "build"),
            str(PACKAGE / "__main__.py"),
        ], check=True, cwd=ROOT)
        if platform == "windows":
            check_version_info(out, version_strings(v, out.name))
        else:
            add_package_note(out, v, Path(tmp))
    print(f"built {out} ({out.stat().st_size // 1024} KB)")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"file={out}\n")
    shutil.rmtree(ROOT / "build", ignore_errors=True)


if __name__ == "__main__":
    main()
