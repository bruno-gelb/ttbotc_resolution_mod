"""Build the single-file tzar-widescreen program for this platform into dist/.

Usage: uv run python src/tools/build_release.py
Needs cnc-ddraw's files first: uv run python src/tools/fetch_cnc_ddraw.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "tzar_widescreen"


def main() -> None:
    if not (PACKAGE / "cnc_ddraw" / "ddraw.dll").is_file():
        sys.exit("cnc-ddraw's files are missing: run src/tools/fetch_cnc_ddraw.py first")
    platform = "windows" if sys.platform == "win32" else "linux"
    # No version in the name: the README links to releases/latest/download/<name>, which always gets the newest one.
    # The program shows its version when it starts.
    name = f"tzar-widescreen-{platform}"
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--console", "--clean", "--noconfirm",
        "--name", name,
        "--add-data", f"{PACKAGE / 'cnc_ddraw'}{os.pathsep}tzar_widescreen/cnc_ddraw",
        "--copy-metadata", "ttbotc-resolution-mod",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        str(PACKAGE / "__main__.py"),
    ], check=True, cwd=ROOT)
    out = ROOT / "dist" / (name + (".exe" if platform == "windows" else ""))
    print(f"built {out} ({out.stat().st_size // 1024} KB)")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"file={out}\n")
    shutil.rmtree(ROOT / "build", ignore_errors=True)


if __name__ == "__main__":
    main()
