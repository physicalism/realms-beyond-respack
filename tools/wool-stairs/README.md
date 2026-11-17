# Raised wool stairs

Implemented 17 November 2026. All 16 vanilla wool stair colours reuse their existing wool textures with treads raised by one model pixel (lower tread y=9, upper tread y=17). The unchanged footprint and base preserve adjoining runner widths. The raised edge is visible beside ordinary stairs. This is a raised wool silhouette, rather than a separate carpet item or stone-backed stair.

Straight, inner, and outer models use shared parents in `assets/realm/models/block/carpeted_wool_stairs*.json`; 48 colour overrides live in `assets/minecraft/models/block/`. Vanilla blockstates retain rotations, upside-down placement, and waterlogging. Upside-down stairs mirror the raised detail to the underside. Collision remains vanilla. Internal partition faces are omitted; raised faces intentionally have no neighbour culling to avoid disappearing beside full blocks.

Regenerate with `python3 tools/wool-stairs/generate.py`, then validate with `python3 tools/build.py --check`. These are new overrides, so there were no existing pack models to back up. Textures, ordinary stairs, slabs, and wool blocks are untouched. In-game visual approval remains pending, including corners, inverted placement, and shader lighting.
