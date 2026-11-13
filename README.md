# [Tzar: The Burden of the Crown][tzar] — widescreen resolution mod

An unofficial fan mod that runs [Tzar][tzar] ([Haemimont Games][haemimont], 2000) at a widescreen resolution, such
as 21:9 for an ultrawide monitor, so the game shows more of the map instead of stretching a 4:3 picture
([how it works](docs/how-it-works.md)).

![Tzar at 1832x768 with the left panel, scaled up to a 3440x1440 ultrawide monitor](docs/screenshots/tzar-1832x768-ultrawide.png)

*The game at 1832x768, scaled to fill a 3440x1440 monitor. The original goes up to 1024x768.*

## Install

You need [Tzar: The Burden of the Crown][tzar] from Steam or [GOG][gog].

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
include [cnc-ddraw](https://github.com/FunkyFr3sh/cnc-ddraw) by FunkyFr3sh, under its own MIT License.

## The game and its owners

- This is an unofficial fan project. It is not affiliated with, endorsed by or connected to
  [Haemimont Games][haemimont], the developer and Steam publisher of [Tzar: The Burden of the Crown][tzar], to
  [GOG][gog], or to any other publisher or store of the game.
- [Tzar: The Burden of the Crown][tzar], its executable, data files, artwork, music and trademarks belong to their
  respective owners. This repository contains none of them, and the mod will only ever ship its own changes (patches and
  configuration), never the game's files. The screenshots show the game's art, which belongs to its owners too.
- The mod doesn't remove or get around any copy protection, and it won't. To use it, buy the game on [Steam][tzar]
  or [GOG][gog].
- The game's files are only changed on your computer, in your copy. Removing the mod puts the originals back, and
  so do Steam's "Verify integrity of game files" and Heroic's "Verify and Repair".

[tzar]: https://store.steampowered.com/app/825730/
[gog]: https://www.gog.com/en/game/tzar_the_burden_of_the_crown
[haemimont]: https://www.haemimontgames.com/
