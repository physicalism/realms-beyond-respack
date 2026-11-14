# Sand shells

Added 14 November 2026. Run `python3 tools/sand-shells/generate.py` from the pack root. Generates only sand blockstates, eight shell models, and a 16 × 16 palette texture; grass assets are untouched.

Eight equally weighted variants versus plain sand weight 224: 8/232 = 3.448% (1 in 29). Cream and pale pink scallop fans use five stepped ribs, at most 1.5 model pixels high, contained within each block. Vanilla sand texture, particles, collision, and drops are preserved. No Fusion dependency.

Ordinary resource-pack variants cannot restrict this to beaches or detect air above: deserts, submerged sand, and covered sand can select shells too. Red sand is unchanged. Placement is stable per position. Visual appearance still needs in-game approval, including shader lighting and covered blocks. Before changing generated outputs, save a dated snapshot under `builds/sand-shells-backups/`.
