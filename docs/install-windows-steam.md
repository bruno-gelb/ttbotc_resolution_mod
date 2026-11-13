# Install on Windows, Steam version

1. [Download the program][download] and double-click it. Windows may say it protected your PC, because the program
   isn't signed yet ([#25](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/25)): click **More info**,
   then **Run anyway**.
2. Press Enter twice: the program finds the game, picks the resolution that matches your screen and installs the mod.
3. Play from Steam as usual.

To change the resolution, run the program again. Run it again after a Steam update too, to put the mod back. To
remove the mod, see [Uninstall](../README.md#uninstall).

The mod hasn't been tried on Windows yet: if something goes wrong, please tell us in
[#7](https://github.com/bruno-gelb/ttbotc_resolution_mod/issues/7).

## More

- Besides the width that matches your screen, the program offers 1232x768 for 16:10 screens, 1368x768 for 16:9 and
  1832x768 for 21:9 ultrawides, or any width from 1032 to 2198. The height is always 768, and the picture is scaled
  to fill your screen, keeping its shape.
- From a terminal, `--width` skips the question, for example `tzar-widescreen-windows.exe --width 1368`. `--help`
  lists the rest.
- If it can't find the game, copy the program into the game's folder (in Steam: right-click Tzar, **Manage**,
  **Browse local files**) and run it from there.

[download]: https://github.com/bruno-gelb/ttbotc_resolution_mod/releases/latest/download/tzar-widescreen-windows.exe
