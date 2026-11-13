# How it works

[Tzar: The Burden of the Crown][tzar] was made for screens up to 1024x768. The mod changes five things, and on Linux a
sixth, and nothing else: the game's rules, AI and saves stay exactly as they were. The program keeps the original files
and puts them back when you remove the mod.

1. **14 bytes in the game's program** (`Tzar_.exe` on Steam, `Tzar.exe` on GOG: the same program). Four make the game's
   1024x768 mode use your width instead. Eight fix a limit in how the game redraws the map: to save work, it only
   redraws the parts of the screen that changed, and its record of those parts only reached 1024 pixels across. Past
   that point nothing was ever redrawn, and the mouse cursor left a trail. Now each entry in that record covers twice
   the width, so it reaches 2048 pixels. The last two stop the game from refusing to start ("Invalid TZAR configuration
   detected") when your sound devices differ from the ones its settings were saved with, which under Linux is almost
   always. On Linux, 9 more bytes change, for the music: see 6.
2. **The screen layout.** The game reads where the map, the minimap and the buttons go from a text file,
   `DATA/LAYOUT.INI`. The mod gives the map view the extra width.
3. **The frame around the map**, a picture the game draws under the map and the panels, is made wider to match,
   from the game's own picture.
4. **[cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw)**, a popular open-source replacement for DirectDraw, the
   graphics library old Windows games use. No monitor has a mode like 1832x768, so cnc-ddraw offers one to the game and
   scales the picture up to fill your screen. On Linux, the program also tells Wine (Steam's Proton, or the one
   Heroic runs the game with), in the game's own Wine settings, to use cnc-ddraw instead of its built-in DirectDraw.
5. **The version line on the main menu**, in its bottom-right corner, gets the mod's name and version in front:
   `ttbotc_resolution_mod 0.4.0. game Version 1.10, 2/03/2002`. The game takes the word "Version" from its text
   file `LOCAL/STRINGS.INI`, so that one line is all that changes.
6. **On Linux, the music.** The game's music is MIDI: notes, which Windows turns into sound with a synthesizer of its
   own. Wine has none, so on Linux the music was silent and only the sound effects played. The mod brings one:
   `TZMUS.dll`, a small library built from the mod's own C code ([native/tzmus](../native/tzmus/)) around the
   open-source synthesizer [TinySoundFont](https://github.com/schellingb/TinySoundFont), and `TZMUS.sf2`, the
   instruments the music uses, taken from the FluidR3 GM soundfont (35 MB of its 148). In the game's program, the name
   of the Windows library it takes its sound functions from, `WINMM.dll`, becomes `TZMUS.dll`: those 9 bytes. So the
   game, and only the game, gets its music from the mod's synthesizer, while its sound effects go on to Windows' library
   as before. Windows keeps its own synthesizer and gets none of this. The library is compiled with Zig's C compiler,
   which builds Windows programs on Linux and installs with the mod's other development tools: see
   [CONTRIBUTING.md](../CONTRIBUTING.md#running-from-source).

The details, down to the addresses in the game's code, are in [findings.md](findings.md).

[tzar]: https://en.wikipedia.org/wiki/Tzar:_The_Burden_of_the_Crown
