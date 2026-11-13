# [Tzar: The Burden of the Crown][tzar] — widescreen resolution mod

An unofficial fan mod that runs [Tzar][tzar] ([Haemimont Games][haemimont], 2000) at a widescreen resolution, such
as 21:9 for an ultrawide monitor, so the game shows more of the map instead of stretching a 4:3 picture
([how it works](docs/how-it-works.md)).

![Tzar at 1832x768 with the left panel, scaled up to a 3440x1440 ultrawide monitor](docs/screenshots/tzar-1832x768-ultrawide.png)

*The game at 1832x768, scaled to fill a 3440x1440 monitor. The original goes up to 1024x768.*

## Install

You need [Tzar: The Burden of the Crown][tzar].

- [Windows + Steam](docs/install-windows-steam.md)
- [Windows + GOG](docs/install-windows-gog.md)
- [Linux + Steam](docs/install-linux-steam.md)
- [Linux + GOG](docs/install-linux-gog.md)

## Uninstall

Run the program again and choose to remove the mod, or let your launcher put the game's files back:

- [Windows + Steam](docs/uninstall-windows-steam.md)
- [Windows + GOG](docs/uninstall-windows-gog.md)
- [Linux + Steam](docs/uninstall-linux-steam.md)
- [Linux + GOG](docs/uninstall-linux-gog.md)

## Compared to other projects

The ones players are most likely to find, briefly. The full comparison, with the pros and cons of each against this
mod, is in [Compared to other projects](docs/compared-to-other-projects.md).

- The [HD Patch](https://www.moddb.com/games/tzar-the-burden-of-the-crown/downloads/tzar-burden-of-the-crown-hd-patch-1280x720-1920x1200-ver-30)
  (with TzarRunner) is the widescreen fix PCGamingWiki lists. It goes taller, up to 1920x1200, which this mod can't
  do yet. But it ships a modified copy of the game's program, is Windows-only, and changes your monitor's
  resolution, which gives black borders and scrolling glitches on bigger screens. This mod patches your own copy, works
  on Linux too, and scales the picture to any screen.
- The [Ready2Play Launcher](https://www.moddb.com/mods/tzar-r2p-launcher) and the
  [GOG Preservation Patch](https://www.gog.com/forum/tzar_the_burden_of_the_crown/tzar_110_english_gog_preservation_patch)
  make the game start on modern Windows and add the CD music, and the GOG patch adds the campaigns released only in
  Spain and Italy. Neither is widescreen: they scale the 4:3 picture. This mod shows more of the map.
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
reports, feature requests and help with testing are most welcome there. Testing on Windows helps the most, since I
don't currently have a machine with it: see [#7](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/7).

## License

The mod's own files (code, patches, documentation) are released under the [MIT License](LICENSE): use, change and
share them freely. That license covers only what's in this repository. The programs on the releases page also
include [cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw) by FunkyFr3sh, under its own MIT License, and the Linux
one, for the game's music, [TinySoundFont](https://github.com/schellingb/TinySoundFont) by Bernhard Schelling and
part of the FluidR3 GM soundfont by Frank Wen, both under the MIT License.

## The game and its owners

- This is an unofficial fan project. It is not affiliated with, endorsed by or connected to
  [Haemimont Games][haemimont], the developer and Steam publisher of [Tzar: The Burden of the Crown][tzar], to
  [GOG][gog], or to any other publisher or store of the game.
- [Tzar: The Burden of the Crown][tzar], its executable, data files, artwork, music and trademarks belong to their
  respective owners. This repository contains none of them, and the mod will only ever ship its own changes (patches and
  configuration), never the game's files. The screenshots show the game's art, which belongs to its owners too.
- The mod doesn't remove or get around any copy protection, and it won't. To use it, buy the game on [Steam][steam]
  or [GOG][gog].
- The game's files are only changed on your computer, in your copy. Removing the mod puts the originals back, and
  so do Steam's "Verify integrity of game files" and Heroic's "Verify and Repair".

[tzar]: https://en.wikipedia.org/wiki/Tzar:_The_Burden_of_the_Crown
[steam]: https://store.steampowered.com/app/825730/
[gog]: https://www.gog.com/en/game/tzar_the_burden_of_the_crown
[haemimont]: https://www.haemimontgames.com/
