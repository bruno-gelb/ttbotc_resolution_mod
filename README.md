# [Tzar: The Burden of the Crown][tzar] — widescreen resolution mod

An unofficial fan mod that runs [Tzar][tzar] ([Haemimont Games][haemimont], 2000) at a widescreen resolution, such
as 21:9 for an ultrawide monitor, so the game shows more of the map instead of stretching a 4:3 picture
([how it works](docs/how-it-works.md)).

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

To change the resolution, run the program again. Run it again after a Steam update too, to put the mod back.

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

## Uninstall

Run the program again and choose to remove the mod. It puts the game's original files back.

Without the program, Steam can put them back too: in your Library, right-click Tzar, then **Properties**,
**Installed Files**, [**Verify integrity of game files**](https://help.steampowered.com/faqs/view/0C48-FCBD-DA71-93EB).
That leaves the few files the mod added in the game folder: delete `ddraw.dll`, `ddraw.ini`, `Shaders` and
`tzar-widescreen-backup` too.

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
