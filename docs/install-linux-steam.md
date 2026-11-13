# Install on Linux, Steam version

1. Start Tzar once from Steam and quit it, so that Steam sets the game up. If it says "Invalid TZAR configuration
   detected", press OK: the mod fixes that too.
2. Run this in a terminal:

   ```bash
   curl -fLO https://github.com/bruno-gelb/ttbotc_resolution_mod/releases/latest/download/tzar-widescreen-linux && chmod +x tzar-widescreen-linux && ./tzar-widescreen-linux
   ```

3. Press Enter twice: the program finds the game, picks the resolution that matches your screen and installs the mod.
4. Play from Steam as usual.

To change the resolution, run `./tzar-widescreen-linux` again. Run it again after a Steam update too, to put the mod
back. To remove the mod, see [Uninstall](../README.md#uninstall).

## More

- Besides the width that matches your screen, the program offers 1232x768 for 16:10 screens, 1368x768 for 16:9 and
  1832x768 for 21:9 ultrawides, or any width from 1032 to 2198. The height is always 768, and the picture is scaled
  to fill your screen, keeping its shape.
- `--width` skips the question, for example `./tzar-widescreen-linux --width 1368`. `--help` lists the rest.
- If it can't find the game, copy the program into the game's folder (in Steam: right-click Tzar, **Manage**,
  **Browse local files**) and run it from there.
