# Contributing

Notes for working on the mod. For what it is and how to play it, see the [README](README.md).

## How it works

The idea is the one [DisciplesGL](https://github.com/rootext/disciples-gl-builds) uses for Disciples II: tell the game
it has a bigger screen, give it a wider in-game layout, and fix the places where the game's code assumes one of its
original screen sizes (800x600 or 1024x768). The target is the screen's shape, not its full size: on a 3440x1440
screen, a 1720x720 game picture scaled up 2x keeps the sprites a sensible size, where native 3440x1440 would make them
tiny.

What it takes today, for 1832x768 with the left panel:

- **The exe.** The screen size the game uses for its "1024" layouts, and the map view's redraw tracking, which only
  covered 1024 px. Both in `tools/patch_exe.py`.
- **`DATA/LAYOUT.INI`.** A wider map view in `[LAYOUT1024L]`.
- **The in-game frame bitmap**, widened by `tools/make_frame.py` from the game's own.
- **[cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw)**, which adds the 1832x768 display mode the game asks for
  and scales it to the monitor.

All the details, with addresses: [docs/findings.md](docs/findings.md).

## Applying it by hand

Until there's an installer. Tested only with the Steam version 1.10 under Proton.

1. Back up `Tzar_.exe`, `tzar.ini`, `DATA/LAYOUT.INI` and `IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP` from the game
   folder.
2. Patch the exe. The script checks every byte before changing it and refuses an unknown version:

   ```bash
   uv run tools/patch_exe.py "<game folder>/Tzar_.exe" 1832 768
   ```

3. In `DATA/LAYOUT.INI`, under `[LAYOUT1024L]`, set `view = 150,30,1682,738`. In `tzar.ini`, under `[DEFAULTS]`,
   `LAYOUT=LAYOUT1024L`, and under `[VIDEO]`, `DIRECTXDEVICE=0`.
4. Make the wider frame from the backed-up original:

   ```bash
   uv run tools/make_frame.py "<backup>/SCREEN 1024 LEFT.BMP" "<game folder>/IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP" 1832
   ```

5. Put cnc-ddraw's `ddraw.dll`, `ddraw.ini` and `Shaders/` in the game folder. In `ddraw.ini`, under `[ddraw]`:
   `fullscreen=true`, `maintas=true`, `inject_resolution=1832x768`, `resolutions=2`, `renderer=opengl`. Then add a
   section for the game's process, `Tzar_.exe` (cnc-ddraw's own preset is named `[Tzar]`, after Steam's launcher):

   ```ini
   [Tzar_]
   adjmouse=true
   ```

6. Under Proton, set the Steam launch options to `WINEDLLOVERRIDES="ddraw=n,b" %command%`, so the game loads
   cnc-ddraw instead of Wine's DirectDraw.
7. If the game says "Invalid TZAR configuration detected", set the sound device counts in `tzar.ini`
   (`SOUNDDEVICENUMBER`, `SOUNDDEVICEDXNUMBER`, `SOUNDDEVICEMIDINUMBER`) as described in
   [the findings](docs/findings.md#startup-config-check-invalid-tzar-configuration).

To undo: copy the backups back and delete `ddraw.dll`, `ddraw.ini` and `Shaders/`, or use Steam's "Verify integrity
of game files" and delete the cnc-ddraw files.

## Tools

`tools/` has Python scripts, run with [uv](https://docs.astral.sh/uv/):

- `patch_exe.py` and `make_frame.py` are the mod itself (above).
- `probe.py` and `xref.py` are for static analysis of the exe, with [pefile](https://github.com/erocarrera/pefile)
  and [Capstone](https://www.capstone-engine.org/). `probe.py` prints the exe's layout, its imports and hardcoded
  screen-size constants; `xref.py` finds strings, references to an address, struct fields and immediate values, and
  disassembles code. See their docstrings for all queries.

  ```bash
  uv run tools/probe.py "<game folder>/Tzar_.exe" pairs
  ```

  ```bash
  uv run tools/xref.py "<game folder>/Tzar_.exe" str LAYOUT , ref 587732 , dis 43bb1b 10
  ```

For what static analysis can't find, profiling the running game helps: `perf record -p <pid of Tzar_.exe>` while
doing the thing you're after, then sort the samples by address (the exe always loads at `0x400000`). That's how the
redraw limit was found.

## Plans and bugs

They're [GitHub issues](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues): what's next, known problems
and ideas. Open one before starting on something bigger. Bug reports, feature requests and testing help are most
welcome, especially on Windows and with the GOG version.

## Workflow

- **Commit messages** follow [How to Write a Git Commit Message](https://cbea.ms/git-commit/): a subject line of up
  to 50 characters, capitalized, in the imperative mood ("Widen the redraw tracking", not "Widened..."), with no
  period at the end; a blank line; then a body wrapped at 72 characters that says what changed and why.
- **Branches** follow [trunk-based development](https://trunkbaseddevelopment.com/): `main` is the trunk and the only
  long-lived branch. Commit to it in small steps, or use a short-lived branch that's merged back within a day or two.
  Keep `main` working: every commit should leave the mod in a state that applies and runs.

## License

Contributions are under the [MIT License](LICENSE), like the rest of the mod. Never commit the game's files: its
exe, DLLs, bitmaps or data. `.gitignore` keeps `.exe`, `.dll` and `.bmp` files out.
