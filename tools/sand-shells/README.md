# Sand shells

Added 14 November 2026. Run `python3 tools/sand-shells/generate.py` from the pack root. Generates only sand blockstates, sixteen shell models, and a 16 × 16 palette texture; grass assets are untouched.

Sixteen equally weighted variants versus plain sand weight 1264: 16/1280 = 1.25% (1 in 80), reduced from 1 in 29 after feedback. Four shapes (scallop, clam, tapered whelk, and fragment) each use two or three broad integer-pixel cuboids, in cream, pale pink, warm grey, and muted mauve. At most two model pixels high. Vanilla sand texture, particles, collision, and drops are preserved. No Fusion dependency.

Ordinary resource-pack variants cannot restrict this to beaches or detect air above: deserts, submerged sand, and covered sand can select shells too. Red sand is unchanged. Placement is stable per position. Visual appearance still needs in-game approval, including shader lighting and covered blocks. Before changing generated outputs, save a dated snapshot under `builds/sand-shells-backups/`.
