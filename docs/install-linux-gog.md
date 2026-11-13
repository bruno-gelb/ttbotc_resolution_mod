# Install on Linux, GOG version

This is for the GOG version installed with [Heroic](https://heroicgameslauncher.com/).

1. Start Tzar once from Heroic and quit it, so that Heroic sets the game up. If it says "Invalid TZAR configuration
   detected", press OK: the mod fixes that too.
2. Run this in a terminal:

   ```bash
   curl -fLO https://github.com/bruno-gelb/ttbotc_resolution_mod/releases/latest/download/tzar-widescreen-linux && chmod +x tzar-widescreen-linux && ./tzar-widescreen-linux
   ```

3. Press Enter twice: the program finds the game, picks the resolution that matches your screen and installs the mod.
4. Play from Heroic as usual.

To change the resolution, run `./tzar-widescreen-linux` again. Run it again after Heroic updates the game too, to put
the mod back. To remove the mod, see [Uninstall](../README.md#uninstall).

## More

- Besides the width that matches your screen, the program offers 1232x768 for 16:10 screens, 1368x768 for 16:9 and
  1832x768 for 21:9 ultrawides, or any width from 1032 to 2198. The height is always 768, and the picture is scaled
  to fill your screen, keeping its shape.
- `--width` skips the question, for example `./tzar-widescreen-linux --width 1368`. `--help` lists the rest.
- If it can't find the game, copy the program into the game's folder (Heroic's default is `~/Games/Heroic/Tzar`) and
  run it from there.
- With another launcher, like Lutris or plain Wine, the mod installs too, but the program can't tell which Wine
  settings run the game: add `WINEDLLOVERRIDES="ddraw=n,b"` to the game's environment yourself, as it says.
