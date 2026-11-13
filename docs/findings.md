# Findings

Static analysis of [Tzar: The Burden of the Crown][tzar] (Steam version 1.10, by
[Haemimont Games][haemimont]), 2026-11-13, then tested in the running game: see the test sections below.

## The game's files

- `Tzar.exe` (21 KB) is a small launcher that starts `Tzar_.exe`, the real game: version 1.10, built in 2002
  (`FileVersion 1, 0, 1, 0`, PE timestamp 1015080651), 32-bit, image base `0x400000`.
- `tzar.ini` in the game folder holds the settings. `[DEFAULTS] LAYOUT=` picks the in-game screen layout by name;
  `[VIDEO] DIRECTXDEVICE=-1` is the setting cnc-ddraw's Tzar preset asks to set to `0`.
- `DATA/LAYOUT.INI` defines six layouts: `LAYOUT800H/L/R` and `LAYOUT1024H/L/R`. H has the panel at the bottom, L on
  the left, R on the right. Each one gives the frame bitmap, the map view rectangle, the minimap and the top-bar
  items (resources, menu, diplomacy and chat buttons, clock) as pixel coordinates. So the in-game frame is data, not
  code.
- The frame bitmaps are `IMAGES/SCREENS/S_VIEW/SCREEN 800*.BMP` (800x600) and `SCREEN 1024*.BMP` (1024x768), 16-bit
  uncompressed BMP. The menu screens (`IMAGES/SCREENS/S_*/BACK.BMP`) are 800x600 only.

## The GOG version

Checked 2026-11-13 with GOG's offline installer `setup_tzar_1.01_(10554).exe` (Inno Setup 5.5.7, GOG game ID
1207659252), unpacked with innoextract, and with a real install through Heroic 2.22.4 on Linux.

- **Same game.** GOG calls it 1.01, but GOG's `Tzar.exe` is Steam's `Tzar_.exe`: same timestamp (1015080651), and
  only 7 bytes differ, all in the PE header (the checksum and the security directory). Steam's copy carries a
  6,072-byte Authenticode signature; every Steam exe is 6,072 bytes bigger than GOG's for the same reason, and the
  DLLs are identical. Of the 2,914 files both have, only those exes differ, so `LAYOUT.INI`, the frame bitmap and
  `STRINGS.INI` are the same too.
- **The exe's name.** On Steam, `Tzar.exe` is a 21 KB launcher for `Tzar_.exe`; on GOG, `Tzar.exe` is the game.
  cnc-ddraw's own `[Tzar]` preset applies to it directly.
- **`tzar.ini`** ships as `__support/app/tzar.ini` (740 B: `LAYOUT1024L`, `DIRECTXDEVICE=-1`, sound counts
  5 / 5 / 2, `DONESETUP=1`); Heroic copies it next to the game at install time.
- **No DirectDraw wrapper.** `goggame.sdb` adds one Windows compatibility shim to `Tzar.exe`, `EmulateHeap`. GOG's
  install script sets `HKCU\Software\Haemimont\Tzar` `Path` to the game folder.
- **Heroic** keeps the install in `~/.config/heroic/gog_store/installed.json` (`install_path`) and the game's
  settings in `GamesConfig/1207659252.json` (`winePrefix`, `wineVersion`). With a Proton build (Proton-CachyOS,
  through umu), the prefix's `pfx` is a link to the prefix itself, so `<prefix>/pfx/user.reg` is the registry, laid
  out like Steam's `compatdata/825730/pfx`. The stock game fails there too with "Invalid TZAR configuration", the
  sound check below.

## Screen size in the code

- The screen size lives in two 16-bit globals: width at `0x587732`, height at `0x587734`. Their defaults in `.data`
  are 800 and 600.
- Set in one place only, `0x43bb1b`: after reading `LAYOUT` from `tzar.ini` (default `LAYOUT800L`), the game checks
  whether the name contains `"1024"`. If it does, `0x43bb31` writes 1024 (`0x400`) and `0x43bb3a` writes 768
  (`0x300`). Both are `mov word ptr [addr], imm16`, so any size that fits in 16 bits can be patched in.
- About 125 places read these globals and use them as plain numbers: a good sign that most of the engine works with
  any size.
- The 800x600 menus are centered on a bigger screen by `(width - 800) / 2` and `(height - 600) / 2` (`0x4fa1f0`), so
  they should follow a new size on their own.
- When saving settings (`0x43c12d`), the game writes `LAYOUT800x` if the width is 800 and `LAYOUT1024x` otherwise,
  so a new size can reuse the `LAYOUT1024L` name.
- `0x474390` maps a width to a height: 768 if the width is 1024, otherwise 600. It's called three times around
  `0x4759xx` (probably the options screen and display mode switching) and needs the same patch as `0x43bb31`.

## Hardcoded 1024 checks

- 12 places (`0x49ce34` to `0x4a5a0a`) position the panel buttons with "is the width exactly 1024?". For the bottom
  layout (H) they shift buttons down by 168 (768 - 600), for the right layout (R) right by 224 (1024 - 800). The left
  layout (L) uses fixed positions that don't depend on the screen size. **So the left-panel layout needs no code
  changes here**, while H and R would need each of these 12 checks rewritten.
- The other `0x400` constants in the code are unrelated: buffer sizes, loop limits, bit flags and CPU model names.

## DirectDraw

- `Tzar_.exe` doesn't import DirectDraw; it loads `ddraw.dll` with `LoadLibraryA` at `0x50ef2c` and looks up
  `DirectDrawCreate`. A `ddraw.dll` in the game folder (like cnc-ddraw) gets loaded first.
- The display mode comes from the list of modes the driver reports: `SetDisplayMode` (`0x50f8a3`) takes width,
  height and depth from an entry of that list. A size that no real display mode has (like 1832x768) needs
  cnc-ddraw's `inject_resolution=` option, which adds a custom mode to the list and scales it to the monitor.
- The primary surface is created with a back buffer (`0x50f286`), sized by the display mode, so no fixed-size screen
  buffer was found. The 7.7 MB `.data` section still deserves a look for static buffers sized for 1024x768.
- Under Proton, Wine prefers its own builtin `ddraw.dll` to the one in the game folder. The first tests used the
  launch option `WINEDLLOVERRIDES="ddraw=n,b"`. Now the installer sets the same override in the game's
  Proton prefix instead (#26): `steamapps/compatdata/825730/pfx/user.reg`, key
  `Software\\Wine\\AppDefaults\\Tzar_.exe\\DllOverrides`, value `"ddraw"="native,builtin"`, the section Proton
  uses for its own per-game overrides. Tested in the game without the launch option (2026-11-13). The prefix exists
  only after the game's first launch, and Wine writes `user.reg` back when the game exits, so it must be closed.

## Startup config check ("Invalid TZAR configuration")

Not about the resolution, but it blocks the first launch under Proton. After init (`0x475c17`), `0x4558c0` decides
whether the config is valid; if not, the game shows `invalidcfg` from `LOCAL/STRINGS.INI` and wants to run
`Setup.exe` on exit. The config is invalid if `DONESETUP` is 0, or either of two device checks fails:

- **Sound (`0x4d07e0`).** Each count must equal the number stored in `tzar.ini` minus one:
  - `SOUNDDEVICENUMBER` = `waveOutGetNumDevs()` + 1
  - `SOUNDDEVICEDXNUMBER` = DirectSound devices + 1, not counting "Primary Sound Driver" (callback `0x52fb90`)
  - `SOUNDDEVICEMIDINUMBER` = `midiOutGetNumDevs()` + 1

  The `tzar.ini` that ships on Steam has 3 / 3 / 2, from the developers' machine. On this laptop under Proton it's
  5 / 5 / 4 (outputs: Wine's default PulseAudio output, JBL Tune 525BT, Radeon HDMI, Ryzen analog; 3 MIDI devices),
  measured on 2026-11-13 with `WINEDEBUG=+relay` on those functions in a Steam launch. Run outside Steam's runtime
  container, Wine can't load its audio driver and reports 0 devices, so measure inside Steam. **The counts change
  when a device comes or goes (Bluetooth headphones), and the error comes back.** For now, a launch script
  (`tzar-run` in the `workstation` repo) rewrites them before every start: Wine's wave and DirectSound outputs are
  the PipeWire sinks plus Wine's own default "PulseAudio Output", and its MIDI outputs are the writable ALSA
  sequencer ports outside the kernel's System client (`/proc/asound/seq/clients`). Patching the check out is
  [#4](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/4).
- **DirectDraw (`0x455890`, only when `DIRECTXDEVICE` isn't -1).** `DIRECTDRAW_DEVICESNUMBER` - 1 must equal the
  number of devices `DirectDrawEnumerateA` reports (callback `0x50fc00` counts all of them). cnc-ddraw reports one,
  so the shipped value 2 works.

**Since 0.1.0 the mod skips the sound check's verdict** (`exe_patch.py`): the jump at `0x4558d0` that returns
"invalid" when `0x4d07e0` reports a mismatch (`75 0a`, `jne`) becomes two NOPs. `0x4d07e0` still runs and still
stores the device counts (`0xc97c34`-`0xc97c38`); its failure path only returns 1, with no side effects. Tested
2026-11-13 with the shipped counts 3 / 3 / 2 against the real 5 / 5 / 4: the game goes straight to the menu.

`DIRECTXDEVICE=-1` means GDI: the `Logs/Tzar.log` shipped with the game says `Video Renderer: GDI`. `0` is the first
DirectDraw device.

`Setup.exe`, the configuration program, doesn't start under Proton: it needs `MFC42.DLL`, which the prefix doesn't
have.

## Main menu version line

The main menu (`mainscr`) shows the game's version in its bottom-right corner. Its constructor builds the text at
`0x4d1834`: `sprintf(this + 0x60, "%s %s", <[general] version from LOCAL/STRINGS.INI>, <0x4ef450>)`, where
`0x4ef450` formats `"%d.%02d, 2/03/2002"`, so the line reads `Version 1.10, 2/03/2002`. The draw method at
`0x4d1960` measures the text and draws it twice for a shadow, right-aligned 29 px from the menu's right edge, at
y = 581 and 580 of the 800x600 menu. So on a wider screen it sits in the menu picture's corner, not the screen's.

The object is 0x168 bytes (allocated at `0x439150`) and nothing in `mainscr` uses it past `0x60`, so the buffer has
about 260 bytes, with no length check: keep the text well under that. `[general] version` is read nowhere else, so
changing it only changes this line; the multiplayer version checks use the numbers. The mod puts
`ttbotc_resolution_mod <version>. game ` in front of it (0.4.0).

`|` can't go in the text: `STRINGS.INI` uses it to split a label from its hint (`single = SINGLE PLAYER| Single player
game`), and the game shows only what comes before it. Tested 2026-11-13: with `| game ` in front, the menu read
`ttbotc_resolution_mod 0.3.0 1.10, 2/03/2002`.

## Plan for a first test

Keep the left-panel layout and change only the width, so nothing vertical moves:

1. Back up `Tzar_.exe`, `tzar.ini`, `DATA/LAYOUT.INI` and `SCREEN 1024 LEFT.BMP`.
2. Patch `Tzar_.exe`: 1024 to 1832 at `0x43bb31`, and the width check in `0x474390`.
3. `LAYOUT.INI`: in `[LAYOUT1024L]`, `view = 150,30,1682,738`.
4. Generate a 1832x768 `SCREEN 1024 LEFT.BMP` from the original by widening its top bar.
5. Install cnc-ddraw with the Tzar preset, `DIRECTXDEVICE=0` and `inject_resolution=1832x768`, and launch through
   Proton with `WINEDLLOVERRIDES="ddraw=n,b"`.

1832x768 is 21:9 with the original 768 height: cnc-ddraw scales it 1.875x to 3435x1440 on a 3440x1440 screen. If it
works, the next step is 1720x720, exactly half of 3440x1440, for a sharp 2x scale; that one cuts 48 pixels off the
left panel's height, so it needs a check of what sits at the bottom of the panel first.

## Test 1: 1832x768 (set up 2026-11-13)

What was changed in the game folder (`~/.steam/debian-installation/steamapps/common/Tzar`):

- `Tzar_.exe`: `patch_exe.py Tzar_.exe 1832 768` (now `exe_patch.py`), 4 bytes (1024 to 1832 at `0x43bb31` and
  `0x474398`).
- `DATA/LAYOUT.INI`: `[LAYOUT1024L] view = 150,30,1682,738`.
- `IMAGES/SCREENS/S_VIEW/SCREEN 1024 LEFT.BMP`: 1832x768, made by `make_frame.py` (now `frame.py`) (the top bar's vine
  ornament repeats every 42 px).
- `tzar.ini`: `DIRECTXDEVICE=0`, and the sound device counts 5 / 5 / 4 (see above).
- Added cnc-ddraw v7.1.0.0 (`ddraw.dll`, `ddraw.ini`, `Shaders/`): `fullscreen=true`, `maintas=true`,
  `inject_resolution=1832x768`, `resolutions=2`, `renderer=opengl`, plus a `[Tzar_]` section with `adjmouse=true`,
  since the game process is `Tzar_.exe` and cnc-ddraw's own preset is named `[Tzar]`.
- Steam launch options: `WINEDLLOVERRIDES=ddraw=n,b` plus the `workstation` repo's `native-scale-run` (100%
  display scale while the game runs). To be replaced by `tzar-run %command%` from the same repo, which does both
  and also rewrites the sound device counts.

The original files are in `ttbotc_backup_2026-11-13/` in the game folder. To undo: copy them back, delete
`ddraw.dll`, `ddraw.ini` and `Shaders/`, and clear the launch options. `localconfig.vdf` from before the launch
options change is in `~/clients/personal/localconfig.vdf.bak-2026-11-13-tzar`.

What to check: the game starts; the menus show centered; in a game the frame fills the width with the map view
across it; scrolling to the map's right edge; the minimap's view rectangle; clicks land under the cursor.

### Results (2026-11-13)

Runs at 1832x768: the frame spans the screen, FPS is good, hotkeys work. **Bug: the map is only drawn in the first
~1024 px of the view.** On the screenshot it ends in a straight vertical line about 1025 px right of the panel
(screen x ~1175); a band about 130 px wide after it shows stale, smeared shroud edges, and the rest is black and never
redrawn, so the mouse cursor leaves a trail there. So the renderer has a limit of its own, independent of the
screen size globals.

What's known about it:

- The `view` rectangle from `LAYOUT.INI` is parsed at `0x43e25b` into four 16-bit globals: x `0xc99dbe`, y
  `0xc99dc0`, width `0xc99dc2`, height `0xc99dc4`. They're read in only five places: `0x43fc3d` (minimap bitmap,
  width / 32), `0x454e93` and `0x4f9daa` (the view rectangle as a clip rect), `0x470639` (the minimap's view
  rectangle, width / 32 in map units: the map's coordinates are in 32 px units) and `0x4ef746` (copied into an
  object's fields `+0x30..+0x36`, probably the map view itself).
- Ruled out: the other `0x400` constants, buffer-size constants for 1024x768 (`0xc0000`, `0x180000`), and every
  compare with 32/33/34 near `shl`/`sar` by 5 (an allocator and switch tables).

**Found by profiling** (`perf record -p <pid>` while scrolling, with `kernel.perf_event_paranoid=2`; samples sorted
by address in the exe, which always loads at `0x400000`): the hot `0x4f36a0` led to the map view's **dirty
rectangles**. The view object (`[0x5cf570]`, created at `0x4ef746`) keeps a 64-bit mask per row at
`+0x16dc + row * 8`: one bit per 16 px column, one row per 16 px. `0x4f99b0` turns a rectangle into a row range and
column bits, `x - view left >> 4`, clamped to 64 columns. `0x4f3760` walks the bits back into rectangles to redraw,
stepping 16 px per bit (and 512 px to skip the first 32-bit word). 64 × 16 = 1024 px, so nothing further right
was ever marked for redraw.

Fix (in `exe_patch.py`, 8 spots): each bit covers 32 px instead of 16, up to 2048 px. `sar 4` → `sar 5` for x at
`0x4f9a1d` and `0x4f9a78`; in `0x4f3760` the x steps 16 → 32 at `0x4f3864`, `0x4f3887`, `0x4f38a7`, `0x4f38ca`,
`0x4f38ef`, and 512 → 1024 at `0x4f38b9`. Rows stay 16 px (64 rows = 1024 px, enough for any height here). The
masks are only touched by these two functions, `0x4f3610` and `0x4f36a0` (both go through `0x4f99b0`), and two
`rep stosd` clears. The map's own tile range is separate: `+0x1926`/`+0x1928`, the view size in 32 px tiles.

Tested 2026-11-13: the map is drawn across the full 1832 px width, no cursor trail. Since 0.2.0 the width is a
choice from 1032 to 2198 (the 150 px panel plus the 2048 px the redraw masks now reach); tested in the game at
2198 (the limit: the map is drawn to the right edge) and 1368 (16:9).

## Open questions

- Fixed-size buffers for the map, fog of war or minimap that assume at most 1024x768.
- Map scrolling limits at the right edge of the map with a wider view.
- Mouse coordinates under cnc-ddraw's scaling (the Tzar preset sets `adjmouse=true`).

[tzar]: https://en.wikipedia.org/wiki/Tzar:_The_Burden_of_the_Crown
[haemimont]: https://www.haemimontgames.com/
