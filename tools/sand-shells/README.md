# Sand decoration

Run `python3 tools/sand-shells/generate.py` from the pack root. Generates only sand blockstates, sixteen decoration models, and a 16 × 16 painted shell atlas; grass assets are untouched. Read `../../ARTSTYLE.md` before changing artwork.

## Current revision — 14 November 2026

Twelve shell variants: cupped clam with a shallow rear lip, closed clam with a stepped convex back, fan-shaped scallop, and tapered spiral shell, each in ivory, coral pink, and warm orange. Maximum two model pixels high. Painted texture clusters, edges, and colour bands follow the supplied shallow pixel-textured shell reference. No identical central ridge across every shape.

Six pebble variants preserve the existing broad low single-stone and offset multi-stone shapes. Three use stone, andesite, and cobblestone; three use pale sandstone top, slightly darker sandstone bottom, and sandstone side textures. They share the existing pebble probability rather than doubling clutter. Five-arm starfish geometry, texture tile, and probability are preserved.

Weights total 4000: plain sand 3956; twelve shells at 2 each; six pebble variants at 3 each; starfish at 2. Shells: 0.6% (about 1 in 167), half the previous frequency. Pebble patches: unchanged at 0.45% (about 1 in 222). Starfish: unchanged at 0.05% (1 in 2000). Combined decoration: 1.1%. Probabilities are expectations, not guaranteed spacing.

## Feedback retained

The first pass was too common. The second pass reduced frequency but was called a downgrade: only its clam shape was explicitly liked. Do not restore the generic block whelk or fragment, or interpret “simple” as removing the defining shell silhouette. Requested additions are orange shells, pebbles, and very rare starfish. Current revision is awaiting visual approval.

## Limitations

Vanilla variants cannot restrict this to beaches or detect air above: deserts, submerged sand, and covered sand can select decoration too. Red sand is unchanged. Position determines the variant. Collision, particles, and drops remain vanilla sand. No Fusion dependency. In-game and shader appearance remain unverified. Before replacing outputs, save a dated snapshot under `builds/sand-shells-backups/`.

## Latest screenshot feedback — 14 November 2026

Starfish shape explicitly liked: preserve its geometry and palette; weight raised from 1 to 2 out of 4000 (now 1 in 2000). Earlier approval of the small clam was superseded: the in-game raised centre looks like a tiny chair and the small shells are disliked. Replace with broad 5 × 5 or 6 × 4 shallow shell halves, one model pixel high, with stepped corners and deliberately painted surface clusters. User supplied shallow textured shell, nautilus sprite, and low beach-pebble references; these establish pixel material detail and low silhouettes, not a request to copy every subject.

Pebbles enlarged to 4 × 3 and 5 × 4 pixels. The multi-stone variant uses an offset 4 × 3 and 3 × 2 composition, replacing the matching pair; multiple stones on one block are allowed. Uses vanilla stone / andesite / cobblestone at native texel scale. Current revision still needs in-game judgement.

Updated weights: plain sand 3932, twelve shells × 4, three pebble patches × 6, starfish 2; total 4000. Shell frequency remains 1.2%, pebble patches 0.45%, starfish 0.05%. Overall decoration 1.7%.

Latest request supersedes the flat-only direction: more detailed 3D shells are allowed, following the supplied textured shell reference. The current four shape families still need in-game judgement.

Sandstone colour correction: removed red sandstone at Henry’s request; all sandy pebbles now use ordinary pale sandstone textures. Shapes and frequencies unchanged.

Latest colour direction supersedes the sandstone texture choices: all three sandy pebble variants use generated `realm:block/sand_pebble_ivory`, a warm chalky ivory palette lighter than vanilla sand, with broad quiet pixel clusters for a sand-pebble / shell appearance. Geometry, ordinary grey stones, shells, starfish, and weights are unchanged. Shader appearance needs in-game review.
