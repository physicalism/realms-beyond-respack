# This Rocks! decoration catalogue

## 15 November 2026

95 placeable models adapted from This Rocks! 1.10.0 (Motschen / TeamMidnightDust): 44 rocks, 39 branches, one pinecone, three shells, three starfish, and five static geyser appearances. Source assets and checksum are retained here; attribution and the MIT licence are in `../../THIRD_PARTY_LICENSES/This-Rocks-MIT.txt` and included by the pack builder.

All variants are available through `minecraft:item_model` on paper, for manual placement using item displays. See COMMANDS.txt for individual give and summon commands, and the tagged preview cleanup command. No new blocks, collision, drops, sounds, eruption effects, or mod dependency. Geyser models are visual props only, including the on-state appearance. They do not erupt.

Automatic decoration: grass retains about 2.52% rocks, with huge variants about 0.12%, plus about 0.50% oak/birch/spruce branches and pinecones. Existing Fusion path-edge overrides are retained. Other branch colours and rock materials are available for manual placement, rather than being scattered indiscriminately. Sand shares its existing 0.6% shell and 0.05% starfish rates between old and new designs; 0.45% pebbles is unchanged. No new random geysers.

Vanilla weighted blockstates cannot select branches by biome or check for air above. Covered grass and sand can select decoration. This is cosmetic and does not modify world saves. The actual in-game result and shader appearance need user review.

## Generation

`python3 tools/this-rocks/generate.py` regenerates from the checked-in source assets. For an intentional source refresh, add `--jar /absolute/path/to/rocks-fabric-1.10.0+26.3.jar`. Run this generator AFTER regenerating lawn-decor or sand-shells, since those base generators restore their original variant lists. Keep a snapshot of current blockstates before regenerating.

Models are flattened into the realm namespace, with vanilla textures or four included mod textures. Bounds are normalised to a single-block footprint. Illegal Java starfish element angles (17.5 / 35 degrees) are snapped to the closest legal angle (22.5 / 45 degrees), so those silhouettes are adapted rather than exact copies. All other supported element rotations and UVs are retained.

## Preview

`builds/this-rocks-previews/` contains an overview and complete rock, branch, and coast/vent sheets. These are texture-mapped model renders, not Minecraft screenshots. `preview.swift` renders them without external libraries. Its render-input.json and texture-cache are prepared from the adapted models and local Minecraft client resources. No visual approval is implied by a passing resource check.

Validated with `python3 tools/build.py --check`. On 15 November 2026, the lawn-decor → sand-shells → this-rocks generation sequence was run in a temporary copy and reproduced current assets byte-for-byte. The catalogue is recorded as source work after base version 0.1.57; see the changelog and Git history for exact revisions. In-game visual approval is still pending.
