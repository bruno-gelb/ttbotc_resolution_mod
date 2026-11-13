# [Tzar: The Burden of the Crown][tzar] — widescreen resolution mod

An unofficial fan mod that runs [Tzar][tzar] ([Haemimont Games][haemimont], 2000) at a widescreen resolution, such
as 21:9 for an ultrawide monitor, so the game shows more of the map instead of stretching a 4:3 picture.

![Tzar at 1832x768 with the left panel, scaled up to a 3440x1440 ultrawide monitor](docs/screenshots/tzar-1832x768-ultrawide.png)

*The game at 1832x768, scaled to fill a 3440x1440 monitor. The original goes up to 1024x768.*

## Install

You need [Tzar: The Burden of the Crown][tzar] from Steam. The GOG and CD versions aren't supported yet
([#9](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/9)).

1. Get the program and start it:
   - **Windows:** [download it][windows] and double-click it.
   - **Linux:** start the game from Steam once, so that Proton sets it up. Then run this in a terminal:

     ```bash
     curl -fLO https://github.com/bruno-gelb/ttbotc_resolution_mod/releases/latest/download/tzar-widescreen-linux && chmod +x tzar-widescreen-linux && ./tzar-widescreen-linux
     ```

2. Press Enter twice: the program finds the game, picks the resolution that matches your screen and installs the mod.
3. Play from Steam as usual.

To change the resolution or remove the mod, run the program again. Run it again after a Steam update too, to put the
mod back.

<details>
<summary>Windows says it protected your PC</summary>

The program isn't signed yet ([#25](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/25)), so Windows
doesn't know it. Click **More info**, then **Run anyway**.

</details>

<details>
<summary>Other resolutions, the command line, and when it can't find the game</summary>

- Besides the width that matches your screen, the program offers 1232x768 for 16:10 screens, 1368x768 for 16:9 and
  1832x768 for 21:9 ultrawides, or any width from 1032 to 2198. The height is always 768, and the picture is scaled
  to fill your screen, keeping its shape.
- From a terminal, `--width` skips the question, for example `./tzar-widescreen-linux --width 1368`. `--help` lists
  the rest.
- If it can't find the game, copy the program into the game's folder and run it from there.

</details>

## How it works

The game was made for screens up to 1024x768. The mod changes four things, and nothing else: the game's rules, AI
and saves stay exactly as they were. The program keeps the original files and puts them back when you remove the
mod.

1. **14 bytes in the game's program** (`Tzar_.exe`). Four make the game's 1024x768 mode use your width instead.
   Eight fix a limit in how the game redraws the map: to save work, it only redraws the parts of the screen that
   changed, and its record of those parts only reached 1024 pixels across. Past that point nothing was ever redrawn,
   and the mouse cursor left a trail. Now each entry in that record covers twice the width, so it reaches 2048
   pixels. The last two stop the game from refusing to start ("Invalid TZAR configuration detected") when your
   sound devices differ from the ones its settings were saved with, which under Linux is almost always.
2. **The screen layout.** The game reads where the map, the minimap and the buttons go from a text file,
   `DATA/LAYOUT.INI`. The mod gives the map view the extra width.
3. **The frame around the map**, a picture the game draws under the map and the panels, is made wider to match,
   from the game's own picture.
4. **[cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw)**, a popular open-source replacement for DirectDraw, the
   graphics library old Windows games use. No monitor has a mode like 1832x768, so cnc-ddraw offers one to the game and
   scales the picture up to fill your screen. On Linux, the program also tells Proton, in the game's own Proton
   settings, to use cnc-ddraw instead of its built-in DirectDraw.

The details, down to the addresses in the game's code, are in [docs/findings.md](docs/findings.md).

## Compared to other projects

- [ReTzar](https://github.com/ColCarlo/ReTzar) is a remake of the whole game in Rust and Bevy (GPL-3.0) that uses
  the art and data from your copy of [Tzar][tzar]: a new engine with crisp scaling up to 4K, HD art packs, extras and
  experimental native macOS and Linux builds. This mod goes the other way: it keeps the original 2002 game,
  including its engine, AI and saves, and changes only how big a screen it draws on, with a few bytes of patches and
  config.
- [Tzared](https://tza.red/) is a free remake you play in the browser or as an app, built around online
  multiplayer: ranked games, leagues and lobbies. You don't need the original game. This mod is for playing the
  original itself.

## Help wanted

Known problems and plans are [GitHub issues](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues). Bug
reports, feature requests and help with testing are most welcome there. Testing on Windows and with the GOG
version helps the most, since the mod hasn't been tried on either yet: see
[#7](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/7) and
[#9](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/9).

## License

The mod's own files (code, patches, documentation) are released under the [MIT License](LICENSE): use, change and
share them freely. That license covers only what's in this repository. The programs on the releases page also
include [cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw) by FunkyFr3sh, under its own MIT License.

## The game and its owners

- This is an unofficial fan project. It is not affiliated with, endorsed by or connected to
  [Haemimont Games][haemimont], the developer and Steam publisher of [Tzar: The Burden of the Crown][tzar], or to
  any other publisher of the game.
- [Tzar: The Burden of the Crown][tzar], its executable, data files, artwork, music and trademarks belong to their
  respective owners. This repository contains none of them, and the mod will only ever ship its own changes (patches and
  configuration), never the game's files. The screenshots show the game's art, which belongs to its owners too.
- The mod doesn't remove or get around any copy protection, and it won't. To use it, [buy the game][tzar].
- The game's files are only changed on your computer, in your copy. Removing the mod puts the originals back, and
  so does Steam's "Verify integrity of game files".

[tzar]: https://store.steampowered.com/app/825730/
[haemimont]: https://www.haemimontgames.com/
[windows]: https://github.com/bruno-gelb/ttbotc_resolution_mod/releases/latest/download/tzar-widescreen-windows.exe
