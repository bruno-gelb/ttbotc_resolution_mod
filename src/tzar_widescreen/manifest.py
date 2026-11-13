"""The record of what the mod did to a game folder: tzar-widescreen-backup/manifest.json.

It sits next to the backed-up original files and tells uninstall what to put back, and the installer what's installed.
"""

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

FILE = "manifest.json"


class DamagedManifest(Exception):
    """manifest.json exists but can't be read."""


@dataclass
class Manifest:
    version: str  # the mod's version that last installed it
    # The game's width the mod was installed with. 0.1.0 didn't record it: it always used 1832.
    width: int = 1832
    # Original values of the tzar.ini keys the mod changes, as "SECTION/KEY": value (None if the key wasn't there).
    tzar_ini: dict[str, str | None] = field(default_factory=dict)
    # Files that were in the game folder before the mod (someone else's ddraw.dll), kept in the backup to put back.
    moved_aside: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, backup_dir: Path) -> "Manifest | None":
        """The manifest in backup_dir, or None if there isn't one (the mod isn't installed)."""
        path = backup_dir / FILE
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as error:
            raise DamagedManifest(f"{path} can't be read ({error})") from error
        if not isinstance(data, dict):
            raise DamagedManifest(f"{path} isn't a JSON object")
        known = {f.name for f in fields(cls)}
        try:
            manifest = cls(**{key: value for key, value in data.items() if key in known})
        except TypeError as error:  # "version" missing
            raise DamagedManifest(f"{path} is incomplete ({error})") from error
        manifest._check(path)
        return manifest

    def _check(self, path: Path) -> None:
        ok = (isinstance(self.version, str) and isinstance(self.width, int)
              and isinstance(self.tzar_ini, dict) and all(isinstance(k, str) for k in self.tzar_ini)
              and all(v is None or isinstance(v, str) for v in self.tzar_ini.values())
              and isinstance(self.moved_aside, list) and all(isinstance(n, str) for n in self.moved_aside))
        if not ok:
            raise DamagedManifest(f"{path} has values of the wrong type")

    def save(self, backup_dir: Path) -> None:
        (backup_dir / FILE).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
