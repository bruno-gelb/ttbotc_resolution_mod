# [Tzar: The Burden of the Crown][tzar] — widescreen resolution mod

An unofficial fan mod that runs [Tzar][tzar] ([Haemimont Games][haemimont], 2000) at a widescreen resolution, such
as 21:9 for an ultrawide monitor, so the game shows more of the map instead of stretching a 4:3 picture.

![Tzar at 1832x768 with the left panel, scaled up to a 3440x1440 ultrawide monitor](docs/screenshots/tzar-1832x768-ultrawide.png)

*The game at 1832x768, scaled to fill a 3440x1440 monitor. The original goes up to 1024x768.*

## Install

You need [Tzar: The Burden of the Crown][tzar] from Steam (game version 1.10), installed. Other versions, like GOG's
or the original CD, aren't supported yet ([#9](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/9)).

1. Download the program for your system from the [latest release](https://github.com/bruno-gelb/ttbotc_resolution_mod/releases/latest):
   `tzar-widescreen-...-windows.exe` for Windows, `tzar-widescreen-...-linux` for Linux.
2. Run it.
   - **Windows:** double-click it. Windows may say it protected your PC, because the program isn't signed: click
     **More info**, then **Run anyway**.
   - **Linux:** open a terminal in the folder you downloaded it to and run:

     ```bash
     chmod +x tzar-widescreen-*-linux && ./tzar-widescreen-*-linux
     ```

3. It finds the game, tells you what it's going to change and asks first. Press Enter to install.
4. **Linux only, once:** in Steam, right-click Tzar, then Properties, General, and put this in Launch Options:

   ```
   WINEDLLOVERRIDES="ddraw=n,b" %command%
   ```

5. Play from Steam as usual. Keep the game's layout with the panel on the left: the other two don't work with the
   mod yet ([#5](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/5)).

If it can't find the game, copy the program into the game's folder and run it from there.

**To remove the mod**, run the program again: it sees the mod and offers to put the game's original files back. After
a Steam update or "Verify integrity of game files", run it again to apply the mod again.

## How it works

The game was made for screens up to 1024x768. The mod changes four things, and nothing else: the game's rules, AI
and saves stay exactly as they were. The program keeps the original files and puts them back when you remove the
mod.

1. **14 bytes in the game's program** (`Tzar_.exe`). Four make the game's 1024x768 mode use 1832x768 instead.
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
   graphics library old Windows games use. No monitor has a 1832x768 mode, so cnc-ddraw offers one to the game and
   scales the picture up to fill your screen.

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
