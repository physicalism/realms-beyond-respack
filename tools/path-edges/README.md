# Connected path edges: generator + checker

`gen.py` writes every lawn/path edge model and both Fusion modifier files from one shape function
(dual-grid corner tiles: each grass/path block = 4 corner tiles picked by its 3 neighbours at that corner).
Shape = smooth base (CUT, RHO_P, RHO_G, STEP_RHO) + organic noise (NOISE section of gen.py):
- every block corner has a 16x16 "window" shared by the 4 blocks around it; its lawn/path boundary gets soft
  random bites/bulges (SHARED_BUMPS/SHARED_AMP), seeded by the window's shape; the window's outer rows (half-way
  along each block edge) stay at the base so windows always meet;
- each lawn block reshapes its own quarter again (OWN_BUMPS/OWN_AMP) seeded by what grows on it
  (nothing / short plants / tall plants / flowers, fences, torches), and moves its half-way seam (MID_PIN);
- cleanup removes thin tongues, stray pixels, pinches and free-floating islands; corner windows also get a
  pixel-art rounding pass (shaves sharp corners); MAX_SHIFT caps how far the edge moves;
- grass tufts (`path_tuft_*`): small separate lawn tufts on path blocks next to lawn blocks with plants on them;
  shape/position/whether one appears are random per (neighbour layout, plant class); TUFT_CHANCE, TUFT_SHAPES.
Change NOISE_SEED for a completely different random set. Fusion has no per-position random predicate for block
model modifiers, so variety comes from neighbours, plants and side. wob_patterns.json is legacy (USE_PATTERNS=False).

Regenerate into a copy of the pack, then check it:

    python3 assemble.py <pack-copy-src> <out>      # copies src -> out, replaces path_edge_test models + modifiers
    python3 run_audit.py <out> audit_out             # see-through holes / z-fighting from 25 views, 16 scenes
    python3 pixcheck.py <out>                        # stray pixels, 1px tongues
    python3 lipcheck.py <out>                        # every lawn/path step has its 1px wall
    python3 fincheck.py <out>                        # no 1px walls standing on their own ("fins")
    python3 fuzz.py <out> 60 1                       # random layouts (with plants): consistency, watertight, lips, pixels

Needs Python 3 with numpy, Pillow, scipy (only for the checker).

## Farmland (2026-11-11)
Farmland counts as `P` for the shape (it is 15px tall like a path), so lawn edges, lips and rounded corners are
identical. The lowered floor of lawn blocks is no longer baked into the `lawn_*` tiles: separate `floor_<corner>_NN`
models pave each lawn quadrant like its nearest low neighbour (dirt path / dry farmland / moist farmland, moisture 7).
`farmland_edge.json` gives farmland blocks the same raised-lawn corners (`path_corner_*`) as paths.
assemble.py can now be re-run on an installed pack.
Farmland <-> path seam: flat paving overlays at y=15.02 (`seam_farm_*` path paving on farmland blocks,
`seam_path_*_{dry,moist}` farmland paving on path blocks), from the same shape with farmland standing in for lawn
(see "farmland <-> path seam" in gen.py; `gen.seam_kind` is the ground truth, checked by fuzz.py).

## Dirt variants (2026-11-12)
Dirt, coarse dirt, rooted dirt and podzol (not snowy) count as lawn (`G`) exactly like grass: same shape, lips,
floors and backing walls. `<kind>_path_edge.json` re-uses the grass appends with re-textured copies of the lawn
tiles (`lawn_*_<kind>`: the block's own top/side textures, no tint, no side overlay). The raised rim on path and
farmland blocks is split by owner (`path_corner_<q>_<i>_<a|b|d>_<kind>`): each texel takes the texture of the
nearest lawn neighbour at that corner; rims with no lawn neighbour keep `corner_grass`. The old earth speckles on
paths next to dirt were retired (assemble.py drops them; the model files remain). Scenes `dirt_*`; fuzz mixes kinds.

## Speed (2026-11-12)
assemble.py runs optimize.py on every modifier: condition trees are flattened and reordered (and: most-likely-to-fail
first; or: most-likely-true first), measured on sample surroundings that are mostly plain fields. Floors get a cheap
one-lookup gate. Model JSON is minified. Meaning is unchanged (checked: same models on every block, 400 random layouts).
Fusion's match_block walks its block list linearly (Spark: HashMap$KeyIterator under MatchBlockBlockStatePredicate),
so optimize.py weights each check by list length and splits common blocks (air, grass, dirt, ...) out of long lists
into one-block checks tried first. What remains is about one 2-block "path or farmland?" check per append.
Correction (from Fusion's source, MatchBlock/MatchStateBlockStatePredicate): block lists are hashed sets (O(1)); the
cost is the offsets HashSet iterated on every test. So optimize.py merges same-block checks into one multi-offset
check, and gate_lists() turns each corner's mutually exclusive lawn tiles / floors into one first-match list headed by
`empty` (shown when no path/farmland is among the 8 neighbours). Plain field block: about 2600 -> about 200 units.
