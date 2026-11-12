# Changelog

Versions follow [semantic versioning](https://semver.org). Each version's section here becomes its release notes.

## 0.1.0 (2026-11-13)

First release.

- Runs the Steam version 1.10 at 1832x768 (21:9) with the panel on the left, scaled to the screen by
  [cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw) 7.1.0.0.
- The map is redrawn across the full width. The game's record of what to redraw only reached 1024 px across, so
  everything further right was left stale and the mouse cursor left a trail there.
- The game no longer refuses to start with "Invalid TZAR configuration detected" when the sound devices differ from
  the ones its settings were saved with, which made it fail under Proton
  ([#4](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/4)).
- `tzar-widescreen` installs and removes the mod on Windows and Linux, keeping the original files to put back
  ([#6](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/6)).
