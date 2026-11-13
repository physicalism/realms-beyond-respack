# Realm mods and packs tracker

One list of every custom mod, resource pack and datapack on the realm: what it does, its version, and what needs doing next.

**How to update (people or AI):** edit the row when something changes, keep one row per project, and use one of these statuses:
`Up to date` · `Needs update` · `Check in game` · `In progress` · `Backup` · `Inactive`.
"Made with" is `Claude`, `ChatGPT`, `Both`, or `?` if unknown.

_Last updated: 2026-11-13_

## Needs attention

| Project | Status | Next action |
| --- | --- | --- |
| Realms Beyond (pack) | Needs update | v0.1.56 is pushed; newer work (kitchen props, florist sign, Chef Ivy backups) is uncommitted. Confirm the v0.1.56 GitHub release is published for the Loader |
| Realms Beyond Cosmetics (SimpleBlood) | Needs update | Source 0.1.41, newest JAR 0.1.38. Run `cd ~/Desktop/Project/realms-beyond-cosmetics && python3 build.py --simpleblood` |
| 3D Framed Maps | In progress | Current relief is shading-based; goal is true-height, diorama-style maps |
| Grand Teleport (26.3 port) | Check in game | 26.3 JAR built; README lists up to 26.2 only |
| Cosy Snails | Check in game | Confirm the JAR has the v2 side-on snails |
| Realms Beyond Vegan | Check in game | Built without Minecraft; test the recipes on the realm |
| Right-Click Harvest | Check in game | 100% farming XP and no-trample guard untested; install unzipped |

## Everything

| Project | Type | Status | Version | Runs on | Who installs | Key features | Made with | Folder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Realms Beyond | Resource pack | Needs update | 0.1.56 | Realm (via Loader) | Everyone | 96 banners, stag war banner, Korra disc 13, connected paths/farmland/dirt, Ivy paintings and plushies, signs, forge and anvil, kitchen props, stag fountain | Claude | `resource-pack/` |
| Realms Beyond Cosmetics (SimpleBlood) | Fabric client mod | Needs update | 0.1.38 (source 0.1.41) | Client | Each player who should see cosmetics | Bloody footprints, hand drips, Petal chainsaw and face drips, lightning bolt, wizard hat, blinks, Wardrobe screen | Claude | `realms-beyond-cosmetics/` |
| Realms Beyond Cosmetics (standalone) | Fabric client mod | Backup | 0.1.33 | Client | Only without SimpleBlood | Same cosmetics with sprite blood; install only one edition | Claude | `realms-beyond-cosmetics/` |
| Realms Beyond Loader | Fabric client mod | Up to date | 1.2.0 | Client | Henry and brother | Downloads the latest published pack release on joining the realm | ? | `realms-beyond-loader/` |
| 3D Framed Maps | Fabric client mod | In progress | 1.0.1 | Client | Optional | Framed maps within 32 blocks render as 3D relief | Claude | `3d-maps/` |
| Item Frame Visibility | Fabric client mod | Up to date | 1.0.0 | Client | Optional | Stops large framed models vanishing off-screen (128 blocks) | ? | `item-frame-visibility/` |
| Grand Teleport (26.3 port) | Fabric client mod | Check in game | 1.0.0 | Client | Optional | GTA-style cinematic teleport camera, `/gtp` | ? | `grand-teleport-26.3/` |
| Cosy Snails | Fabric client mod (needs Cosy Critters) | Check in game | 1.0.0 | Client | Optional | Snails on grass/moss/leaves, more in rain, slime trails, hide in shell | Claude | `cosy-snails/` |
| Realms Beyond Vegan | Datapack | Check in game | 1.0 | Realm world | Realm | 18 plant-based recipes, plant food for pets | Claude | not in workspace |
| Right-Click Harvest | Datapack | Check in game | v3 + XP | Realm world | Realm | Right-click harvest and replant, farming XP, trample guard | Claude | not in workspace |
| Gentle Fishing | Datapack | Up to date | 1.0 | Realm world | Realm | Fishing gives junk instead of fish | Claude | not in workspace |
| Realm Cleanup | Datapack (one-off) | Up to date | 1.0 | Realm world | Realm | Removes leftover scoreboards; run once then uninstall | Claude | not in workspace |
| Cosmetics-Test | Resource pack (test) | Inactive | – | Client | Nobody | Test overrides for cosmetics | Claude | `Cosmetics-Test/` |
