# Realms Beyond — Project Instructions

## Project overview

Realms Beyond is a custom Minecraft Java Edition 26.3 resource pack (pack format 97.1), developed for a personal Realm and played on a Fabric client with Complementary shaders.

- Repository: `~/Desktop/Project/resource-pack` (git, branch `main`).
- The folder is live-linked into the game, so changes can be tested with F3+T. Anything written into `assets/` is live immediately, so do not leave half-finished assets there.
- Namespaces: `assets/realm` (the pack's own assets), `assets/minecraft` (vanilla overrides), `assets/realms_beyond_cosmetics` (resources for the companion cosmetics mod, whose source is at `~/Desktop/Project/realms-beyond-cosmetics`).
- Some features are client-side and depend on mods: connected paths, farmland edges and lawn decor use Fusion model modifiers (`assets/realm/fusion/`). Players without the mod see vanilla, and collision is always vanilla.

## Repository layout

- `assets/` — the pack.
- `tools/` — `build.py`, `release.py`, `VERSION`, and one folder per generator (for example `path-edges/`, `war-banner/`, `hanging-banner/`). Each generator folder has its own README where one is needed.
- `builds/` — backups, previews and install tarballs, grouped per feature (for example `builds/path-edge-backups/`).
- `dist/` — built ZIPs (git-ignored).
- `docs/CHANGELOG.md`, `README.md` — user-facing documentation.

## Development workflow

- Inspect existing assets and conventions before modifying anything.
- Prefer reusing established models, textures and utilities.
- Keep changes narrow and avoid modifying unrelated assets.
- Preserve existing asset names, references and compatibility unless a change explicitly requires otherwise. Item IDs already placed in the world (banners, signs, figurines) must keep working.
- Generated assets are changed through their generator in `tools/`, not by hand-editing the output. Keep the generator, its README and the generated files in step.
- Before replacing a set of generated or hand-made assets, save a dated snapshot in the matching `builds/<feature>-backups/` folder.
- Validate with `python3 tools/build.py --check`.
- Build with `python3 tools/build.py` when needed.
- Do not commit, bump `tools/VERSION`, or create or publish releases unless explicitly requested.
- Do not claim in-game visual verification without actual evidence.

## Visual design

- Aim for a polished Minecraft-native appearance, consistent with Mojang and Origin Realms aesthetics. The Origin Realms server pack is the style reference; ask for it to be attached when a task needs its files.
- Respect Minecraft's pixel-grid conventions and the resolution of existing assets.
- Prefer deliberate colours, clear silhouettes and controlled shading over excessive gradients or unnecessary complexity.
- Preserve established creative decisions unless the user requests changes. Decisions and rejected approaches are recorded in the generator READMEs and the project notes; read the relevant one before reworking a feature.
- The stag is the town's mascot and stays on its banners.
- Consider how models appear at their intended in-game scale, orientation and lighting, including under shaders.
- Models must be clean from every angle: no gaps, z-fighting, stray pixels or floating planes.

## Problem solving

- Identify the likely root cause before repeatedly changing an asset.
- Avoid repeating approaches already shown to fail.
- When testing visual fixes, distinguish validated code or asset changes from unverified in-game appearance. A passing simulator or preview render is not an in-game check.
- Ask for a screenshot when actual in-game behaviour cannot be established from available files or tests.

## Completion

Provide a brief account of:

- Files changed and why.
- Validation or build results.
- Anything that still needs in-game testing.
- Whether the work is committed and whether the version was bumped.

Do not report success if validation failed.
