# Realm mods and packs tracker

One list of custom mods, patches, resource packs and datapacks used or being developed for the Realm: what each does, its recorded version, and what needs doing next. Entries do **not** by themselves prove installation or publication.

**How to update (people or AI):** edit the row when something changes, keep one row per project, and use one of these statuses:
`Up to date` · `Needs update` · `Check in game` · `In progress` · `Backup` · `Inactive`.
"Made with" is `Claude`, `ChatGPT`, `Both`, or `?` if unknown. Versions describe the latest **evidenced build/source**, not necessarily the installed JAR or a published release. Record uncertainty rather than guessing.

_Last reviewed: 2026-11-15 for resource-pack source and Git Pack Manager deployment. Other project rows retain earlier evidence and have not been re-audited._

## Needs attention

| Project | Status | Next action |
| --- | --- | --- |
| Realms Beyond (pack) | Check in game | Git Pack Manager deployment verified; server builds now identify the exact source commit. Current nature catalogue and rarity changes validate and regenerate exactly. Latest lotus petal correction still needs shader review. See `docs/GIT-PACK-MANAGER.md`. |
| Realms Beyond Cosmetics (SimpleBlood) | In progress | Later test builds supersede the old 0.1.38 entry: Cosmetics v0.1.48 and SimpleBlood rb47 are evidenced, but their combined installation and in-game behaviour are unconfirmed. Verify compatible JARs, mannequin expressions, and first-person/Paper Doll blood; avoid claiming the F5-only issue is fixed. |
| 3D Framed Maps | In progress | 2.8.1-alpha.30 built: broader crop coverage, restored pre-grounding stair heights, and retained smoke optimisation; not installed or visually verified. |
| Grand Teleport (26.3 port) | Check in game | Test the 26.3 build's cinematic teleport and `/gtp`; check interaction with the Safe Map Teleport patch and Distant Horizons LOD loading. |
| Realms Safe Map Teleport | Check in game | Verify the updated compatibility patch with Grand Teleport's teleport method and the temporary Distant Horizons quality/CPU bridge. Current integrated version and installation are unverified. |
| Touch'n Motion horse compatibility patch | In progress | Rider alignment was reported fixed, but horse movement animation was lost; verify the later refinement against Touch'n Motion 1.0.5, FA Player Animations and Not Enough Animations without restoring rider displacement. |
| Cosy Snails | Check in game | Confirm the installed JAR contains the v2 side-on snails. |
| Realms Beyond Vegan | Check in game | Built without Minecraft; test the recipes and pet food on the Realm. |
| Right-Click Harvest | Check in game | Install the unzipped datapack and test 100% farming XP and the no-trample guard. |

## Everything

| Project | Type | Status | Version | Runs on | Who installs | Key features | Made with | Folder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Realms Beyond | Resource pack | Check in game | Base 0.1.57 + Git source revision (automatic builds) | Modrinth Fabric server via Git Pack Manager | Server offers pack to players; Loader optional | Existing decorations, 95 This Rocks! props, sparse branches/pinecones, reduced large-rock rarity, and lotus surface corrections; visual review pending | Both | `resource-pack/` |
| Realms Beyond Cosmetics (SimpleBlood) | Fabric client mod | In progress | Cosmetics 0.1.48 test; SimpleBlood rb47 test (installed versions unknown) | Client | Each player who should see cosmetics | Bloody footprints, hand drips, Petal chainsaw and Carrie face drips, lightning bolt, wizard hat, Wardrobe; blinking settings changed and mannequin expressions experimental; first-person/Paper Doll blood unresolved | Both | `realms-beyond-cosmetics/` |
| Realms Beyond Cosmetics (standalone) | Fabric client mod | Backup | 0.1.33 | Client | Only without SimpleBlood | Same cosmetics with sprite blood; install only one edition | Claude | `realms-beyond-cosmetics/` |
| Realms Beyond Loader | Fabric client mod | Inactive | 1.2.0 (recorded; installation not re-audited) | Client | Optional for legacy release downloads | Superseded on the Modrinth server by Git Pack Manager; keep source for optional release/singleplayer distribution | ? | `realms-beyond-loader/` |
| 3D Framed Maps | Fabric client mod | In progress | 2.8.1-alpha.30 | Client | Optional | Flat landscape with captured textured block models; v8 detail cache, geometry budgets, simplified fallback; current build in `3d-maps/build/`; Broader crops/farmland, original stair heights restored, optimised billowing smoke; 16-block range/session snapshots; not installed or published | Claude / Codex | `3d-maps/` |
| Item Frame Visibility | Fabric client mod | Up to date | 1.0.0 | Client | Optional | Stops large framed models vanishing off-screen (128 blocks) | ? | `item-frame-visibility/` |
| Grand Teleport (26.3 port) | Fabric client mod | Check in game | 1.0.0 (built; in-game status unverified) | Client | Optional | GTA-style cinematic teleport camera, `/gtp`; check Safe Map Teleport interaction and DH LOD loading | ? | `grand-teleport-26.3/` |
| Realms Safe Map Teleport | Fabric client mod (custom patch) | Check in game | 0.1.1 base; later integration patch version unverified | Client | Optional | Safe teleport from Xaero-style maps; Grand Teleport method compatibility and temporary DH loading improvements require verification | ChatGPT | Source folder not verified |
| Touch'n Motion horse compatibility patch | Patched Fabric client mod | In progress | Touch'n Motion 1.0.5; rider-fix refinement (build number unverified) | Client | Players using Touch'n Motion | Fix rider offset/floating on horses while retaining animation compatibility with FA Player Animations and Not Enough Animations | ChatGPT | Patch/JAR; source folder not verified |
| Cosy Snails | Fabric client mod (needs Cosy Critters) | Check in game | 1.0.0 | Client | Optional | Snails on grass/moss/leaves, more in rain, slime trails, hide in shell | Claude | `cosy-snails/` |
| Realms Beyond Vegan | Datapack | Check in game | 1.0 | Realm world | Realm | 18 plant-based recipes, plant food for pets | Claude | not in workspace |
| Right-Click Harvest | Datapack | Check in game | v3 + XP | Realm world | Realm | Right-click harvest and replant, farming XP, trample guard | Claude | not in workspace |
| Gentle Fishing | Datapack | Up to date | 1.0 | Realm world | Realm | Fishing gives junk instead of fish | Claude | not in workspace |
| Realm Cleanup | Datapack (one-off) | Up to date | 1.0 | Realm world | Realm | Removes leftover scoreboards; run once then uninstall | Claude | not in workspace |
| Cosmetics-Test | Resource pack (test) | Inactive | – | Client | Nobody | Test overrides for cosmetics | Claude | `Cosmetics-Test/` |

## Verification notes

- **Pack distribution:** automatic Git Pack Manager builds follow pushed source commits, independently of numbered GitHub Releases. Base version remains 0.1.57; CI adds the exact source revision. HTTP download and all 2,449 assets of the initial deployed build were verified; later petal/nature changes require visual checks. Other projects are not covered by this deployment audit.
- **Cosmetics:** the later 0.1.48/rb47 test files are evidence of builds, **not** evidence that the most recent combined patch was successfully installed or fixed the blood/Paper Doll issue. The older 0.1.41 source and 0.1.38 JAR records have been superseded as the tracker headline.
- **Source boundaries:** `ARTSTYLE.md` supplies visual direction and its illustrated catalogue; `AGENTS.md`, `CLAUDE.md` and feature notes govern safe pack work. The tracker is an inventory, not a substitute for those sources.
- **Next verification:** compare repository status, actual built filenames, installed mods and the live release against these rows. Move statuses only after evidence; preserve unknown versions rather than inferring them from filenames or discussion.
