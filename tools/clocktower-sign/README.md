# Sign particle references

13 November 2026: the blacksmith, florist, and town clocktower models now set
`textures.particle` to their existing `textures.sign` atlas. The caps generator
emits both entries; the build validator checks them. Geometry, displays, and
textures were preserved. Pre-edit models are in
`../../builds/sign-caps-backups/particle-fix-2026-11-13/`.

The supplied sign-only ZIP could not be downloaded, so direct patch comparison
was unavailable. The correction was derived from the current source instead.
An independent audit resolved particles for all 1,994 concrete models using
the installed Minecraft 26.3 client resources. The abstract banner base requires
its children's cloth slot; all 96 children resolved correctly.

Both required build commands currently fail at the existing Elphaba broom
model/generator equality check. This task did not alter those assets or bypass
that check. No successful ZIP build or in-game visual verification is claimed.
The live Fabric Realm `Realms Beyond` symlink still resolves to this repository.
