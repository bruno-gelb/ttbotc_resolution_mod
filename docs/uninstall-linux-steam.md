# Uninstall on Linux, Steam version

Run `./tzar-widescreen-linux` again, in the folder you installed from, and choose to remove the mod. It puts the
game's original files back and removes everything it added, including its setting in Steam's Proton prefix. If you
deleted the program, run the line from [the install steps](install-linux-steam.md) again.

## Without the program

Steam can put the game's files back: in your Library, right-click Tzar, then **Properties**, **Installed Files**,
[**Verify integrity of game files**][verify]. It also resets the game's settings.

Then delete what the mod added to the game folder (right-click Tzar, **Manage**, **Browse local files**): `ddraw.dll`,
`ddraw.ini`, `Shaders` and `tzar-widescreen-backup`.

[verify]: https://help.steampowered.com/faqs/view/0C48-FCBD-DA71-93EB
