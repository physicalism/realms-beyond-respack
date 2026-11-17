# 3D wooden ladder

Added 17 November 2026. The hand-authored `assets/minecraft/models/block/ladder.json` replaces the flat vanilla placed ladder with two full-height rails and four inset rungs. It reuses `minecraft:block/ladder`, including opaque UV strips for the exposed edges; no texture is copied or recoloured.

The model retains the vanilla silhouette and rung spacing. Rails occupy z=14.5..16 and rungs z=15..16, inside the vanilla three-pixel-deep ladder shape. Rung ends meet the rails without overlapping visible faces. Vanilla blockstates rotate the north-facing model for all four wall directions; vertically stacked rails meet at block boundaries. Climbing, collision, waterlogging and the inventory icon retain vanilla behaviour. No mod is required.

There was no previous pack ladder override to back up. Validate with `python3 tools/build.py --check`. Source geometry and UVs have been checked against the local Minecraft 26.3 client assets. In-game appearance, stacked joins and shader lighting still need visual verification with F3+T.

Revision on 17 November 2026: halved the depth towards the supporting wall (rails 3 → 1.5 model pixels, rungs 2 → 1), retaining the front silhouette, UVs and stacking alignment. Saved the previous model under `builds/ladder-backups/`. In-game appearance still needs checking in the installed pack.
