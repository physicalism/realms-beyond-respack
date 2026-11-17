# Raised wool stairs and connected carpet edges

Updated 17 November 2026. All 16 wool stair colours keep their existing wool textures. The lower tread sits at y=9 and the upper at y=17. A one-pixel front extension and expanded inner riser give the runner a continuous wrapped profile. The mesh is the exposed surface of one joined volume, with no stacked coplanar layers or internal partition faces. Straight, inner, and outer corners retain vanilla blockstate rotations, inverted placement, and waterlogging. Collision remains vanilla.

## Fixed texture variety

Wool blocks, carpets, and wool stairs have four equally weighted model alternatives, selected by vanilla's position-seeded model randomisation. The pattern stays fixed when walking or reloading. Cubes and carpets use rotated wool UVs; stair faces use mirrored UVs and square-face rotations. Cropped rectangular stair faces are not rotated through 90 degrees, which would stretch their texels. All use the existing `minecraft:block/<colour>_wool` texture, so higher-priority texture replacements still apply. This changes texture orientation, not colour or animation, and works without Fusion.

The Fluffy Carpets v1.1 ZIP was identified but could not be downloaded in this session because file transfer failed with DNS errors, including after the user re-uploaded it. Its implementation and licence were not inspected. No models or textures from that pack have been copied; these variations are an original model-based treatment and are not claimed to reproduce its fluff.

## Fusion spill

The installed Fusion 1.3.16a supports the `match_state` predicates and appended models used here (checked against its installed class metadata/bytecode and the pack's existing modifiers). A narrow one-pixel strip extends sideways from wool onto an adjacent non-wool vanilla stair only when both are dry, bottom-half stairs with the same facing and shape. This covers all four facings and all five shapes; at corners, only portions with matching underlying tread heights receive a strip. It does not spread further or bridge air. Opposing runners can each cover one pixel of a middle stair, leaving fourteen pixels between the strips.

The strip belongs to the wool block and disappears when that wool is removed. All faces buried against either the supporting stair or the wool are omitted, including bottom faces against stone treads and faces against its vertical riser. This avoids placing a carpet face directly on an existing stone face. Strip models are baked in world orientation and their conditions use `apply_model_rotation: false`.

Waterlogged stairs, inverted stairs, differently facing/ shaped neighbours, and adjacent wool stairs do not get spill strips. Inverted wool stairs still mirror the base raised profile to their underside. Without Fusion, the raised shapes and fixed variation remain; only conditional side spill is absent. Ordinary stair models and collision are untouched.

## Source and checks

- `generate.py`: one generator for stair geometry, blockstate alternatives, and Fusion modifiers. Reads vanilla 26.3 assets from the installed client JAR; override with `--client-jar PATH`.
- `generated.json`: exact generated paths for the pack validator.
- `audit.py`: resolves all model parents/texture slots against the actual client JAR, checks complete stair surface coverage, distinct texture variants, duplicate faces, spill contact planes, and valid/invalid neighbour cases.
- `assets/realm/models/block/carpeted_wool_stairs*.json`: shared raised stair geometry.
- `assets/realm/models/block/wool_variation/`: wool block and carpet UV alternatives.
- `assets/realm/models/block/wool_spill/`: conditional side-strip models.
- `assets/realm/fusion/model_modifiers/blocks/wool_spill_*.json`: per-colour conditions.
- `assets/minecraft/blockstates/*_wool*.json` and `*_carpet.json`: vanilla position-based alternatives.

Run from the pack root:

```sh
python3 tools/wool-stairs/generate.py
python3 tools/wool-stairs/audit.py
python3 tools/build.py --check
```

The original raised implementation is retained in a dated `builds/wool-stairs-backups/before-spill-*.tar.gz` snapshot, and in Git. An asset audit does not establish in-game visual approval: F3+T and check the runner, corner transitions, and shader lighting. No version bump or release is implied.
