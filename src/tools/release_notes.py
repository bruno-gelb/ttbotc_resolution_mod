"""Print the CHANGELOG.md section of a version, for its GitHub release notes.

Usage: python src/tools/release_notes.py 0.1.0
"""

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[2] / "CHANGELOG.md"


def main() -> None:
    version = sys.argv[1].removeprefix("v")
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(rf"(?ms)^## {re.escape(version)}\b[^\n]*\n(.*?)(?=^## |\Z)", text)
    if not match:
        sys.exit(f"no section for {version} in CHANGELOG.md")
    # Unwrap the 120-column paragraphs: GitHub turns single line breaks in release notes into real ones.
    notes = re.sub(r"\n(?=[ ]{2}\S|[^\n-])", " ", match.group(1).strip())
    print(re.sub(r" {2,}", " ", notes))


if __name__ == "__main__":
    main()
