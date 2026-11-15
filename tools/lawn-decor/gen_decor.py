"""Natural variation via vanilla weighted random blockstate variants (truly random per position, no mod needed).

- Grass: chunky little boulders/pebble clusters (stone, andesite, cobblestone) on ~7% of plain grass blocks.
- (paths: removed at Henry's request) Dirt path: worn patches (coarse dirt / gravel / packed mud) and a few small pebbles on ~30% of path blocks,
  kept to the middle of the block (texels 4..11) so they never meet the Fusion lawn-edge pieces.
Grass next to paths uses the Fusion path models instead, so no boulders on path edges.
Re-run: python3 tools/lawn-decor/gen_decor.py
"""
import json, os, random, copy
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRASS_CHANCE, GRASS_VARIANTS = 0.035, 10
BIG_VARIANTS = 2   # extra, bigger single stones (same rarity per variant as the others)
PATH_CHANCE, PATH_VARIANTS = 0.30, 14
rng = random.Random('realms-beyond-decor-v2')

GRASS = {"parent": "minecraft:block/block",
    "textures": {"particle": "minecraft:block/dirt", "bottom": "minecraft:block/dirt", "top": "minecraft:block/grass_block_top",
                 "side": "minecraft:block/grass_block_side", "overlay": "minecraft:block/grass_block_side_overlay"},
    "elements": [
        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": {
            "down": {"uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down"},
            "up": {"uv": [0, 0, 16, 16], "texture": "#top", "cullface": "up", "tintindex": 0},
            **{d: {"uv": [0, 0, 16, 16], "texture": "#side", "cullface": d} for d in ("north", "south", "west", "east")}}},
        {"from": [0, 0, 0], "to": [16, 16, 16], "faces": {
            d: {"uv": [0, 0, 16, 16], "texture": "#overlay", "tintindex": 0, "cullface": d} for d in ("north", "south", "west", "east")}}]}
PATH = {"parent": "minecraft:block/block",
    "textures": {"particle": "minecraft:block/dirt", "bottom": "minecraft:block/dirt", "top": "minecraft:block/dirt_path_top",
                 "side": "minecraft:block/dirt_path_side"},
    "elements": [{"from": [0, 0, 0], "to": [16, 15, 16], "faces": {
        "down": {"uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down"},
        "up": {"uv": [0, 0, 16, 16], "texture": "#top"},
        **{d: {"uv": [0, 1, 16, 16], "texture": "#side", "cullface": d} for d in ("north", "south", "west", "east")}}}]}

def box(x, y, z, w, h, d, tex, u, v):
    """Box with 1:1 pixel UVs sampled from a random spot of the texture (keeps vanilla pixel scale)."""
    f = {"up": {"uv": [u, v, u + w, v + d], "texture": tex}}
    for s in ("north", "south"): f[s] = {"uv": [u, v + 2, u + w, v + 2 + h], "texture": tex}
    for s in ("west", "east"): f[s] = {"uv": [u + 1, v + 2, u + 1 + d, v + 2 + h], "texture": tex}
    return {"from": [x, y, z], "to": [x + w, y + h, z + d], "faces": f}

def free(occ, cells):
    return not any((x + dx, z + dz) in occ for (x, z) in cells for dx in (-1, 0, 1) for dz in (-1, 0, 1))

def stone(els, occ, tex, size, lo, hi, base_y):
    """A rounded little rock: a base slab plus a smaller offset cap (bigger sizes), placed within [lo, hi)."""
    shapes = {
        'pebble': [((2, 1, 1), None), ((1, 1, 2), None), ((2, 1, 2), None)],
        'small':  [((2, 1, 2), None), ((3, 1, 2), None), ((2, 1, 3), None)],
        'medium': [((3, 1, 3), None), ((4, 1, 2), None), ((2, 1, 4), None), ((3, 2, 2), None)],
        'large':  [((4, 2, 4), (3, 1, 2)), ((5, 2, 3), (3, 1, 2)), ((4, 3, 5), (2, 1, 3))],
        'big':    [((5, 2, 4), None), ((4, 2, 5), None), ((6, 2, 4), None), ((5, 3, 5), None)],
    }
    (w, h, d), cap = rng.choice(shapes[size])
    for _ in range(40):
        x, z = rng.randint(lo, hi - w), rng.randint(lo, hi - d)
        cells = [(xx, zz) for xx in range(x, x + w) for zz in range(z, z + d)]
        if free(occ, cells): break
    else:
        return False
    occ |= set(cells)
    u, v = rng.randint(0, 16 - max(w, d) - 2), rng.randint(0, 9 - h)
    els.append(box(x, base_y, z, w, h, d, tex, u, v))
    if cap and SIMPLE is False:
        cw, ch, cd = cap
        cx = x + rng.randint(0, w - cw); cz = z + rng.randint(0, d - cd)
        els.append(box(cx, base_y + h, cz, cw, ch, cd, tex, (u + 3) % (16 - cw), v))
    if not SIMPLE and size in ('medium', 'large') and rng.random() < 0.6:     # a chipped-off pebble beside it
        stone(els, occ, tex, 'pebble', lo, hi, base_y)
    return True

SIMPLE = True   # single-box stones (no caps / chips)
STONES = ["minecraft:block/stone", "minecraft:block/andesite", "minecraft:block/cobblestone", "minecraft:block/stone", "minecraft:block/andesite"]

def grass_variant():
    m = copy.deepcopy(GRASS); occ = set(); key = 'rock'
    m["textures"][key] = rng.choice(STONES)
    plan = rng.choice([['small'], ['small'], ['medium'], ['small', 'pebble']])
    for size in plan:
        stone(m["elements"], occ, '#' + key, size, 2, 14, 16)
    return m

PATCH_TEX = ["minecraft:block/coarse_dirt", "minecraft:block/coarse_dirt", "minecraft:block/gravel", "minecraft:block/packed_mud", "minecraft:block/rooted_dirt"]

def blob(lo, hi):
    """Irregular patch as a union of 2-3 overlapping rectangles."""
    cells = set()
    cx, cz = rng.randint(lo + 2, hi - 3), rng.randint(lo + 2, hi - 3)
    for _ in range(rng.randint(2, 3)):
        w, d = rng.randint(2, 4), rng.randint(2, 3)
        if rng.random() < 0.5: w, d = d, w
        x0 = min(max(lo, cx - rng.randint(0, w - 1)), hi - w); z0 = min(max(lo, cz - rng.randint(0, d - 1)), hi - d)
        cells |= {(x, z) for x in range(x0, x0 + w) for z in range(z0, z0 + d)}
    return cells

def path_variant():
    m = copy.deepcopy(PATH); occ = set()
    kind = rng.choice(['patch', 'patch', 'pebbles', 'patch+pebbles'])
    if 'patch' in kind:
        m["textures"]["patch"] = rng.choice(PATCH_TEX)
        cells = blob(4, 12)
        rows = {}
        for (x, z) in sorted(cells): rows.setdefault(z, []).append(x)
        for z, xs in rows.items():
            xs.sort(); a = xs[0]; prev = a
            for x in xs[1:] + [None]:
                if x is not None and x == prev + 1: prev = x; continue
                m["elements"].append({"from": [a, 15.03, z], "to": [prev + 1, 15.03, z + 1],
                                      "faces": {"up": {"uv": [a, z, prev + 1, z + 1], "texture": "#patch"}}})
                if x is not None: a = prev = x
        occ |= cells
    if 'pebbles' in kind:
        m["textures"]["peb"] = rng.choice(STONES)
        for _ in range(rng.randint(1, 2)):
            stone(m["elements"], occ, '#peb', 'pebble', 4, 12, 15)
    return m

def write(block, models, plain_model, plain_rot, chance, subdir):
    mdir = f"{ROOT}/assets/realm/models/block/{subdir}"; os.makedirs(mdir, exist_ok=True)
    plain_w = max(1, round(len(models) * (1 - chance) / chance / len(plain_rot)))   # each decor variant has weight 1
    variants = [dict({"model": plain_model, "weight": plain_w}, **({"y": y} if y else {})) for y in plain_rot]
    for i, m in enumerate(models):
        json.dump(m, open(f"{mdir}/{subdir.split('/')[-1]}_{i:02d}.json", "w"), indent=1)
        v = {"model": f"realm:block/{subdir}/{subdir.split('/')[-1]}_{i:02d}", "weight": 1}
        y = rng.choice([0, 90, 180, 270])
        if y: v["y"] = y
        variants.append(v)
    return variants

def big_variant():
    m = copy.deepcopy(GRASS); occ = set()
    m["textures"]['rock'] = rng.choice(STONES)
    stone(m["elements"], occ, '#rock', 'big', 3, 13, 16)
    return m

g = write('grass_block', [grass_variant() for _ in range(GRASS_VARIANTS)] + [big_variant() for _ in range(BIG_VARIANTS)], "minecraft:block/grass_block", (0, 90, 180, 270), GRASS_CHANCE, "lawn_decor/rock")
bs = f"{ROOT}/assets/minecraft/blockstates"; os.makedirs(bs, exist_ok=True)
json.dump({"variants": {"snowy=false": g, "snowy=true": {"model": "minecraft:block/grass_block_snow"}}}, open(f"{bs}/grass_block.json", "w"), indent=1)
for name, vs in (('grass', g),):
    tot = sum(v['weight'] for v in vs); print(name, 'decor share', round(sum(v['weight'] for v in vs[4:]) / tot, 3), 'variants', len(vs) - 4)
