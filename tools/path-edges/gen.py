"""Generator for Realms Beyond connected 3D paths (dual-grid corner tiles).

One global shape function decides, per texel, whether the surface is lawn (y=16) or path (y=15).
Every texel near a lattice corner Q depends only on the 4 cells around Q, so each block is built
from 4 corner tiles (one per corner) chosen by Fusion conditions on 3 neighbours. Neighbouring blocks
evaluate the same function, so seams always agree.

Cell types seen by the shape function:
  P  dirt path or farmland (same level; both are 15px tall, so they share one shape and only the paving differs)
  G  grass block with air/plants/fence/torch above (participates)
  S  wooden stair/slab step at the same level, or open air with a wooden stair/slab just below
  N  anything else (air, stone, non-participating grass, ...)
"""
import json, math, os, shutil, sys, itertools
import numpy as np

# ---------------------------------------------------------------- shape parameters
CUT = 2            # base depth (texels) that the path eats into the lawn
# Irregular edge patterns (texel offset added to CUT along a straight lawn edge; -1 = lawn bulge, +1/+2 = notch).
# One pattern per (what grows on the lawn block, which side the path is on), so edges vary block to block
# wherever plants are scattered and the two sides of a path never mirror each other. Ends are 0 so neighbouring
# lawn blocks always meet at the same depth.
PATTERNS = json.load(open(os.path.join(os.path.dirname(__file__), 'wob_patterns.json')))
RHO_P = 7          # radius rounding the outer corners of path blocks (dead ends, turns, single blocks)
RHO_G = 4          # radius rounding lawn corners that poke into junctions/turns
STEP_RHO = 4       # radius rounding lawn corners where the path meets a wooden step
assert all(p[0] == p[1] == p[7] == p[8] == p[14] == p[15] == 0 for p in PATTERNS) and len(PATTERNS) >= 16
assert CUT + max(max(p) for p in PATTERNS) <= 4 and CUT + RHO_G <= 7 and RHO_P <= 7
EDGE_DIRS = 'NESW'

LISTS = json.load(open(os.path.join(os.path.dirname(__file__), 'lists.json')))
AIRISH = LISTS['59']          # air, plants, fences, gates, torches (what may sit on a participating lawn block)
WOOD = LISTS['26']            # wooden stairs + slabs
AIR3 = LISTS['3']
_A = AIRISH
CLASSES = [
    [b for b in _A if b.split(':')[1] in ('air', 'cave_air', 'void_air')],
    [b for b in _A if b.split(':')[1] in ('short_grass', 'fern', 'short_dry_grass', 'leaf_litter', 'pink_petals', 'wildflowers')],
    [b for b in _A if b.split(':')[1] in ('tall_grass', 'large_fern', 'tall_dry_grass', 'bush', 'firefly_bush')],
]
CLASSES.append([b for b in _A if not any(b in c for c in CLASSES)])   # flowers, fences, gates, torches
assert sum(len(c) for c in CLASSES) == len(AIRISH)
OPEN_SIDE = sorted(set(AIRISH) | {'minecraft:farmland'})  # (legacy)
# Backing walls (1px lawn-coloured wall where a lowered lawn edge meets a neighbour) are only needed when the
# neighbour is a full opaque cube (its side face is culled against the lawn block, leaving a slit). Next to
# anything else (slabs, stairs, crops, fences, plants, air) the wall would stand on its own as a "fin".
_WOODS = ['acacia', 'bamboo', 'birch', 'cherry', 'crimson', 'dark_oak', 'jungle', 'mangrove', 'oak', 'pale_oak', 'spruce', 'warped']
FULL_NEIGHBOURS = sorted(set(
    [b for b in LISTS['147'] if b.endswith(('_log', '_wood', '_stem', '_hyphae')) and b != 'minecraft:big_dripleaf_stem'] +
    [f'minecraft:{w}_planks' for w in _WOODS] + ['minecraft:grass_block'] +
    ['minecraft:' + b for b in (
        'dirt coarse_dirt rooted_dirt podzol mycelium mud packed_mud mud_bricks moss_block clay gravel sand red_sand '
        'stone cobblestone mossy_cobblestone smooth_stone stone_bricks mossy_stone_bricks cracked_stone_bricks '
        'chiseled_stone_bricks andesite polished_andesite diorite polished_diorite granite polished_granite tuff '
        'deepslate cobbled_deepslate polished_deepslate deepslate_bricks deepslate_tiles calcite dripstone_block '
        'bricks sandstone smooth_sandstone cut_sandstone red_sandstone smooth_red_sandstone cut_red_sandstone '
        'terracotta hay_block snow_block bookshelf crafting_table barrel note_block bone_block'
    ).split()]))

# ---------------------------------------------------------------- global shape function
def cell_of(t):
    return (math.floor(t[0] / 16), math.floor(t[1] / 16))

def corner_rounded(cells, c, q):
    """Is path cell c rounded at its corner q? q = (qx,qz) in {0,1}^2 (0 = low side)."""
    cx, cz = c
    sx = -1 if q[0] == 0 else 1; sz = -1 if q[1] == 0 else 1
    a = cells.get((cx + sx, cz), 'N'); b = cells.get((cx, cz + sz), 'N'); d = cells.get((cx + sx, cz + sz), 'N')
    return a == 'G' and b == 'G' and d != 'P'

def dist_to_path(cells, px, pz):
    """Distance from point (texel units, absolute) to the rounded path region P'. Also returns the
    offset vector to the nearest feature (for wobble direction)."""
    best = (1e9, 0, 0, False)
    ccx, ccz = math.floor(px / 16), math.floor(pz / 16)
    for cx in range(ccx - 1, ccx + 2):
        for cz in range(ccz - 1, ccz + 2):
            if cells.get((cx, cz)) != 'P': continue
            x0, z0 = cx * 16, cz * 16
            qx = min(max(px, x0), x0 + 16); qz = min(max(pz, z0), z0 + 16)
            d = math.hypot(px - qx, pz - qz); vx, vz = px - qx, pz - qz
            straight = (vx == 0) != (vz == 0)
            # rounded corners
            for cq in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                if not corner_rounded(cells, (cx, cz), cq): continue
                kx = x0 + (RHO_P if cq[0] == 0 else 16 - RHO_P)
                kz = z0 + (RHO_P if cq[1] == 0 else 16 - RHO_P)
                inzone_x = (qx <= kx) if cq[0] == 0 else (qx >= kx)
                inzone_z = (qz <= kz) if cq[1] == 0 else (qz >= kz)
                if inzone_x and inzone_z:
                    r = math.hypot(px - kx, pz - kz)
                    d = max(0.0, r - RHO_P); vx, vz = px - kx, pz - kz; straight = False
            if d < best[0] - 1e-9 or (abs(d - best[0]) <= 1e-9 and not straight): best = (d, vx, vz, straight)
    return best

USE_PATTERNS = False   # superseded by organic window noise (see NOISE section)
TAPER = 8   # each half of a pattern is dropped when its edge end is not a plain straight continuation

def wobble(cells, px, pz, vx, vz, klass):
    """Edge offset for a lawn texel whose nearest path feature is a straight edge. (vx,vz) = texel - nearest point."""
    cx, cz = math.floor(px / 16), math.floor(pz / 16)
    ix = int(math.floor(px)) % 16; iz = int(math.floor(pz)) % 16
    if abs(vz) > abs(vx):
        d = 'N' if vz > 0 else 'S'; k = ix
        pdx, pdz = (0, -1) if d == 'N' else (0, 1); along = (1, 0)
    else:
        d = 'W' if vx > 0 else 'E'; k = iz
        pdx, pdz = (-1, 0) if d == 'W' else (1, 0); along = (0, 1)
    if cells.get((cx + pdx, cz + pdz)) != 'P':
        return 0
    for sgn, near in ((-1, k < TAPER), (1, k > 15 - TAPER)):
        if not near: continue
        g2 = cells.get((cx + sgn * along[0], cz + sgn * along[1]), 'N')
        p2 = cells.get((cx + pdx + sgn * along[0], cz + pdz + sgn * along[1]), 'N')
        if not (g2 == 'G' and p2 == 'P'):
            return 0
    return PATTERNS[klass * 4 + EDGE_DIRS.index(d)][k]

def height(cells, tx, tz, klass=None):
    """Surface height (16 lawn / 15 path) of texel (tx,tz) (absolute texel indices). None if not G/P.
    klass: dict cell -> plant class (0..3) of lawn cells (default 0)."""
    c = cell_of((tx, tz)); T = cells.get(c)
    if T not in ('G', 'P'): return None
    px, pz = tx + .5, tz + .5
    d, vx, vz, straight = dist_to_path(cells, px, pz)
    lim = CUT + (wobble(cells, px, pz, vx, vz, (klass or {}).get(c, 0)) if (USE_PATTERNS and straight and T == 'G') else 0)
    if d < lim: return 15
    if T == 'P': return 16
    # lawn fillets at the cell's corners
    cx, cz = c
    for qx in (0, 1):
        for qz in (0, 1):
            sx = -1 if qx == 0 else 1; sz = -1 if qz == 0 else 1
            a = cells.get((cx + sx, cz), 'N'); b = cells.get((cx, cz + sz), 'N'); dg = cells.get((cx + sx, cz + sz), 'N')
            ua = (px - cx * 16) if qx == 0 else (cx * 16 + 16 - px)   # distance to edge shared with a
            ub = (pz - cz * 16) if qz == 0 else (cz * 16 + 16 - pz)
            if a == 'P' and b == 'P':                      # lawn corner poking into a junction / turn
                Ra = Rb = CUT + RHO_G; rho = RHO_G
            elif a == 'P' and b in ('S', 'N') and dg == 'S':      # path runs onto a step past this lawn corner
                Ra, Rb, rho = CUT + STEP_RHO, STEP_RHO, STEP_RHO
            elif b == 'P' and a in ('S', 'N') and dg == 'S':
                Ra, Rb, rho = STEP_RHO, CUT + STEP_RHO, STEP_RHO
            else:
                continue
            if ua < Ra and ub < Rb and (Ra - ua) ** 2 + (Rb - ub) ** 2 > rho ** 2:
                return 15
    return 16

# ---------------------------------------------------------------- organic noise
# Every texel belongs to the "window" of its nearest block corner Q (16x16 texels centred on Q, shared by the
# 4 blocks around Q). A window's shape only depends on the 4 block types around Q, so all 4 blocks compute the
# same thing. Each window gets random bites/bulges along the lawn/path boundary (seeded by its block types),
# with the window's outer rows (the lines halfway along each block edge) kept at the smooth base shape so
# neighbouring windows always meet. On top of that, each lawn block reshapes the inside of its own quarter
# (never its outer rows) with a seed that also includes what grows on it, so straight runs vary block to block.
import zlib, random as _random
from functools import lru_cache

NOISE_SEED = 'realms-beyond-paths-v2'
SHARED_BUMPS, SHARED_AMP = (1, 3), (0.8, 2.2)   # soft bites/bulges per corner window
OWN_BUMPS, OWN_AMP = (1, 2), (2.0, 4.0)         # per lawn quarter, seeded with what grows on the block
MAX_SHIFT = 4              # how far (texels) the noisy edge may move from the smooth edge
CORNER_CELLS = {(-1, -1): 0, (0, -1): 1, (-1, 0): 2, (0, 0): 3}   # TL, TR, BL, BR around Q (cell offsets)
# Depth offset of the lawn edge at the half-way point of a block edge facing a path, per plant class and side.
# Both halves of the block know their own plant class, so this seam can move without breaking anything.
MID_PIN = {(kl, side): v for kl in range(4) for side, v in zip('NESW', _random.Random(f'pins{kl}').sample([-1, 0, 1, 2, 1, -1, 0, 2], 4))}
SIDE_VEC = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'E': (1, 0)}

def mid_pin_height(cells_g, kl, x, z):
    """Height of a lawn texel (x,z) of the block at (0,0) on its half-way seam (x or z in {7,8}) near an edge
    that faces a path block, or None if the texel is not such a pin."""
    for side, (dx, dz) in SIDE_VEC.items():
        if cells_g.get((dx, dz)) != 'P': continue
        if dz:   # north/south edge: seam columns 7,8
            if x not in (7, 8): continue
            depth = z if side == 'N' else 15 - z
        else:
            if z not in (7, 8): continue
            depth = x if side == 'W' else 15 - x
        if depth > 5: continue
        return 15 if depth < CUT + MID_PIN[(kl, side)] else 16
    return None

def _shape_key(W, T):
    # identical-looking windows get identical noise (keeps the number of distinct models down)
    t = np.vectorize(lambda v: {'G': 'g', 'P': 'p'}.get(v, 'x'))(T)
    return zlib.crc32(W.astype(np.int8).tobytes() + ''.join(t.ravel()).encode())

def _rng(*key):
    return _random.Random(zlib.crc32(('|'.join(map(str, (NOISE_SEED,) + key))).encode()))

def _cells4(cfg4):
    return {c: cfg4[i] for c, i in CORNER_CELLS.items()}

@lru_cache(maxsize=None)
def base_window(cfg4):
    """Smooth heights for window texels (offsets -8..7 around Q at texel (0,0)); None outside lawn/path."""
    cells = _cells4(cfg4)
    W = np.full((16, 16), -1, int)       # [oz+8][ox+8]: 1 lawn, 0 path, -1 not lawn/path
    T = np.full((16, 16), 'N', object)   # block type owning each texel
    for oz in range(-8, 8):
        for ox in range(-8, 8):
            c = cell_of((ox, oz)); T[oz + 8, ox + 8] = cells.get(c, 'N')
            h = height(cells, ox, oz)
            if h is not None: W[oz + 8, ox + 8] = 1 if h == 16 else 0
    return W, T

def _features_ok(M, base, region):
    """No 1-texel tongues/tips/isolated texels or diagonal pinches that the base shape didn't already have,
    looking at texels in/near region."""
    H, Wd = M.shape
    def bad_at(A, z, x):
        v = A[z, x]
        if v < 0: return False
        n = []
        for dz, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            zz, xx = z + dz, x + dx
            n.append(A[zz, xx] if 0 <= zz < H and 0 <= xx < Wd else -1)
        known = [k for k in n if k >= 0]
        diff = sum(1 for k in known if k != v)
        if diff >= 3: return True
        if (n[0] >= 0 and n[1] >= 0 and n[0] != v and n[1] != v) or (n[2] >= 0 and n[3] >= 0 and n[2] != v and n[3] != v):
            return True
        return False
    def pinch_at(A, z, x):
        if z + 1 >= H or x + 1 >= Wd: return False
        q = A[z:z + 2, x:x + 2]
        if (q < 0).any(): return False
        return q[0, 0] == q[1, 1] and q[0, 1] == q[1, 0] and q[0, 0] != q[0, 1]
    near = region.copy()
    near[1:, :] |= region[:-1, :]; near[:-1, :] |= region[1:, :]; near[:, 1:] |= region[:, :-1]; near[:, :-1] |= region[:, 1:]
    for z in range(H):
        for x in range(Wd):
            if not near[z, x]: continue
            if bad_at(M, z, x) and not bad_at(base, z, x): return False
            for zz, xx in ((z, x), (z - 1, x), (z, x - 1), (z - 1, x - 1)):
                if 0 <= zz and 0 <= xx and pinch_at(M, zz, xx) and not pinch_at(base, zz, xx): return False
    # small islands fully inside the editable region
    from scipy.ndimage import label
    for v in (0, 1):
        lab, k = label(M == v)
        for i in range(1, k + 1):
            comp = lab == i
            if comp.sum() < 5 and (comp <= region).all() and not ((label(base == v)[0] > 0) & comp).all():
                return False
    return True

def _allowed(base, T, region):
    """Texels the noise may flip."""
    H, Wd = base.shape
    from scipy.ndimage import distance_transform_cdt
    valid = base >= 0
    # distance to the smooth lawn/path boundary
    edge = np.zeros_like(valid)
    for dz, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        sh = np.full_like(base, -1)
        zs = slice(max(0, dz), H + min(0, dz)); xs = slice(max(0, dx), Wd + min(0, dx))
        zd = slice(max(0, -dz), H + min(0, -dz)); xd = slice(max(0, -dx), Wd + min(0, -dx))
        sh[zd, xd] = base[zs, xs]
        edge |= valid & (sh >= 0) & (sh != base)
    if not edge.any(): return np.zeros_like(valid)
    dist = distance_transform_cdt(~edge, metric='chessboard')
    # keep a 1-texel margin from anything that isn't lawn/path (walls, drops, steps)
    wall = ~valid
    near_wall = wall.copy()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            zs = slice(max(0, dz), H + min(0, dz)); xs = slice(max(0, dx), Wd + min(0, dx))
            zd = slice(max(0, -dz), H + min(0, -dz)); xd = slice(max(0, -dx), Wd + min(0, -dx))
            near_wall[zd, xd] |= wall[zs, xs]
    # path blocks may only grow lawn within 2 texels of a lawn block
    lawn_cell = (T == 'G')
    near_lawn_cell = lawn_cell.copy()
    for _ in range(2):
        g = near_lawn_cell.copy()
        g[1:, :] |= near_lawn_cell[:-1, :]; g[:-1, :] |= near_lawn_cell[1:, :]
        g[:, 1:] |= near_lawn_cell[:, :-1]; g[:, :-1] |= near_lawn_cell[:, 1:]
        near_lawn_cell = g
    ok = valid & region & (dist <= MAX_SHIFT) & ~near_wall
    ok &= (T == 'G') | ((T == 'P') & (near_lawn_cell | (base == 1)))
    return ok

def _cleanup(M, allow):
    """Morphological open+close with a 2x2 element, only flipping allowed texels."""
    H, Wd = M.shape
    for _ in range(8):
        changed = False
        for v in (1, 0):
            keep = np.zeros_like(allow)
            for z in range(H - 1):
                for x in range(Wd - 1):
                    blk = M[z:z + 2, x:x + 2]
                    if ((blk == v) | (blk < 0)).all() and (blk == v).any():
                        keep[z:z + 2, x:x + 2] |= (blk == v)
            flip = allow & (M == v) & ~keep
            if flip.any():
                M[flip] = 1 - v; changed = True
        if not changed: break
    return M

def _sdf(M):
    """Signed distance at texel centres: >0 inside lawn, <0 inside path (texels not lawn/path count as lawn)."""
    from scipy.ndimage import distance_transform_edt
    lawn = M != 0
    path = M == 0
    if not path.any() or not lawn.any():
        return np.where(lawn, 9.0, -9.0)
    dl = distance_transform_edt(lawn)     # for lawn texels: distance to nearest path texel
    dp = distance_transform_edt(path)
    return np.where(lawn, dl - 0.5, -(dp - 0.5))

def _taper(region, ramp=1.6):
    """1 deep inside region, easing to 0 at its border (smoothstep over `ramp` texels)."""
    from scipy.ndimage import distance_transform_edt
    d = distance_transform_edt(np.pad(region, 1)).astype(float)[1:-1, 1:-1]
    t = np.clip((d - 0.5) / ramp, 0, 1)
    return t * t * (3 - 2 * t)

def _drop_islands(M, allow):
    """Remove lawn/path pieces that float free inside the editable area (accidental patches)."""
    from scipy.ndimage import label
    for v in (1, 0):
        lab, k = label(M == v)
        for i in range(1, k + 1):
            comp = lab == i
            if (comp <= allow).all():
                # touches a fixed texel of the same kind? then it is attached
                grown = comp.copy()
                grown[1:, :] |= comp[:-1, :]; grown[:-1, :] |= comp[1:, :]; grown[:, 1:] |= comp[:, :-1]; grown[:, :-1] |= comp[:, 1:]
                if not (grown & ~allow & (M == v)).any() and not (grown & ~allow & (M < 0)).any():
                    M[comp] = 1 - v
    return M

def _round_corners(M, allow, passes=2):
    """Pixel-art rounding: shave the outermost texel off sharp convex corners of lawn and of path."""
    H, Wd = M.shape
    touched = np.zeros_like(allow)
    def get(A, z, x):
        return A[z, x] if 0 <= z < H and 0 <= x < Wd else -1
    for _ in range(passes):
        for v in (1, 0):
            A = M.copy()
            for z in range(H):
                for x in range(Wd):
                    if not allow[z, x] or touched[z, x] or A[z, x] != v: continue
                    for dz, dx in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                        o1, o2, dg = get(A, z + dz, x), get(A, z, x + dx), get(A, z + dz, x + dx)
                        op1, op2 = get(A, z - dz, x), get(A, z, x - dx)
                        # sharp corner: open on two sides, solid on the two opposite sides
                        if o1 == o2 == dg == 1 - v and op1 == op2 == v:
                            M[z, x] = 1 - v; touched[z, x] = True
                            break
    return M

def _perturb(base, T, region, key, bumps, amp, taper_region=None, rounding=False):
    allow = _allowed(base, T, region)
    if not allow.any(): return base.copy()
    sd = _sdf(base)
    w = _taper(region if taper_region is None else taper_region)
    zz, xx = np.mgrid[0:16, 0:16]
    cand = [(z, x) for z in range(16) for x in range(16) if allow[z, x] and abs(sd[z, x]) < 2.6]
    if not cand: return base.copy()
    for attempt in range(60):
        rng = _rng(*key, attempt)
        n = np.zeros((16, 16))
        nb = rng.randint(*bumps)
        if nb == 0:
            return base.copy()
        for _ in range(nb):
            cz, cx = rng.choice(cand)
            cz += rng.uniform(-1, 1); cx += rng.uniform(-1, 1)
            sig = rng.uniform(1.6, 3.4)
            a = rng.choice((-1, 1)) * rng.uniform(*amp)
            n += a * np.exp(-((zz - cz) ** 2 + (xx - cx) ** 2) / (2 * sig * sig))
        n = np.clip(n * w, -MAX_SHIFT, MAX_SHIFT)
        M = base.copy()
        newv = np.where(sd + n > 0, 1, 0)
        M[allow] = newv[allow]
        M = _cleanup(M, allow)
        M = _drop_islands(M, allow)
        if rounding: M = _round_corners(M, allow)
        M = _cleanup(M, allow)
        M = _drop_islands(M, allow)
        if (M != base).sum() >= 3 and _features_ok(M, base, allow):
            return M
    return base.copy()

@lru_cache(maxsize=None)
def noisy_window(cfg4):
    base, T = base_window(cfg4)
    region = np.zeros((16, 16), bool); region[1:15, 1:15] = True     # outer rows stay smooth
    v = base[base >= 0]
    rows_uniform = all(len(set(r[r >= 0])) <= 1 for r in base)
    cols_uniform = all(len(set(c[c >= 0])) <= 1 for c in base.T)
    if (rows_uniform or cols_uniform) or len(set(v.tolist())) < 2:
        return base.copy(), T      # plain straight edge (or no edge): leave variety to the blocks themselves
    return _perturb(base, T, region, ('win', _shape_key(base, T)), SHARED_BUMPS, SHARED_AMP, rounding=False), T

@lru_cache(maxsize=None)
def own_quarter(cfg4, slot, kl):
    """Window after the lawn block in corner slot (0 TL,1 TR,2 BL,3 BR) reshapes its own quarter.
    It may not touch: the window border (the block's half-way lines), texels on its block edge next to
    another lawn block or a wall, or edge texels next to a raised-lawn texel of a path block (those
    neighbours draw the step and must know the shape)."""
    W, T = noisy_window(cfg4)
    if cfg4[slot] != 'G': return W
    W = W.copy()
    # block-relative cell types (block at (0,0)) and texel mapping
    gx, gz = [k for k, v in CORNER_CELLS.items() if v == slot][0]
    cells_g = {(cx - gx, cz - gz): cfg4[i] for (cx, cz), i in CORNER_CELLS.items()}
    for wz in range(16):
        for wx in range(16):
            ox, oz = wx - 8, wz - 8
            if (math.floor(ox / 16), math.floor(oz / 16)) != (gx, gz): continue
            x, z = ox - 16 * gx, oz - 16 * gz
            h = mid_pin_height(cells_g, kl, x, z)
            if h is not None: W[wz, wx] = 1 if h == 16 else 0
    zr = range(0, 8) if slot in (0, 1) else range(8, 16)
    xr = range(0, 8) if slot in (0, 2) else range(8, 16)
    quarter = np.zeros((16, 16), bool)
    for z in zr:
        for x in xr: quarter[z, x] = True
    region = quarter.copy()
    region[0, :] = region[15, :] = False; region[:, 0] = region[:, 15] = False     # window border
    soft = np.zeros((16, 16), bool)    # region border sides that may move freely (towards path blocks)
    for z in zr:
        for x in xr:
            if not region[z, x]: continue
            for dz, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                zz, xx = z + dz, x + dx
                if quarter[zz, xx]: continue
                if T[zz, xx] == 'P' and W[zz, xx] == 0:
                    soft[zz, xx] = True
                else:
                    region[z, x] = False
    w_region = region | soft
    return _perturb(W, T, region, ('own', slot, kl, _shape_key(W, T), region.tobytes().hex()), OWN_BUMPS, OWN_AMP, taper_region=w_region)

# ---------------------------------------------------------------- geometry helpers
def rects(mask):
    """Greedy rectangle cover of a boolean 2D mask [z][x] -> list of (x0,z0,x1,z1)."""
    m = mask.copy(); out = []
    H, W = m.shape
    for z in range(H):
        x = 0
        while x < W:
            if not m[z, x]: x += 1; continue
            x1 = x
            while x1 < W and m[z, x1]: x1 += 1
            z1 = z + 1
            while z1 < H and m[z1, x:x1].all(): z1 += 1
            m[z:z1, x:x1] = False
            out.append((x, z, x1, z1)); x = x1
    return out

def runs(vals):
    """vals: list of (pos, key) sorted by pos, contiguous -> merged [(p0,p1,key)]"""
    out = []
    for p, k in vals:
        if out and out[-1][2] == k and out[-1][1] == p: out[-1][1] = p + 1
        else: out.append([p, p + 1, k])
    return out

def side_uv(face, a, b):
    return {'north': (16 - b, 16 - a), 'south': (a, b), 'west': (a, b), 'east': (16 - b, 16 - a)}[face]

# ---------------------------------------------------------------- tile builders
QUADS = {'nw': (0, 0), 'ne': (1, 0), 'sw': (0, 1), 'se': (1, 1)}   # (qx,qz) of the corner
DIRV = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}

def neighbours_for(q):
    qx, qz = QUADS[q]
    sx = -1 if qx == 0 else 1; sz = -1 if qz == 0 else 1
    return (sx, 0), (0, sz), (sx, sz)   # a (x-side), b (z-side), d (diagonal)

def tile_heights(cells, klass=None):
    """heights for texels of cell (0,0) plus a 1-texel ring: array [18,18] indexed [z+1][x+1]"""
    H = np.zeros((18, 18), object)
    for z in range(-1, 17):
        for x in range(-1, 17):
            H[z + 1, x + 1] = height(cells, x, z, klass)
    return H

def window_H(q, cells, kl=0):
    """18x18 heights for the block at (0,0) (+1 ring) using the noisy corner window of quadrant q."""
    qx, qz = QUADS[q]
    cfg4 = tuple(cells.get((qx + dx, qz + dz), 'N') for (dx, dz) in CORNER_CELLS)
    slot = CORNER_CELLS[(-qx, -qz)]
    W = own_quarter(cfg4, slot, kl) if cells[(0, 0)] == 'G' else noisy_window(cfg4)[0]
    H = np.zeros((18, 18), object)
    for z in range(-1, 17):
        for x in range(-1, 17):
            ox, oz = x - 16 * qx, z - 16 * qz
            if -8 <= ox < 8 and -8 <= oz < 8:
                v = W[oz + 8, ox + 8]
                H[z + 1, x + 1] = None if v < 0 else (16 if v == 1 else 15)
            else:
                h = None
                if cells[(0, 0)] == 'G' and 0 <= x < 16 and 0 <= z < 16:
                    h = mid_pin_height(cells, kl, x, z)
                H[z + 1, x + 1] = h if h is not None else height(cells, x, z)
    return H

def grass_tile(q, cells, kl=0):
    """Elements for the quadrant q of a lawn block at (0,0) whose plant class is kl."""
    H = window_H(q, cells, kl)
    qx, qz = QUADS[q]
    xs = range(0, 8) if qx == 0 else range(8, 16)
    zs = range(0, 8) if qz == 0 else range(8, 16)
    els = []
    # tops
    g = np.zeros((16, 16), bool); p = np.zeros((16, 16), bool)
    for z in zs:
        for x in xs:
            if H[z + 1, x + 1] == 16: g[z, x] = True
            else: p[z, x] = True
    for (x0, z0, x1, z1) in rects(g):
        els.append({'from': [x0, 15, z0], 'to': [x1, 16, z1],
                    'faces': {'up': {'uv': [x0, z0, x1, z1], 'texture': '#top', 'tintindex': 0, 'cullface': 'up'}}})
    # (the lowered floor is drawn by the separate floor_* models, see floor_tile)
    # lips (inside cell + across the block edge): lawn texel next to a lower texel / open side
    lips = {d: [] for d in DIRV}
    for z in zs:
        for x in xs:
            if H[z + 1, x + 1] != 16: continue
            for d, (dx, dz) in DIRV.items():
                nx, nz = x + dx, z + dz
                inside = 0 <= nx < 16 and 0 <= nz < 16
                nh = H[nz + 1, nx + 1]
                if inside:
                    if nh == 15: lips[d].append((x, z))
                else:
                    if nh != 16: lips[d].append((x, z))   # path texel, unknown/open neighbour
    for d, lst in lips.items():
        # group by plane, merge along
        horiz = d in ('north', 'south')
        planes = {}
        for (x, z) in lst:
            key = z if horiz else x
            planes.setdefault(key, []).append(x if horiz else z)
        for key, ps in planes.items():
            ps.sort()
            for a, b, _ in runs([(v, 0) for v in ps]):
                if horiz:
                    zz = key if d == 'north' else key + 1
                    fr, to = [a, 15, zz], [b, 16, zz]
                else:
                    xx = key if d == 'west' else key + 1
                    fr, to = [xx, 15, a], [xx, 16, b]
                u0, u1 = (a, b)
                els.append({'from': fr, 'to': to, 'faces': {d: {'uv': [u0, 0, u1, 1], 'texture': '#side_top', 'tintindex': 0}}})
    # outer body sides (0..15) on the two block edges of this quadrant
    for d in DIRV:
        on = {'north': qz == 0, 'south': qz == 1, 'west': qx == 0, 'east': qx == 1}[d]
        if not on: continue
        if d in ('north', 'south'):
            z = 0 if d == 'north' else 15
            seq = [(x, 'G' if H[z + 1, x + 1] == 16 else 'P') for x in xs]
        else:
            x = 0 if d == 'west' else 15
            seq = [(z, 'G' if H[z + 1, x + 1] == 16 else 'P') for z in zs]
        for a, b, k in runs(seq):
            if d in ('north', 'south'):
                zz = 0 if d == 'north' else 16
                fr, to = [a, 0, zz], [b, 15, zz]
            else:
                xx = 0 if d == 'west' else 16
                fr, to = [xx, 0, a], [xx, 15, b]
            u0, u1 = side_uv(d, a, b)
            if k == 'G':
                els.append({'from': fr, 'to': to, 'faces': {d: {'uv': [u0, 1, u1, 16], 'texture': '#side', 'cullface': d}}})
                els.append({'from': fr, 'to': to, 'faces': {d: {'uv': [u0, 1, u1, 16], 'texture': '#overlay', 'tintindex': 0, 'cullface': d}}})
            else:
                els.append({'from': fr, 'to': to, 'faces': {d: {'uv': [u0, 1, u1, 16], 'texture': '#path_side', 'cullface': d}}})
    return els

def path_owners(q, cells):
    """16x16 int array for a path block's quadrant: -2 = not raised, -1 = raised with no lawn neighbour at this corner,
    j = raised and closest to neighbour slot j (0 a, 1 b, 2 diagonal) of neighbours_for(q), which is lawn ('G').
    The raised rim takes that neighbour's texture (grass / dirt variant)."""
    H = window_H(q, cells)
    qx, qz = QUADS[q]
    nb = neighbours_for(q)
    xs = range(0, 8) if qx == 0 else range(8, 16)
    zs = range(0, 8) if qz == 0 else range(8, 16)
    O = np.full((16, 16), -2)
    for z in zs:
        for x in xs:
            if H[z + 1, x + 1] != 16: continue
            best = None
            for j, (cx, cz) in enumerate(nb):
                if cells.get((cx, cz)) != 'G': continue
                px, pz = x + .5, z + .5
                nx = min(max(px, cx * 16), cx * 16 + 16); nz = min(max(pz, cz * 16), cz * 16 + 16)
                d = math.hypot(px - nx, pz - nz)
                if best is None or d < best[0] - 1e-9: best = (d, j)
            O[z, x] = -1 if best is None else best[1]
    return O

def path_tile(q, cells, sel=None):
    """Raised-lawn elements inside a path block's quadrant (only texels in `sel`, if given)."""
    H = window_H(q, cells)
    qx, qz = QUADS[q]
    xs = range(0, 8) if qx == 0 else range(8, 16)
    zs = range(0, 8) if qz == 0 else range(8, 16)
    g = np.zeros((16, 16), bool)
    for z in zs:
        for x in xs:
            if H[z + 1, x + 1] == 16 and (sel is None or sel[z, x]): g[z, x] = True
    if not g.any(): return []
    els = []
    for (x0, z0, x1, z1) in rects(g):
        els.append({'from': [x0, 15, z0], 'to': [x1, 16, z1], 'faces': {'up': {'uv': [x0, z0, x1, z1], 'texture': '#edge'}}})
    lips = []
    for z in zs:
        for x in xs:
            if not g[z, x]: continue
            for d, (dx, dz) in DIRV.items():
                nx, nz = x + dx, z + dz
                nh = H[nz + 1, nx + 1]
                if nh == 15: lips.append((d, x, z))
    for d in DIRV:
        horiz = d in ('north', 'south')
        planes = {}
        for (dd, x, z) in lips:
            if dd != d: continue
            planes.setdefault(z if horiz else x, []).append(x if horiz else z)
        for key, ps in planes.items():
            ps.sort()
            for a, b, _ in runs([(v, 0) for v in ps]):
                if horiz:
                    zz = key if d == 'north' else key + 1; fr, to = [a, 15, zz], [b, 16, zz]
                else:
                    xx = key if d == 'west' else key + 1; fr, to = [xx, 15, a], [xx, 16, b]
                els.append({'from': fr, 'to': to, 'faces': {d: {'uv': [a, 0, b, 1], 'texture': '#edge'}}})
    return els



# ---------------------------------------------------------------- grass tufts on the path
# Small separate lawn tufts on path blocks, next to lawn blocks that have plants on them. Shape, position and
# whether one appears at all are random per (neighbour layout, plant class), so they come and go with the plants.
TUFT_CHANCE = 0.0   # tufts removed at Henry's request
TUFT_SHAPES = [
    ["##", "##"], ["###", "###"], ["##", "##", "##"], [".##", "###", "##."], ["##.", "###", ".##"],
    [".##.", "####", "####", ".##."], ["####", "####"], ["##", "##", "##", "##"], [".###", "####", "###."],
    ["##..", "####", "..##"], [".##", "###", "###", "##."],
    [".####", "#####", "###.."], ["..##", ".###", "####", "##.."], [".###.", "#####", "#####", ".###."],
]

@lru_cache(maxsize=None)
def path_tuft(q, ta, tb, td, kl):
    """16x16 bool mask (block coords) of a tuft in quadrant q of a path block, or None."""
    if kl == 0 or 'G' not in (ta, tb) or any(t not in 'PG' for t in (ta, tb, td)):
        return None
    A, Bn, D = neighbours_for(q)
    H = window_H(q, {(0, 0): 'P', A: ta, Bn: tb, D: td})
    qx, qz = QUADS[q]
    inner = range(1, 7) if qx == 0 else range(9, 15)
    innz = range(1, 7) if qz == 0 else range(9, 15)
    cand = np.zeros((16, 16), bool)
    for z in innz:
        for x in inner:
            if H[z + 1, x + 1] != 15: continue
            ok = True
            cells_q = {(0, 0): 'P', A: ta, Bn: tb, D: td}
            for dz in range(-2, 3):
                for dx in range(-2, 3):
                    zz, xx = z + dz, x + dx
                    if -1 <= zz <= 16 and -1 <= xx <= 16 and H[zz + 1, xx + 1] == 16: ok = False
                    # keep clear of lawn blocks: they may move their own edge right up to the block boundary
                    if cells_q.get((math.floor(xx / 16), math.floor(zz / 16)), 'N') != 'P': ok = False
            cand[z, x] = ok
    if TUFT_CHANCE <= 0: return None
    rng = _rng('tuft', q, ta, tb, td, kl)
    if rng.random() > TUFT_CHANCE: return None
    for _ in range(40):
        shp = rng.choice(TUFT_SHAPES)
        if rng.random() < 0.5: shp = [''.join(r) for r in zip(*shp)]          # transpose
        if rng.random() < 0.5: shp = [r[::-1] for r in shp]
        h, w = len(shp), len(shp[0])
        z0 = rng.randint(0, 16 - h); x0 = rng.randint(0, 16 - w)
        m = np.zeros((16, 16), bool)
        for i, row in enumerate(shp):
            for j, ch in enumerate(row):
                if ch == '#': m[z0 + i, x0 + j] = True
        if (m <= cand).all():
            return m
    return None

def tuft_elements(m):
    els = []
    for (x0, z0, x1, z1) in rects(m):
        els.append({'from': [x0, 15, z0], 'to': [x1, 16, z1], 'faces': {'up': {'uv': [x0, z0, x1, z1], 'texture': '#edge'}}})
    for d, (dx, dz) in DIRV.items():
        horiz = d in ('north', 'south'); planes = {}
        for z in range(16):
            for x in range(16):
                if not m[z, x]: continue
                nz, nx = z + dz, x + dx
                if 0 <= nz < 16 and 0 <= nx < 16 and m[nz, nx]: continue
                planes.setdefault(z if horiz else x, []).append(x if horiz else z)
        for key, ps in planes.items():
            ps.sort()
            for a, b, _ in runs([(v, 0) for v in ps]):
                if horiz:
                    zz = key if d == 'north' else key + 1; fr, to = [a, 15, zz], [b, 16, zz]
                else:
                    xx = key if d == 'west' else key + 1; fr, to = [xx, 15, a], [xx, 16, b]
                els.append({'from': fr, 'to': to, 'faces': {d: {'uv': [a, 0, b, 1], 'texture': '#edge'}}})
    return els

# ---------------------------------------------------------------- conditions
def mb(off, blocks):
    return {'type': 'match_block', 'offset': list(off), 'blocks': blocks, 'apply_model_rotation': False}
def up(off): return (off[0], off[1] + 1, off[2])
def down(off): return (off[0], off[1] - 1, off[2])
def NOT(c): return {'type': 'not', 'predicate': c}
def AND(*cs): return {'type': 'and', 'predicates': list(cs)}
def OR(*cs): return cs[0] if len(cs) == 1 else {'type': 'or', 'predicates': list(cs)}

LOW = ['minecraft:dirt_path', 'minecraft:farmland']   # blocks whose surface is the lowered (15px) level
def isP(o): return mb(o, LOW)
def _farm(o, moist):
    return {'type': 'match_state', 'offset': list(o), 'apply_model_rotation': False, 'block': 'minecraft:farmland',
            'properties': {'moisture': ['7'] if moist else [str(i) for i in range(7)]}}
# floor kinds (what the lowered part of a lawn block is paved with): P dirt path, F dry farmland, M moist farmland, - none
FLOOR_TEX = {'P': '#path', 'F': '#farm', 'M': '#farm_moist'}
def floor_typ(o, t):
    return {'P': mb(o, ['minecraft:dirt_path']), 'F': _farm(o, False), 'M': _farm(o, True), '-': NOT(isP(o))}[t]
def floor_cond(cfgs, offs):
    U = 'PFM-'; cfgset = set(cfgs); remaining = set(cfgset); terms = []
    while remaining:
        c0 = sorted(remaining)[0]
        box = [{c0[0]}, {c0[1]}, {c0[2]}]
        for slot in range(3):
            for t in U:
                trial = [set(b) for b in box]; trial[slot].add(t)
                if all(c in cfgset for c in itertools.product(*trial)): box = trial
        for c in itertools.product(*box): remaining.discard(c)
        parts = []
        for sl in range(3):
            if len(box[sl]) == 4: continue
            if box[sl] == set('PFM'): parts.append(isP(offs[sl])); continue
            parts.append(OR(*[floor_typ(offs[sl], t) for t in sorted(box[sl], key=U.index)]))
        terms.append(AND(*parts) if len(parts) > 1 else parts[0])
    return OR(*terms)
def floor_tile(q, ka, kb, kd):
    """Lowered floor (y=15) for quadrant q of a lawn block: each texel is paved like the nearest low neighbour.
    Drawn under the whole quadrant; the raised lawn (15..16 boxes with top faces and lips) hides the rest."""
    qx, qz = QUADS[q]
    A, Bn, D = neighbours_for(q)
    xs = range(0, 8) if qx == 0 else range(8, 16)
    zs = range(0, 8) if qz == 0 else range(8, 16)
    els = []
    masks = {k: np.zeros((16, 16), bool) for k in 'PFM'}
    for z in zs:
        for x in xs:
            best = None
            for pri, ((cx, cz), k) in enumerate(((A, ka), (Bn, kb), (D, kd))):
                if k == '-': continue
                px, pz = x + .5, z + .5
                nx = min(max(px, cx * 16), cx * 16 + 16); nz = min(max(pz, cz * 16), cz * 16 + 16)
                d = math.hypot(px - nx, pz - nz)
                if best is None or d < best[0] - 1e-9: best = (d, k)
            masks[best[1]][z, x] = True
    for k in 'PFM':
        for (x0, z0, x1, z1) in rects(masks[k]):
            els.append({'from': [x0, 15, z0], 'to': [x1, 15, z1],
                        'faces': {'up': {'uv': [x0, z0, x1, z1], 'texture': FLOOR_TEX[k]}}})
    return els
# Lawn-level ground that merges with paths (Henry, 2026-11-12): grass and every dirt variant. They share one shape;
# only the textures differ (dirt variants have no grass tint and no side overlay).
LAWN_KINDS = ['grass', 'dirt', 'coarse_dirt', 'rooted_dirt', 'podzol']
DIRT_TEX = {'dirt': ('dirt', 'dirt'), 'coarse_dirt': ('coarse_dirt', 'coarse_dirt'),
            'rooted_dirt': ('rooted_dirt', 'rooted_dirt'), 'podzol': ('podzol_top', 'podzol_side')}   # (top, side)
def kind_target(k):
    if k in ('grass', 'podzol'):
        return {'block': 'minecraft:' + ('grass_block' if k == 'grass' else k), 'properties': {'snowy': ['false']}}
    return 'minecraft:' + k
def kind_cond(o, k):
    t = kind_target(k)
    if isinstance(t, str): return mb(o, [t])
    return {'type': 'match_state', 'offset': list(o), 'apply_model_rotation': False, 'block': t['block'], 'properties': t['properties']}
def isG(o): return AND(OR(kind_cond(o, 'grass'), kind_cond(o, 'podzol'),
                          mb(o, ['minecraft:dirt', 'minecraft:coarse_dirt', 'minecraft:rooted_dirt'])), mb(up(o), AIRISH))
def isS(o): return OR(mb(o, WOOD), AND(mb(o, AIR3), mb(down(o), WOOD)))
def typ(o, t, universe):
    """condition that the cell at offset o has type t, with t from universe (exclusive classification)."""
    if t == 'P': return isP(o)
    if t == 'G': return AND(NOT(isP(o)), isG(o))
    if t == 'S': return AND(NOT(isP(o)), isS(o))
    # N = none of the other members of the universe
    cs = [NOT(isP(o))]
    if 'G' in universe: cs.append(NOT(isG(o)))
    if 'S' in universe: cs.append(NOT(isS(o)))
    return AND(*cs)

SELF_OK = mb((0, 1, 0), AIRISH)
NEI8 = [(dx, 0, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dz) != (0, 0)]
ANY_P = OR(*[isP(o) for o in NEI8])

# ---------------------------------------------------------------- farmland <-> path seam (flat, texture only)
# Farmland and paths are both 15px tall, so their seam is only a change of paving. It reuses the lawn/path shape
# with farmland standing in for the lawn ('G', plant class 0) and everything that is not farmland/path as 'N':
# where that shape says "path" inside a farmland block the block gets a thin path-paved overlay, and where it says
# "lawn" inside a path block (rounded corners, bulges) the block gets a farmland-paved overlay.
SEAM_Y = 15.02      # just above the block top (and above the earth/gravel speckle overlays at 15.01)
def seam_typ(o, t):
    return {'P': mb(o, ['minecraft:dirt_path']), 'G': mb(o, ['minecraft:farmland']), 'N': NOT(isP(o))}[t]
def seam_cells(cells):
    """real-ish cells (P path, F farmland, anything else) -> cells for the seam shape"""
    return {c: {'P': 'P', 'F': 'G'}.get(t, 'N') for c, t in cells.items()}
def seam_mask(q, me, ta, tb, td):
    """16x16 bool mask of the overlay in quadrant q of a block of seam type `me` ('G' farmland / 'P' path)."""
    A, Bn, D = neighbours_for(q)
    H = window_H(q, {(0, 0): me, A: ta, Bn: tb, D: td}, 0)
    qx, qz = QUADS[q]
    xs = range(0, 8) if qx == 0 else range(8, 16)
    zs = range(0, 8) if qz == 0 else range(8, 16)
    want = 15 if me == 'G' else 16
    m = np.zeros((16, 16), bool)
    for z in zs:
        for x in xs:
            m[z, x] = H[z + 1, x + 1] == want
    return m
def seam_elements(m, tex):
    return [{'from': [x0, SEAM_Y, z0], 'to': [x1, SEAM_Y, z1], 'faces': {'up': {'uv': [x0, z0, x1, z1], 'texture': tex}}}
            for (x0, z0, x1, z1) in rects(m)]

# ---------------------------------------------------------------- build everything
def canon(els):
    return json.dumps(els, sort_keys=True)

def build(out_root, ns='realm', folder='path_edge_test'):
    mdir = f'{out_root}/assets/{ns}/models/block/{folder}'
    os.makedirs(mdir, exist_ok=True)
    def write_model(name, textures, els):
        m = {'loader': 'fusion:model', 'type': 'base', 'textures': textures, 'elements': els}
        json.dump(m, open(f'{mdir}/{name}.json', 'w'), separators=(',', ':'))   # minified: faster reloads
        return f'{ns}:block/{folder}/{name}'
    GT = {'particle': 'minecraft:block/dirt', 'top': 'minecraft:block/grass_block_top',
          'side': 'minecraft:block/grass_block_side', 'overlay': 'minecraft:block/grass_block_side_overlay',
          'side_top': 'minecraft:block/grass_block_top', 'path': 'minecraft:block/dirt_path_top',
          'path_side': 'minecraft:block/dirt_path_side', 'bottom': 'minecraft:block/dirt',
          'farm': 'minecraft:block/farmland', 'farm_moist': 'minecraft:block/farmland_moist'}
    grass_appends, path_appends = [], []
    stats = {}
    # lawn base: body box, bottom only
    base = write_model('lawn_base', GT, [{'from': [0, 0, 0], 'to': [16, 15, 16],
                        'faces': {'down': {'uv': [0, 0, 16, 16], 'texture': '#bottom', 'cullface': 'down'}}}])
    for q in QUADS:
        A, Bn, D = neighbours_for(q)
        groups = {}
        for kl in range(len(CLASSES)):
            for ta in 'PSGN':
                for tb in 'PSGN':
                    for td in 'PSGN':
                        cells = {(0, 0): 'G', A: ta, Bn: tb, D: td}
                        els = grass_tile(q, cells, kl)
                        groups.setdefault(canon(els), (els, {}))[1].setdefault((ta, tb, td), set()).add(kl)
        stats[q] = len(groups)
        offs = [(A[0], 0, A[1]), (Bn[0], 0, Bn[1]), (D[0], 0, D[1])]
        for i, (key, (els, cfgmap)) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1][1]))):
            ref = write_model(f'lawn_{q}_{i:02d}', GT, els)
            # partition configs by (has path?, set of plant classes) -> one append entry each
            parts = {}
            for cfg, kls in cfgmap.items():
                parts.setdefault(('P' in cfg, frozenset(kls)), []).append(cfg)
            for (has_p, kls), cfgs in sorted(parts.items(), key=lambda kv: (not kv[0][0], sorted(kv[0][1]))):
                cond = simplify_or(cfgs, offs)
                if has_p:
                    always = [j for j in range(3) if all(cfg[j] == 'P' for cfg in cfgs)]
                    some = [j for j in range(3) if any(cfg[j] == 'P' for cfg in cfgs)]
                    pre = [isP(offs[always[0]])] if always else [OR(*[isP(offs[j]) for j in some])]
                else:
                    others = [o for o in NEI8 if o not in offs]
                    pre = [OR(*[isP(o) for o in others])] + [NOT(isP(o)) for o in offs]
                if len(kls) == len(CLASSES):
                    tail = [SELF_OK]
                else:
                    tail = [mb((0, 1, 0), sorted(b for k in kls for b in CLASSES[k]))]
                grass_appends.append({'model': ref, 'show_breaking_overlay': True,
                                      'conditions': AND(*pre, *([cond] if cond else []), *tail)})
    # lowered floors, paved like the neighbouring path / farmland
    for q in QUADS:
        A, Bn, D = neighbours_for(q)
        offs = [(A[0], 0, A[1]), (Bn[0], 0, Bn[1]), (D[0], 0, D[1])]
        groups = {}
        for cfg in itertools.product('PFM-', repeat=3):
            if cfg == ('-', '-', '-'): continue
            els = floor_tile(q, *cfg)
            groups.setdefault(canon(els), (els, []))[1].append(cfg)
        for i, (key, (els, cfgs)) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1][1]))):
            ref = write_model(f'floor_{q}_{i:02d}', GT, els)
            # cheap gate (implied by floor_cond): a low neighbour in the slots this tile needs
            always = [j for j in range(3) if all(c[j] != '-' for c in cfgs)]
            gate = AND(*[isP(offs[j]) for j in always]) if always else \
                OR(*[isP(offs[j]) for j in range(3) if any(c[j] != '-' for c in cfgs)])
            grass_appends.append({'model': ref, 'show_breaking_overlay': False,
                                  'conditions': AND(gate, floor_cond(cfgs, offs), SELF_OK)})
    # backing walls: only where a lowered lawn edge meets something solid up to the top of the block
    BT = {'side': 'minecraft:block/grass_block_top', 'particle': '#side'}
    STAIRS = sorted(b for b in set(LISTS['26']) | set(LISTS['84']) if b.endswith('_stairs'))
    TOP_SLABS = sorted(b for b in LISTS['26'] if b.endswith('_slab'))
    OPP = {'north': 'south', 'south': 'north', 'west': 'east', 'east': 'west'}
    def stair_state(o, facings, halves):
        return OR(*[{'type': 'match_state', 'offset': list(o), 'apply_model_rotation': False, 'block': b,
                     'properties': {'facing': facings, 'half': halves}} for b in STAIRS])
    for d, (dx, dz) in DIRV.items():
        o = (dx, 0, dz)
        inward = OPP[d]
        def wall(a, b):
            if d in ('north', 'south'):
                zz = 0.01 if d == 'north' else 15.99
                return {'from': [a, 15, zz], 'to': [b, 16, zz], 'faces': {inward: {'uv': [a, 0, b, 1], 'texture': '#side', 'tintindex': 0}}}
            xx = 0.01 if d == 'west' else 15.99
            return {'from': [xx, 15, a], 'to': [xx, 16, b], 'faces': {inward: {'uv': [a, 0, b, 1], 'texture': '#side', 'tintindex': 0}}}
        full_ref = write_model(f'lawn_backing_{d}', BT, [wall(0, 16)])
        full_cond = OR(AND(mb(o, FULL_NEIGHBOURS), NOT(isG(o))),
                       AND(mb(o, STAIRS), stair_state(o, ['north', 'south', 'east', 'west'], ['top'])),
                       AND(mb(o, STAIRS), stair_state(o, [OPP[d]], ['bottom'])),
                       AND(mb(o, TOP_SLABS), OR(*[{'type': 'match_state', 'offset': list(o), 'apply_model_rotation': False,
                                                   'block': b, 'properties': {'type': ['top', 'double']}} for b in TOP_SLABS])))
        grass_appends.append({'model': full_ref, 'show_breaking_overlay': False, 'conditions': AND(full_cond, SELF_OK, ANY_P)})
        # side-on bottom stairs: only the tall half of the edge
        sides = ('west', 'east') if d in ('north', 'south') else ('north', 'south')
        for facing, (a, b) in zip(sides, ((0, 8), (8, 16))):
            ref = write_model(f'lawn_backing_{d}_{facing}_half', BT, [wall(a, b)])
            grass_appends.append({'model': ref, 'show_breaking_overlay': False,
                                  'conditions': AND(mb(o, STAIRS), stair_state(o, [facing], ['bottom']), SELF_OK, ANY_P)})
    # path: raised lawn inside path blocks (rounded outer corners + organic bulges)
    PT = {'edge': 'realm:block/path_edge_test/corner_grass', 'particle': '#edge'}
    for q in QUADS:
        A, Bn, D = neighbours_for(q)
        offs = [(A[0], 0, A[1]), (Bn[0], 0, Bn[1]), (D[0], 0, D[1])]
        groups = {}
        for ta in 'PSGN':
            for tb in 'PSGN':
                for td in 'PSGN':
                    cells = {(0, 0): 'P', A: ta, Bn: tb, D: td}
                    O = path_owners(q, cells)
                    if (O == -2).all(): continue
                    groups.setdefault(O.tobytes(), (O, cells, []))[2].append((ta, tb, td))
        for i, (key, (O, cells, cfgs)) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1][2]))):
            cond = simplify_or(cfgs, offs)
            for j in (-1, 0, 1, 2):
                if not (O == j).any(): continue
                els = path_tile(q, cells, O == j)
                if j == -1:     # rim with no lawn neighbour at this corner: grass, as before
                    ref = write_model(f'path_corner_{q}_{i:02d}', PT, els)
                    path_appends.append({'model': ref, 'show_breaking_overlay': True, 'conditions': cond if cond else {'type': 'true'}})
                    continue
                for k in LAWN_KINDS:
                    tex = PT if k == 'grass' else {'edge': 'minecraft:block/' + DIRT_TEX[k][0], 'particle': '#edge'}
                    ref = write_model(f'path_corner_{q}_{i:02d}_{"abd"[j]}_{k}', tex, els)
                    kc = kind_cond(offs[j], k)
                    path_appends.append({'model': ref, 'show_breaking_overlay': True,
                                         'conditions': AND(cond, kc) if cond else kc})
    for q in QUADS:
        A, Bn, D = neighbours_for(q)
        offs = [(A[0], 0, A[1]), (Bn[0], 0, Bn[1]), (D[0], 0, D[1])]
        groups = {}
        for ta in 'PG':
            for tb in 'PG':
                for td in 'PG':
                    for kl in (1, 2, 3):
                        m = path_tuft(q, ta, tb, td, kl)
                        if m is None: continue
                        els = tuft_elements(m)
                        groups.setdefault(canon(els), (els, []))[1].append((ta, tb, td, kl))
        for i, (els, cfgs) in enumerate(groups.values()):
            ref = write_model(f'path_tuft_{q}_{i:02d}', PT, els)
            ors = []
            for (ta, tb, td, kl) in cfgs:
                lawn_o = offs[0] if ta == 'G' else offs[1]
                ors.append(AND(mb(up(lawn_o), CLASSES[kl]), typ(offs[0], ta, 'PSGN'), typ(offs[1], tb, 'PSGN'), typ(offs[2], td, 'PSGN')))
            path_appends.append({'model': ref, 'show_breaking_overlay': True, 'conditions': OR(*ors)})
    grass_mod = {'targets': [{'block': 'minecraft:grass_block', 'properties': {'snowy': ['false']}}],
                 'default_model_overrides': [{'model': base, 'conditions': AND(SELF_OK, ANY_P)}],
                 'append_models': grass_appends}
    # dirt variants: same appends, lawn tiles/backing walls re-textured (no tint, no side overlay)
    dirt_mods = {}
    for k in LAWN_KINDS[1:]:
        top, side = ('minecraft:block/' + t for t in DIRT_TEX[k])
        refmap = {}
        def variant(ref):
            if ref in refmap: return refmap[ref]
            name = ref.split('/')[-1]
            if not name.startswith('lawn_') or name == 'lawn_base':
                refmap[ref] = ref; return ref
            m = json.load(open(f'{mdir}/{name}.json'))
            if name.startswith('lawn_backing'):
                tex = {'side': top, 'particle': '#side'}
            else:
                tex = {'particle': side, 'top': top, 'side_top': top, 'side': side,
                       'path_side': m['textures']['path_side'], 'bottom': m['textures']['bottom']}
            els = []
            for e in m['elements']:
                faces = {}
                for d, fc in e['faces'].items():
                    if fc['texture'] == '#overlay': continue
                    fc = dict(fc); fc.pop('tintindex', None); faces[d] = fc
                if faces: els.append(dict(e, faces=faces))
            refmap[ref] = write_model(f'{name}_{k}', tex, els)
            return refmap[ref]
        dirt_mods[k] = {'targets': [kind_target(k)],
                        'default_model_overrides': [{'model': base, 'conditions': AND(SELF_OK, ANY_P)}],
                        'append_models': [dict(a, model=variant(a['model'])) for a in grass_appends]}
    # farmland <-> path seam overlays
    ST = {'path': 'minecraft:block/dirt_path_top', 'farm': 'minecraft:block/farmland',
          'farm_moist': 'minecraft:block/farmland_moist', 'particle': '#path'}
    farm_seam, path_seam = [], []
    for q in QUADS:
        A, Bn, D = neighbours_for(q)
        offs = [(A[0], 0, A[1]), (Bn[0], 0, Bn[1]), (D[0], 0, D[1])]
        for me in 'GP':
            groups = {}
            for cfg in itertools.product('PGN', repeat=3):
                m = seam_mask(q, me, *cfg)
                if m.any(): groups.setdefault(m.tobytes(), (m, []))[1].append(cfg)
            for i, (m, cfgs) in enumerate(sorted(groups.values(), key=lambda v: -len(v[1]))):
                def shape_cond(cfg):
                    return [seam_typ(o, t) for o, t in zip(offs, cfg)]
                if me == 'G':    # path paving creeping onto the farmland block
                    ref = write_model(f'seam_farm_{q}_{i:02d}', ST, seam_elements(m, '#path'))
                    farm_seam.append({'model': ref, 'show_breaking_overlay': False,
                                      'conditions': OR(*[AND(*shape_cond(c)) for c in cfgs])})
                else:            # farmland paving in the path block, dry or moist like the nearest farmland
                    for moist in (False, True):
                        ref = write_model(f'seam_path_{q}_{i:02d}_{"moist" if moist else "dry"}', ST,
                                          seam_elements(m, '#farm_moist' if moist else '#farm'))
                        ors = []
                        for c in cfgs:
                            if 'G' not in c: continue
                            ors.append(AND(*shape_cond(c), _farm(offs[c.index('G')], moist)))
                        assert len(ors) == len(cfgs)
                        path_seam.append({'model': ref, 'show_breaking_overlay': False, 'conditions': OR(*ors)})
    stats['seam'] = (len(farm_seam), len(path_seam))
    farm_mod = {'targets': ['minecraft:farmland'], 'append_models': path_appends + farm_seam}
    path_appends = path_appends + path_seam
    return grass_mod, path_appends, stats, farm_mod, dirt_mods

def simplify_or(cfgs, offs):
    """Build an OR condition for the list of (ta,tb,td) configs, collapsing full universes per slot."""
    U = ['PSGN', 'PSGN', 'PSGN']
    cfgset = set(cfgs)
    # try collapsing slot-by-slot: represent as product sets
    # greedy: group by (tb,td) -> set of ta, etc.
    def cond_for(slot, vals):
        o = offs[slot]; u = U[slot]
        if set(vals) == set(u): return None
        if len(vals) == 1: return typ(o, vals[0], u)
        # complement trick
        comp = [t for t in u if t not in vals]
        if len(comp) == 1 and comp[0] in 'PGS':
            c = {'P': isP(o), 'G': isG(o), 'S': isS(o)}[comp[0]]
            return NOT(c)
        return OR(*[typ(o, t, u) for t in vals])
    # decompose into product boxes greedily
    remaining = set(cfgset); terms = []
    while remaining:
        c0 = sorted(remaining)[0]
        box = [{c0[0]}, {c0[1]}, {c0[2]}]
        for slot in range(3):
            for t in U[slot]:
                trial = [set(b) for b in box]; trial[slot].add(t)
                if all(c in cfgset for c in itertools.product(*trial)):
                    box = trial
        for c in itertools.product(*box): remaining.discard(c)
        parts = [cond_for(s, sorted(box[s], key=U[s].index)) for s in range(3)]
        parts = [p for p in parts if p is not None]
        terms.append(AND(*parts) if len(parts) > 1 else (parts[0] if parts else None))
    if any(t is None for t in terms): return None
    return OR(*terms)

if __name__ == '__main__':
    out = sys.argv[1]
    gm, pa, stats, fm, dm = build(out)
    print('distinct lawn tiles per corner:', stats, 'appends:', len(gm['append_models']))
    json.dump({'gm': gm, 'pa': pa}, open(out + '/_gen.json', 'w'))


def global_height(cells, tx, tz, klass=None):
    """Ground truth for the organic shape: the (noisy) window of the texel's nearest block corner."""
    c = cell_of((tx, tz)); T = cells.get(c)
    if T not in ('G', 'P'): return None
    qx, qz = math.floor((tx + 8) / 16), math.floor((tz + 8) / 16)
    cfg4 = tuple(cells.get((qx + dx, qz + dz), 'N') for (dx, dz) in CORNER_CELLS)
    slot = CORNER_CELLS[(c[0] - qx, c[1] - qz)]
    if T == 'G':
        W = own_quarter(cfg4, slot, (klass or {}).get(c, 0))
    else:
        W = noisy_window(cfg4)[0]
    v = W[tz - 16 * qz + 8, tx - 16 * qx + 8]
    if T == 'P' and v != 1:
        lx, lz = tx - 16 * c[0], tz - 16 * c[1]
        q = ('n' if lz < 8 else 's') + ('w' if lx < 8 else 'e')
        A, Bn, D = neighbours_for(q)
        ta, tb, td = (cells.get((c[0] + o[0], c[1] + o[1]), 'N') for o in (A, Bn, D))
        if ta == 'G' or tb == 'G':
            lawn = (c[0] + A[0], c[1] + A[1]) if ta == 'G' else (c[0] + Bn[0], c[1] + Bn[1])
            m = path_tuft(q, ta, tb, td, (klass or {}).get(lawn, 0))
            if m is not None and m[lz, lx]: return 16
    return 16 if v == 1 else 15


def seam_kind(cells, tx, tz):
    """Ground truth for the farmland/path seam: paving ('P' path / 'F' farmland) of texel (tx,tz); cells use
    P path, F farmland, anything else. None if the texel is in neither."""
    c = cell_of((tx, tz))
    if cells.get(c) not in ('P', 'F'): return None
    return 'P' if global_height(seam_cells(cells), tx, tz) == 15 else 'F'
