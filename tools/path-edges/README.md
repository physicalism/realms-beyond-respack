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
