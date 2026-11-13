"""Download cnc-ddraw's release (pinned, checksum verified) into src/tzar_widescreen/cnc_ddraw/ for bundling.

Usage: uv run python src/tools/fetch_cnc_ddraw.py

Its license goes in as ddraw-LICENSE.txt, which the installer copies next to ddraw.dll. The xBRZ shaders are left out:
they're GPL-3.0 (from HqMAME), the mod doesn't use them, and shipping them would mean shipping the GPL with them.
"""

import hashlib
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

VERSION = "v7.1.0.0"
URL = f"https://github.com/FunkyFr3sh/cnc-ddraw/releases/download/{VERSION}/cnc-ddraw.zip"
SHA256 = "0b13ab89a64c9918189b1dadd449ef6ed3cb3b7b19cabd96d8adbd95505bb908"
LICENSE_URL = f"https://raw.githubusercontent.com/FunkyFr3sh/cnc-ddraw/{VERSION}/LICENSE"
DEST = Path(__file__).resolve().parents[1] / "tzar_widescreen" / "cnc_ddraw"
LEFT_OUT = ("Shaders/xbrz/",)  # GPL-3.0, unused


def main() -> None:
    data = urllib.request.urlopen(URL, timeout=60).read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        sys.exit(f"cnc-ddraw.zip checksum mismatch: {digest}, expected {SHA256}")
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            name = info.filename
            shader = name.startswith("Shaders/") and not name.endswith(".zip") and not name.startswith(LEFT_OUT)
            if name in ("ddraw.dll", "ddraw.ini") or shader:
                target = (DEST / name).resolve()
                if DEST not in target.parents:
                    sys.exit(f"unexpected path in the zip: {name}")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(info))
    (DEST / "ddraw-LICENSE.txt").write_bytes(urllib.request.urlopen(LICENSE_URL, timeout=60).read())
    print(f"cnc-ddraw {VERSION} in {DEST}")


if __name__ == "__main__":
    main()
