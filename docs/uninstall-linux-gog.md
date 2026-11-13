# Uninstall on Linux, GOG version

Run `./tzar-widescreen-linux` again, in the folder you installed from, and choose to remove the mod. It puts the
game's original files back and removes everything it added, including its setting in Heroic's Wine prefix. If you
deleted the program, run the line from [the install steps](install-linux-gog.md) again.

## Without the program

[Heroic](https://heroicgameslauncher.com/) can put the game's files back: the game's **Verify and Repair**.

Then delete what the mod added to the game folder (Heroic's default is `~/Games/Heroic/Tzar`): `ddraw.dll`,
`ddraw.ini`, `Shaders` and `tzar-widescreen-backup`.
