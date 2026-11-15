# Grass rocks

Run `python3 tools/lawn-decor/gen_decor.py` from the pack root. Uses the shared `rock_shapes.py` surface mesher, also used by sand pebbles.

## 15 November 2026 — This Rocks! direction

Inspected This Rocks! 1.10.0 from the Fabric Realm profile. Its rocks use broad low bases, offset caps, and shoulders. New original silhouettes follow that direction: wider stones with asymmetric stepped profiles, retaining vanilla stone, andesite, and cobblestone materials at native texel scale. Larger grass stones reach four model pixels high. Only exposed faces are emitted and coplanar faces are merged; no overlapping cuboids or hidden faces.

Twelve variants use approximately 2.5% grass decoration probability. Snowy grass and Fusion path-edge overrides are unchanged. No new mod dependency; in-game and shader appearance still need judgement. Before edits, save a dated snapshot under `builds/lawn-decor-backups/`.

## Reduced rarity — 15 November 2026

Grass rocks reduced from about 3.49% to 2.50% (roughly 29% fewer). Each ordinary variant has weight 4; each of the two largest variants has weight 1. Largest rocks together occur on about 0.119% of eligible blocks (roughly 1 in 841), down from 0.581% (1 in 172): about 80% fewer. Shapes, materials, and sand are untouched.

## Expanded nature catalogue

`../this-rocks/generate.py` adds sparse branches and pinecones after this base generator. Run it last when regenerating. See [nature catalogue](../this-rocks/README.md) for final rates and placement.
