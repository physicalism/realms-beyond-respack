"""Tiny Fusion/Minecraft block-model simulator for auditing the Realms Beyond path edges.

- Evaluates Fusion model-modifier conditions (match_block / match_state / and / or / not).
- Places vanilla-ish base models + Fusion overrides/appends in a test scene.
- Rasterises every face (orthographic, z-buffer, per-pixel UV) from several views.
- Flags: see-through holes (void visible), back faces visible, z-fighting.
"""
import json, os, math
import numpy as np
from PIL import Image

ROOT = None  # pack root (dir containing assets/)
_model_cache = {}

def set_root(r):
    global ROOT, _model_cache, _tex_cache, _mods
    ROOT = r; _model_cache = {}; _tex_cache = {}; _mods = None

def load_model(ident):
    if ident in _model_cache: return _model_cache[ident]
    ns, p = ident.split(':')
    m = json.load(open(f'{ROOT}/assets/{ns}/models/{p}.json'))
    _model_cache[ident] = m
    return m

_mods = None
def modifiers():
    global _mods
    if _mods is None:
        _mods = []
        d = f'{ROOT}/assets/realm/fusion/model_modifiers/blocks'
        for f in sorted(os.listdir(d)):
            if f.endswith('.json'):
                _mods.append(json.load(open(os.path.join(d, f))))
    return _mods

# ---------------------------------------------------------------- world
AIR = ('minecraft:air', {})
def B(name, **props):
    if ':' not in name: name = 'minecraft:' + name
    if name == 'minecraft:grass_block': props.setdefault('snowy', 'false')
    return (name, {k: str(v).lower() for k, v in props.items()})

class World(dict):
    def get(self, p):
        return dict.get(self, tuple(p), AIR)

def ev(cond, world, pos):
    t = cond['type']
    if t == 'true': return True
    if t == 'false': return False
    if t == 'and': return all(ev(c, world, pos) for c in cond['predicates'])
    if t == 'or': return any(ev(c, world, pos) for c in cond['predicates'])
    if t == 'not': return not ev(cond['predicate'], world, pos)
    off = cond.get('offset', [0, 0, 0])
    name, props = world.get((pos[0]+off[0], pos[1]+off[1], pos[2]+off[2]))
    if t == 'match_block':
        bl = cond.get('blocks') or [cond['block']]
        return name in bl
    if t == 'match_state':
        if name != cond['block']: return False
        return all(props.get(k) in v for k, v in cond.get('properties', {}).items())
    raise ValueError(t)

def target_ok(tg, blk):
    name, props = blk
    if isinstance(tg, str): return tg == name
    if tg['block'] != name: return False
    return all(props.get(k) in v for k, v in tg.get('properties', {}).items())

# ---------------------------------------------------------------- vanilla-ish base models
def cube(fr, to, tex, cull=True, tint=None):
    faces = {}
    for d in ['down', 'up', 'north', 'south', 'west', 'east']:
        f = {'texture': tex[d] if isinstance(tex, dict) else tex}
        if cull: f['cullface'] = d
        faces[d] = f
    return {'from': fr, 'to': to, 'faces': faces}

def vanilla(blk):
    name, props = blk
    n = name.split(':')[1]
    T = lambda t: 'minecraft:block/' + t
    if n == 'grass_block':
        tex = {'down': T('dirt'), 'up': T('grass_block_top'), **{d: 'GS' for d in ['north', 'south', 'west', 'east']}}
        return [cube([0,0,0],[16,16,16], tex)]
    if n == 'dirt_path':
        tex = {'down': T('dirt'), 'up': T('dirt_path_top'), **{d: T('dirt_path_side') for d in ['north','south','west','east']}}
        e = cube([0,0,0],[16,15,16], tex)
        e['faces']['up'].pop('cullface')
        for d in ['north','south','west','east']: e['faces'][d]['uv'] = [0,1,16,16]
        return [e]
    if n == 'farmland':
        e = cube([0,0,0],[16,15,16], {'down': T('dirt'), 'up': T('farmland'), **{d: T('dirt') for d in ['north','south','west','east']}})
        e['faces']['up'].pop('cullface')
        for d in ['north','south','west','east']: e['faces'][d]['uv'] = [0,1,16,16]
        return [e]
    if n == 'void':
        return [{'from': [0,16,0], 'to': [16,16,16], 'faces': {'up': {'texture': T('void'), 'uv': [0,0,16,16]}}}]
    if n in ('dirt', 'coarse_dirt', 'stone', 'gravel', 'rooted_dirt', 'podzol'):
        return [cube([0,0,0],[16,16,16], T(n))]
    if n.endswith('_stairs'):
        f = props.get('facing', 'north')
        half = [cube([0,0,0],[16,8,16], T('oak_planks'))]
        half[0]['faces']['up'].pop('cullface')
        back = {'north': ([0,8,0],[16,16,8]), 'south': ([0,8,8],[16,16,16]),
                'west': ([0,8,0],[8,16,16]), 'east': ([8,8,0],[16,16,16])}[f]
        e = cube(back[0], back[1], T('oak_planks'))
        for d in list(e['faces']):
            if d != f and d != 'up': pass
        # only faces on block boundary keep cullface
        for d, fc in e['faces'].items():
            on_bound = {'down': e['from'][1]==0, 'up': e['to'][1]==16, 'north': e['from'][2]==0, 'south': e['to'][2]==16,
                        'west': e['from'][0]==0, 'east': e['to'][0]==16}[d]
            if not on_bound: fc.pop('cullface', None)
        return half + [e]
    if n.endswith('_slab'):
        e = cube([0,0,0],[16,8,16], T('oak_planks')); e['faces']['up'].pop('cullface')
        for d in ['north','south','west','east']: e['faces'][d].pop('cullface')
        return [e]
    if n.endswith('_fence'):
        e = cube([6,0,6],[10,16,10], T('oak_planks'))
        for d in ['north','south','west','east']: e['faces'][d].pop('cullface')
        return [e]
    if 'torch' in n:
        e = cube([7,0,7],[9,10,9], T('torch'))
        for d in ['north','south','west','east','up']: e['faces'][d].pop('cullface', None)
        return [e]
    if n in ('wheat', 'carrots', 'potatoes', 'short_grass', 'tall_grass', 'fern', 'poppy', 'dandelion', 'bush', 'pink_petals'):
        return []  # ignore plants for geometry
    if n == 'air':
        return []
    raise ValueError(n)

# what counts as a full opaque neighbour for culling a face of direction d
FULL = {'grass_block', 'dirt', 'coarse_dirt', 'stone', 'gravel', 'rooted_dirt', 'podzol'}
def occludes(blk, d):
    """Does blk fully cover its face opposite to d (i.e. the face touching us)?"""
    n = blk[0].split(':')[1]
    if n in FULL: return True
    opp = {'down':'up','up':'down','north':'south','south':'north','west':'east','east':'west'}[d]
    if n in ('dirt_path', 'farmland'):
        return opp == 'down'
    if n.endswith('_slab'): return opp == 'down'
    if n.endswith('_stairs'):
        return opp == 'down' or opp == blk[1].get('facing', 'north')
    return False

DIRS = {'down': (0,-1,0), 'up': (0,1,0), 'north': (0,0,-1), 'south': (0,0,1), 'west': (-1,0,0), 'east': (1,0,0)}

def block_models(world, pos):
    """Return list of (model_dict_or_elements, textures, tag) for block at pos."""
    blk = world.get(pos)
    out = []
    base = None
    appends = []
    for mod in modifiers():
        if not any(target_ok(t, blk) for t in mod['targets']): continue
        for o in mod.get('default_model_overrides', []):
            if isinstance(o, str):
                base = base or o
            elif base is None and ev(o['conditions'], world, pos):
                base = o['model']
        for a in mod.get('append_models', []):
            if ev(a['conditions'], world, pos):
                appends.append(a['model'])
    if base:
        m = load_model(base); out.append((m['elements'], m['textures'], base))
    else:
        out.append((vanilla(blk), {}, 'vanilla:' + blk[0]))
    for a in appends:
        m = load_model(a); out.append((m['elements'], m['textures'], a))
    return out

# ---------------------------------------------------------------- textures
_tex_cache = {}
rng = np.random.default_rng(7)
def noisy(base, amp=14, seed=0):
    r = np.random.default_rng(seed)
    a = np.array(base, float)[None, None, :] + r.integers(-amp, amp+1, (16, 16, 1))
    return np.clip(a, 0, 255)

GREEN = (110, 160, 70)
def synth(name):
    if name == 'minecraft:block/grass_block_top': return noisy(GREEN, 16, 1)
    if name == 'minecraft:block/dirt': return noisy((134, 96, 67), 18, 2)
    if name == 'minecraft:block/dirt_path_top': return noisy((176, 150, 92), 12, 3)
    if name == 'minecraft:block/dirt_path_side':
        t = noisy((134, 96, 67), 18, 4)
        top = noisy((176, 150, 92), 10, 5)
        t[0:2] = top[0:2]
        r = np.random.default_rng(9)
        for x in range(16):
            if r.random() < .5: t[2, x] = top[2, x]
        return t
    if name == 'GS':
        t = noisy((134, 96, 67), 18, 2)
        ov = Image.open(f'{ROOT}/assets/realm/textures/block/path_edge_test/side_grass_overlay.png').convert('RGBA')
        ov = np.array(ov, float)
        g = noisy(GREEN, 16, 6)
        m = ov[..., 3:4] > 0
        return np.where(m, g * ov[..., :3] / 170, t)
    if name == 'minecraft:block/oak_planks': return noisy((160, 120, 70), 10, 8)
    if name == 'minecraft:block/stone': return noisy((125, 125, 125), 10, 10)
    if name == 'minecraft:block/farmland': return noisy((90, 60, 40), 10, 11)
    if name == 'minecraft:block/torch': return noisy((240, 200, 80), 5, 12)
    if name == 'minecraft:block/void': return np.full((16, 16, 3), (255, 0, 255), float)
    if name in ('minecraft:block/coarse_dirt', 'minecraft:block/rooted_dirt', 'minecraft:block/podzol'):
        return noisy((120, 85, 60), 22, 13)
    if name == 'minecraft:block/gravel': return noisy((130, 125, 120), 25, 14)
    return None

def texture(name):
    """returns (rgb 16x16x3 float, alpha 16x16 bool)"""
    if name in _tex_cache: return _tex_cache[name]
    s = synth(name)
    if s is not None:
        res = (s, np.ones((16, 16), bool))
    else:
        ns, p = name.split(':')
        im = np.array(Image.open(f'{ROOT}/assets/{ns}/textures/{p}.png').convert('RGBA'), float)[:16]
        rgb, a = im[..., :3], im[..., 3] > 0
        mc = f'{ROOT}/assets/{ns}/textures/{p}.png.mcmeta'
        if os.path.exists(mc) and 'biome_grass' in open(mc).read():
            rgb = rgb / 255 * np.array(GREEN) * 1.6
        res = (rgb, a)
    _tex_cache[name] = res
    return res

def resolve(texmap, ref, depth=0):
    if ref.startswith('#'):
        v = texmap.get(ref[1:])
        if v is None: return None
        return resolve(texmap, v, depth+1)
    if ':' not in ref and ref != 'GS': ref = 'minecraft:' + ref
    return ref

# ---------------------------------------------------------------- face collection
AUTO_UV = {
    'down':  lambda f, t: [f[0], 16-t[2], t[0], 16-f[2]],
    'up':    lambda f, t: [f[0], f[2], t[0], t[2]],
    'north': lambda f, t: [16-t[0], 16-t[1], 16-f[0], 16-f[1]],
    'south': lambda f, t: [f[0], 16-t[1], t[0], 16-f[1]],
    'west':  lambda f, t: [f[2], 16-t[1], t[2], 16-f[1]],
    'east':  lambda f, t: [16-t[2], 16-t[1], 16-f[2], 16-f[1]],
}
def corners(d, f, t):
    """origin, U axis vector, V axis vector (3D) for (u,v) in [0,1]^2."""
    x1, y1, z1 = f; x2, y2, z2 = t
    if d == 'up':    return (x1, y2, z1), (x2-x1, 0, 0), (0, 0, z2-z1)
    if d == 'down':  return (x1, y1, z2), (x2-x1, 0, 0), (0, 0, -(z2-z1))
    if d == 'north': return (x2, y2, z1), (-(x2-x1), 0, 0), (0, -(y2-y1), 0)
    if d == 'south': return (x1, y2, z2), (x2-x1, 0, 0), (0, -(y2-y1), 0)
    if d == 'west':  return (x1, y2, z1), (0, 0, z2-z1), (0, -(y2-y1), 0)
    if d == 'east':  return (x2, y2, z2), (0, 0, -(z2-z1)), (0, -(y2-y1), 0)

class Face:
    __slots__ = ('o', 'U', 'V', 'n', 'uv', 'rot', 'tex', 'texname', 'tag', 'pos', 'dir', 'tint')

def collect(world, positions):
    faces = []
    for pos in positions:
        blk = world.get(pos)
        if blk[0] == 'minecraft:air': continue
        has_overlay = {}
        for els, texmap, tag in block_models(world, pos):
            ov_present = any(fc.get('texture') == '#overlay' for e in els for fc in e['faces'].values())
            for e in els:
                for d, fc in e['faces'].items():
                    if 'cullface' in fc:
                        dd = DIRS[fc['cullface']]
                        nb = world.get((pos[0]+dd[0], pos[1]+dd[1], pos[2]+dd[2]))
                        if occludes(nb, fc['cullface']): continue
                    ref = fc['texture']
                    if ref == '#overlay': continue  # merged into GS
                    tn = resolve(texmap, ref) if texmap else ref
                    if tn is None: continue
                    if tn == 'minecraft:block/grass_block_side' and ov_present: tn = 'GS'
                    F = Face()
                    o, U, V = corners(d, e['from'], e['to'])
                    F.o = np.array(o, float) / 16 + np.array(pos, float)
                    F.U = np.array(U, float) / 16; F.V = np.array(V, float) / 16
                    F.n = np.array(DIRS[d], float)
                    F.uv = fc.get('uv') or AUTO_UV[d](e['from'], e['to'])
                    F.rot = fc.get('rotation', 0)
                    F.texname = tn; F.tag = tag; F.pos = pos; F.dir = d
                    faces.append(F)
    return faces

# ---------------------------------------------------------------- rasteriser
def view_basis(yaw_deg, pitch_deg):
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    # camera looks along -fwd ... fwd is direction from scene toward camera
    fwd = np.array([math.sin(yaw)*math.cos(pitch), math.sin(pitch), math.cos(yaw)*math.cos(pitch)])
    up0 = np.array([0, 1, 0.]) if abs(pitch_deg) < 89 else np.array([0, 0, -1.])
    right = np.cross(up0, fwd); right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return right, up, fwd

SHADE = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'west': .6, 'east': .6}

def render(faces, yaw, pitch, scale=6, center=None, size=None):
    R, Uv, Fw = view_basis(yaw, pitch)
    pts = np.array([f.o for f in faces] + [f.o + f.U + f.V for f in faces])
    sx = pts @ R; sy = pts @ Uv
    if center is None: center = ((sx.min()+sx.max())/2, (sy.min()+sy.max())/2)
    W = int((sx.max()-sx.min())*16*scale)+8 if size is None else size[0]
    H = int((sy.max()-sy.min())*16*scale)+8 if size is None else size[1]
    k = 16*scale
    img = np.zeros((H, W, 3)); img[:] = (40, 40, 60)
    zb = np.full((H, W), -1e9); zb2 = np.full((H, W), -1e9)
    fid = np.full((H, W), -1, int); fid2 = np.full((H, W), -1, int)
    back = np.zeros((H, W), bool)
    for i, f in enumerate(faces):
        o = f.o; U = f.U; V = f.V
        a = np.array([o@R, o@Uv]); u2 = np.array([U@R, U@Uv]); v2 = np.array([V@R, V@Uv])
        M = np.array([u2, v2]).T * k
        if abs(np.linalg.det(M)) < 1e-9: continue
        Mi = np.linalg.inv(M)
        p0 = (a - np.array(center)) * k + np.array([W/2, H/2])
        cs = [p0, p0+M[:, 0], p0+M[:, 1], p0+M[:, 0]+M[:, 1]]
        xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
        x0, x1 = max(0, int(math.floor(min(xs)))), min(W, int(math.ceil(max(xs)))+1)
        y0, y1 = max(0, int(math.floor(min(ys)))), min(H, int(math.ceil(max(ys)))+1)
        if x0 >= x1 or y0 >= y1: continue
        gx, gy = np.meshgrid(np.arange(x0, x1)+.5, np.arange(y0, y1)+.5)
        rel = np.stack([gx-p0[0], gy-p0[1]], -1) @ Mi.T
        s, t = rel[..., 0], rel[..., 1]
        inside = (s >= 0) & (s < 1) & (t >= 0) & (t < 1)
        if not inside.any(): continue
        depth = (o@Fw) + s*(U@Fw) + t*(V@Fw)
        # texture lookup
        rgb, al = texture(f.texname)
        u1_, v1_, u2_, v2_ = f.uv
        ss, tt = s, t
        r = f.rot % 360
        if r == 90: ss, tt = t, 1-s
        elif r == 180: ss, tt = 1-s, 1-t
        elif r == 270: ss, tt = 1-t, s
        tu = u1_ + (u2_-u1_)*ss; tv = v1_ + (v2_-v1_)*tt
        iu = np.clip(np.floor(tu).astype(int), 0, 15); iv = np.clip(np.floor(tv).astype(int), 0, 15)
        facing = (f.n @ Fw) > 0
        if not facing: continue  # Minecraft culls back faces
        opaque = al[iv, iu] & inside
        sub = (slice(y0, y1), slice(x0, x1))
        z = zb[sub]; z2 = zb2[sub]; fi = fid[sub]; fi2 = fid2[sub]
        closer = opaque & (depth > z + 1e-6)
        tie = opaque & (np.abs(depth - z) <= 1e-6)
        # second layer bookkeeping for z-fight detection
        z2[closer] = z[closer]; fi2[closer] = fi[closer]
        z2[tie & (depth > z2)] = depth[tie & (depth > z2)]; fi2[tie] = i
        z[closer] = depth[closer]; fi[closer] = i
        col = rgb[iv, iu] * SHADE[f.dir]
        img[sub][closer] = col[closer]
        back[sub][closer] = not facing
    return img, fid, fid2, zb, zb2, back, (R, Uv, Fw)

VIEWS = [(yaw, pitch) for pitch in (20, 40, 65) for yaw in (15, 60, 105, 150, 195, 240, 285, 330)] + [(0, 90)]

def audit(world, positions, focus=None, views=VIEWS, scale=4):
    faces = collect(world, positions)
    issues = {'void': 0, 'backface': 0, 'zfight': 0}
    details = []
    imgs = []
    for yaw, pitch in views:
        img, fid, fid2, zb, zb2, back, basis = render(faces, yaw, pitch, scale)
        vis = fid >= 0
        void = np.zeros_like(vis)
        idx = np.unique(fid[vis])
        for i in idx:
            if faces[i].texname == 'minecraft:block/void':
                void |= (fid == i)
        from scipy.ndimage import binary_erosion
        from scipy.ndimage import label
        def drop_small(m, n=4):
            lab, k = label(m)
            if k == 0: return m
            sizes = np.bincount(lab.ravel())
            keep = sizes >= n; keep[0] = False
            return keep[lab]
        void = drop_small(void)
        bf = binary_erosion(back & vis, iterations=1)
        # z-fight: second face equally near with different texture and same facing
        zf = (fid2 >= 0) & (np.abs(zb - zb2) < 1e-6)
        zf_real = np.zeros_like(zf)
        for (a, b) in set(zip(fid[zf].tolist(), fid2[zf].tolist())):
            if a == b: continue
            fa, fb = faces[a], faces[b]
            if not np.allclose(fa.n, fb.n): continue
            if fa.texname != fb.texname or tuple(fa.uv) != tuple(fb.uv) or fa.tag != fb.tag:
                zf_real |= (fid == a) & (fid2 == b)
        zf_real = binary_erosion(zf_real, iterations=1)
        nv, nb, nz = int(void.sum()), int(bf.sum()), int(zf_real.sum())
        issues['void'] += nv; issues['backface'] += nb; issues['zfight'] += nz
        if nv or nb or nz:
            for i in np.unique(fid[void | bf | zf_real]):
                f = faces[i]; details.append(((yaw, pitch), f.pos, f.dir, f.tag.split('/')[-1], f.texname.split('/')[-1],
                                              'void' if f.texname.endswith('void') else ('back' if (bf & (fid == i)).any() else 'zf')))
        mark = img.copy()
        mark[void] = (255, 0, 255); mark[bf] = (255, 0, 0); mark[zf_real] = (0, 255, 255)
        imgs.append(mark)
    return issues, details, imgs, faces

def save(img, path):
    Image.fromarray(np.clip(img[::-1], 0, 255).astype(np.uint8)).save(path)

def topdown(world, positions, x0, z0, x1, z1):
    """per-texel top classification over blocks [x0,x1)x[z0,z1) at the grass/path layer: returns (height, texname) grids"""
    faces = collect(world, positions)
    W, H = (x1-x0)*16, (z1-z0)*16
    hgt = np.full((H, W), -1e9); cls = np.full((H, W), '', object)
    for f in faces:
        if f.dir != 'up': continue
        rgb, al = texture(f.texname)
        xa, za = f.o[0], f.o[2]
        xb, zb_ = xa + f.U[0], za + f.V[2]
        y = f.o[1]
        for tz in range(int(round(za*16)), int(round(zb_*16))):
            for tx in range(int(round(xa*16)), int(round(xb*16))):
                gx, gz = tx - x0*16, tz - z0*16
                if not (0 <= gx < W and 0 <= gz < H): continue
                s = (tx/16 + 1/32 - xa) / (xb - xa); t = (tz/16 + 1/32 - za) / (zb_ - za)
                u1_, v1_, u2_, v2_ = f.uv
                iu = min(15, int(u1_ + (u2_-u1_)*s)); iv = min(15, int(v1_ + (v2_-v1_)*t))
                if not al[iv, iu]: continue
                if y > hgt[gz, gx] + 1e-6:
                    hgt[gz, gx] = y; cls[gz, gx] = f.texname
    return hgt, cls
