# Contributing

Notes for working on the mod. For what it is and how to play it, see the [README](README.md).

## How it works

The idea is the one [DisciplesGL](https://github.com/rootext/disciples-gl-builds) uses for Disciples II: tell the game
it has a bigger screen, give it a wider in-game layout, and fix the places where the game's code assumes one of its
original screen sizes (800x600 or 1024x768). The target is the screen's shape, not its full size: on a 3440x1440
screen, a 1720x720 game picture scaled up 2x keeps the sprites a sensible size, where native 3440x1440 would make them
tiny.

What it takes today, for 1832x768 with the left panel. The code is in `src/tzar_widescreen/`:

- **The exe** (`exe_patch.py`): the screen size the game uses for its "1024" layouts, the map view's redraw tracking,
  which only covered 1024 px, and the startup check that refused to run when the sound devices changed.
- **`DATA/LAYOUT.INI`** (`install.py`): a wider map view in `[LAYOUT1024L]`.
- **The in-game frame bitmap** (`frame.py`), widened from the game's own.
- **[cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw)** (`cnc_ddraw.py`), which adds the 1832x768 display mode
  the game asks for and scales it to the monitor. Its files are bundled into the release programs.

`install.py` puts it together: it backs up the original files to `tzar-widescreen-backup/` in the game folder, with a
manifest, and puts them back on uninstall. `game.py` finds the game in the Steam libraries, and `cli.py` is the
`tzar-widescreen` program.

All the details, with addresses: [docs/findings.md](docs/findings.md).

## Running from source

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

```bash
uv run python src/tools/fetch_cnc_ddraw.py
```

```bash
uv run tzar-widescreen --help
```

`fetch_cnc_ddraw.py` downloads cnc-ddraw's release (pinned, checksum verified) into `src/tzar_widescreen/cnc_ddraw/`,
which git ignores. `tzar-widescreen status --game-dir "<game folder>"` shows what's applied without changing anything.
Test on a copy of the game's folder first: the program needs only `Tzar_.exe`, `tzar.ini`, `DATA/LAYOUT.INI` and
`IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP` in it.

Every third-party dependency is pinned to an exact version: Python in `.python-version`, packages in
`pyproject.toml` and, with their whole tree, in `uv.lock`, cnc-ddraw by version and checksum in
`fetch_cnc_ddraw.py`, and in the release workflow the actions, uv and the runner images. Update a pin on purpose,
in its own commit, and run `uv lock` after changing `pyproject.toml`.

To build the single-file program for your platform into `dist/` (the same command the release uses):

```bash
uv run python src/tools/build_release.py
```

## Tools

`src/tools/` has scripts for development, run with `uv run python src/tools/<script>`:

- `fetch_cnc_ddraw.py`, `build_release.py` and `release_notes.py`: the release build (above and below).
- `probe.py` and `xref.py`: static analysis of the exe, with [pefile](https://github.com/erocarrera/pefile) and
  [Capstone](https://www.capstone-engine.org/). `probe.py` prints the exe's layout, its imports and hardcoded
  screen-size constants; `xref.py` finds strings, references to an address, struct fields and immediate values, and
  disassembles code. See their docstrings for all queries.

  ```bash
  uv run python src/tools/probe.py "<game folder>/Tzar_.exe" pairs
  ```

  ```bash
  uv run python src/tools/xref.py "<game folder>/Tzar_.exe" str LAYOUT , ref 587732 , dis 43bb1b 10
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
  long-lived branch. Make each change on a short-lived branch and merge it into `main` with a pull request within a
  day or two. `main` is protected: it takes no direct pushes, no force pushes and can't be deleted. Pull request
  titles follow the same rules as commit subjects. Keep `main` working: every merge should leave the mod in a state
  that applies and runs.

## Versions and releases

Versions follow [semantic versioning](https://semver.org), and the version lives in `pyproject.toml`: the major
number for changes that make players do something differently (a different install, a dropped game version), the
minor one for new features (resolutions, layouts, game versions), the patch one for fixes. While it's 0.x, minor
versions can also carry bigger changes.

To release:

1. Add the version's section to [CHANGELOG.md](CHANGELOG.md): it becomes the release notes.
2. Set the version in `pyproject.toml`, run `uv lock`, commit (`Release 0.2.0`) and merge it into `main` with a pull
   request.
3. Tag the merged commit on `main` and push the tag:

   ```bash
   git tag -a v0.2.0 -m "Release 0.2.0" && git push origin v0.2.0
   ```

The [release workflow](.github/workflows/release.yml) then builds the programs for Windows and Linux, checks that
the tag matches `pyproject.toml`, and publishes the release with both. Running it by hand (Actions, Release, Run
workflow) only builds them, to download and test before tagging.

## License

Contributions are under the [MIT License](LICENSE), like the rest of the mod. Never commit the game's files: its
exe, DLLs, bitmaps or data. `.gitignore` keeps `.exe`, `.dll` and `.bmp` files out.
