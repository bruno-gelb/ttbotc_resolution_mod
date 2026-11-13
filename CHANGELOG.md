# Changelog

Versions follow [semantic versioning](https://semver.org). Each version's section here becomes its release notes.

## Unreleased

- Linux: no more Steam launch options. The installer tells Proton to use cnc-ddraw in Tzar's own Proton settings, and
  removing the mod takes that back. Start the game once before installing, so that Proton sets it up. If you added
  `WINEDLLOVERRIDES="ddraw=n,b"` to Tzar's Launch Options for an earlier version, run the program again to apply
  the new setting, then you can clear them ([#26](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/26)).
- Shorter install steps. The programs on the releases page are now named `tzar-widescreen-windows.exe` and
  `tzar-widescreen-linux`, without the version, so the README links straight to the newest one, and on Linux one
  line downloads and starts it. The program still shows its version when it starts
  ([#28](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/28)).

## 0.2.1 (2026-11-13)

- The program's command line is rebuilt with [Click](https://click.palletsprojects.com/en/stable/): `install`,
  `uninstall` and `status` each have their own `--help`, and wrong options get clearer messages. Everything that
  worked before still works ([#14](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/14)).
- If the mod's backup record (`tzar-widescreen-backup/manifest.json`) gets damaged, the program now says so and how
  to recover. Before, it treated the mod as not installed and blamed other software for the changed game files
  ([#16](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/16)).

## 0.2.0 (2026-11-13)

- Choose the resolution: the installer detects your screen and offers the width with the same shape, presets for
  16:10 (1232x768), 16:9 (1368x768) and 21:9 (1832x768), or any width from 1032 to 2198. The height stays 768
  ([#11](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/11)).
- Running the installer again when the mod is installed offers to change the resolution, not only to remove the
  mod. `--width` sets it from the command line.

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
