# Why not existing projects

Other ways players make [Tzar: The Burden of the Crown][tzar] work on modern PCs, compared with this mod. Most of them
come from the Steam thread [DONT BUY][thread], PCGamingWiki's [page on the game][pcgw] and the GOG forum. Checked
2026-11-13 ([#22](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/22)).

For comparison, this mod ([how it works](how-it-works.md)):

- patches 14 bytes of the game's own program, widens the screen layout and the frame around the map, and adds
  [cnc-ddraw][cnc-ddraw] to scale the picture to your screen;
- shows more of the map, at any width from 1032 to 2198 and a height of 768, with the left panel only;
- installs and uninstalls with one program, and keeps the originals;
- is made for the Steam and GOG versions, on Windows and on Linux (Proton, Heroic), though it hasn't been tried on
  Windows yet ([#7](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/7));
- plays the music on Linux;
- is MIT-licensed and ships none of the game's files.

Every project here is someone's work to keep Tzar playable, and many players are happy with them. This page is to
help you pick the one that suits you, not to judge anyone's work. Sorted from the most viable and popular to the
least; pros and cons are compared with this mod.

| Solution | How it works | Pros | Cons |
| --- | --- | --- | --- |
| [Ready2Play Launcher][r2p] (LuKeStorm, 2023, updated 2026-03, ~4,700 downloads, pinned on Reddit) | A launcher unpacked into the game folder. It sets up cnc-ddraw, a CD audio wrapper, its own config without the registry, and an optional Community Balance Mod. | The fix pinned on Reddit, so the one players find first. CD music instead of MIDI. Choice of renderer and shaders, windowed and borderless modes, from a launcher. Skips the intro. Removes the "Invalid TZAR configuration" error on Windows too. Balance mod. Actively maintained, with Steam and GOG support. | No widescreen: the 4:3 picture is scaled or stretched, the map view doesn't grow. Windows 7-11 only, no Linux support. A bigger download: 56 MB, against 9 MB for this mod's Windows program. Replaces game files, texts included: its own English and German copies, older than the ones Steam and GOG ship. Some players still see crashes in missions, as with the original game. |
| [ReTzar][retzar] (ColCarlo, 2026-10, GPL-3.0, on top of Reddit in 2026-11) | A remake of the whole game in Rust and Bevy that reads the art and data from your copy of Tzar (Steam, GOG or CD): a new engine with the original AI and mission scripts. | Fresh and getting attention: on top of Reddit right now. Crisp scaling up to 4K and any screen shape. HD art packs and extras. Experimental native macOS and Linux builds. Open source. | A new engine, a month old, so it plays the way ReTzar rebuilds the game rather than the original program itself. Linux and macOS are build-from-source and experimental. This mod keeps the original game, engine, AI and saves. |
| [HD Patch 3.4][hd] (OLDodin, 2021-2025, ~8,800 downloads) | Replaces the game's exe with a modified one, for every game version, and adds two launchers: `TzarSettings.exe` picks the resolution, `TzarRunner.exe` starts the game. The **TzarRunner** players mention in the thread is this patch. Shows more of the map. Needs .NET Framework 2.0 and the Visual C++ 2015 Redistributable. Source of the two launchers included, no license stated. | Taller resolutions: 1280x720 to 1920x1200, so more of the map vertically too (this mod: 768 high only, [#2][i2]). The fix PCGamingWiki lists. Years of player testing and fixes (Shift, Ctrl+right click, hotkeys). Works with CD audio emulation. | Ships a modified copy of the game's program instead of patching yours. Windows only: needs .NET 2.0 and VC++ 2015, nothing about Linux. Changes the monitor's real resolution, so black borders, an off-center picture and scrolling glitches on screens bigger than the game's mode, until the Windows resolution is lowered to match. Left layout only, like this mod, and changing the layout in the game can crash it. A fixed list of resolutions, no 21:9. Manual install, no uninstall. |
| [Tzared][tzared] (nehhon) | A free remake of the game, played in the browser at tza.red or as an app for Windows, macOS and Linux, built around online multiplayer: ranked games, leagues and lobbies. | You don't need the original game. Native widescreen and high resolutions. Free online play with a live community, which the original lacks (it has LAN only, online needs GameRanger and the like). | Not the original game: a new engine, with its own rules, AI and balance. Focused on multiplayer rather than the original campaigns. For playing the original itself, this mod or another fix is still needed. |
| [GOG Preservation Patch][gogpp] (castanhojfc, 2024-12) | A setup program that upgrades 1.10 to 1.11 and to the Anthology Edition: replaces images, adds a pre-configured `tzar.ini`, cnc-ddraw 7.0 set up to look like a CRT, and the CDAudio proxy for the CD music. Download from Mega. | All the campaigns released only in Spain and Italy, translated to English. CD music. Game version 1.11. Fixes the "Invalid TZAR configuration" error on Windows. | No widescreen, on purpose: the author prefers the original look. Tested only with the GOG version. Replaces many game files. On Linux under Proton the configuration error stays. |
| [cnc-ddraw][cnc-ddraw] alone, with `DIRECTXDEVICE=0` ([GOG forum][cnc-gog]) | A DirectDraw replacement you copy into the game folder, set to "Fullscreen Upscaled", after switching the game to DirectDraw in `tzar.ini`. This mod and most fixes above build on it. | Small, open source (MIT), and widely used. Windowed and borderless modes, shaders and VSync through its own config. | Manual setup. No widescreen: the 4:3 picture is only scaled. Doesn't fix the "Invalid TZAR configuration" error under Linux. |
| [tzaronline.com][tzaronline] "Tzar mod" | A community site with a launcher pack (all campaigns, 500+ maps, 10+ mods, replays and stats tools) and a separate patched Windows 11 build with `TzarSettings.exe` (1280x768 or 1920x1080). Its own page says the full-screen mod cracks the game. Downloads from Mega. | Lots of community content in one place. Online play guides (GameRanger, Radmin VPN). | Its page says the full-screen mod cracks the game, which this mod doesn't do: it leaves copy protection alone. Mostly scaling only. No license or source published. Windows only. |
| CD audio (Redbook) wrapper, the [CDAudio proxy][cdaudio] | A `winmm.dll` replacement that plays the CD's music tracks from audio files, for the game's `CDAUDIO` mode. The Ready2Play Launcher and the GOG Preservation Patch include one. | The CD soundtrack, which players say sounds much better than the MIDI. | Not a display fix. Needs the CD's music tracks as audio files, from a disc or a pack; the site the thread's copy came from is gone. Volume only in its .ini, and the music loops everywhere, briefings and victory screens included. Windows only, and it would clash with this mod's Linux music library. |

## Crashes

The thread reports random maps crashing on generation and missions crashing every 2-3 minutes. None of the fixes
above claims to fix these yet, this mod included. Two leads from them, neither tested yet:

- The Ready2Play author suggests `singlecpu=false` in cnc-ddraw's `ddraw.ini` against crashes in missions. This mod
  uses cnc-ddraw too, with its default `singlecpu=true`.
- PCGamingWiki notes that 32-bit games may need the large address aware (LAA) flag to run properly on modern
  machines. `Tzar_.exe` doesn't have it.

## What this mod can learn

It's in the mod's [GitHub issues](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues).

## Not compared

PCGamingWiki also lists unofficial patches 1.13 and 1.16b, which change the game's balance, not how it runs, and
translations of the campaigns released only in Spain and Italy. They don't touch the screen, so they may work
alongside this mod, untested.

[tzar]: https://en.wikipedia.org/wiki/Tzar:_The_Burden_of_the_Crown
[thread]: https://steamcommunity.com/app/825730/discussions/0/796715497279267166/
[pcgw]: https://www.pcgamingwiki.com/wiki/Tzar:_The_Burden_of_the_Crown
[cnc-ddraw]: https://github.com/FunkyFr3sh/cnc-ddraw
[cnc-gog]: https://www.gog.com/forum/tzar_the_burden_of_the_crown/enable_directdraw_and_use_cncddraw
[hd]: https://www.moddb.com/games/tzar-the-burden-of-the-crown/downloads/tzar-burden-of-the-crown-hd-patch-1280x720-1920x1200-ver-30
[r2p]: https://www.moddb.com/mods/tzar-r2p-launcher/downloads/tzar-ready2play-launcher
[tzared]: https://tza.red/
[gogpp]: https://www.gog.com/forum/tzar_the_burden_of_the_crown/tzar_110_english_gog_preservation_patch
[retzar]: https://github.com/ColCarlo/ReTzar
[tzaronline]: https://tzaronline.com/
[cdaudio]: https://sourceforge.net/p/dxwnd/discussion/general/thread/5acf883519/
[i2]: https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/2
