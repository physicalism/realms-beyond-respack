#!/usr/bin/env python3
"""Animated kitchen props (Realms Beyond). Usage: gen_kitchen.py <pack_root>
Rewrites assets/realm/{items,models/item,textures/item}/decorations/kitchen_{bread_cutting,vegetable_pan,rotating_spit}*
(the item IDs are unchanged, so placed frames keep working).

Model space: 1 unit = 1 block px; every prop uses an INVISIBLE item frame and the same display maths as the
blacksmith props:
- TOP props (bread board, vegetable pan): frame on the TOP of the block (counter, furnace, smoker).
  Model (x, y, z) -> block-space (x/16, 1 + (y-8)/16, z/16); model y 8 is the block's top face.
- WALL prop (rotating spit): frame on the BACK WALL of the fireplace, in the open block straight above the
  campfire. Model (8,8,8) is the centre of that wall face and model z > 8 is the fireplace slot in front of it;
  model y 0 is the top of the campfire's block, x 0 and 16 are the brick cheeks either side.
Animation: each moving part has one copy per pose; each copy samples its own atlas patch, which is opaque only
in the frames where that pose shows (the Lucky Ivy / anvil hammer technique). Heat is light_emission 15."""
import json, os, random, sys, zlib
from PIL import Image

FS = 128                                   # frame size in px; uv = px * 16 / FS
FACES = ('north', 'south', 'west', 'east', 'up', 'down')


def clamp(v): return max(0, min(255, int(round(v))))
def mul(c, k): return tuple(clamp(x * k) for x in c[:3])
def mix(a, b, t): return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- materials
# Each painter: (w, h, face, rng) -> 2D list of rgb. Kept flat and chunky: a base colour, a little pixel
# noise, a lit top row and a darker bottom row on side faces, and a pattern where the object needs one.
def solid(base, amp=0.06, rim=True):
    def paint(w, h, face, rng):
        g = [[mul(base, 1 + rng.uniform(-amp, amp)) for _ in range(w)] for _ in range(h)]
        if rim and face not in ('up', 'down') and h >= 3:
            g[0] = [mul(c, 1.10) for c in g[0]]
            g[-1] = [mul(c, 0.86) for c in g[-1]]
        return g
    return paint


def wood(base, dark):
    def paint(w, h, face, rng):
        g = []
        for y in range(h):
            row = []
            stripe = rng.random() < 0.35
            for x in range(w):
                c = mix(base, dark, 0.55) if stripe and rng.random() < 0.8 else mul(base, 1 + rng.uniform(-.05, .05))
                row.append(c)
            g.append(row)
        if face not in ('up', 'down') and h >= 2: g[-1] = [mul(c, .85) for c in g[-1]]
        return g
    return paint


CRUST, CRUST_D, CRUST_L = (196, 124, 58), (140, 80, 36), (226, 168, 92)
CRUMB, CRUMB_D = (246, 226, 178), (220, 192, 136)


def crust_top(w, h, face, rng):              # scored bloomer top: diagonal cuts
    g = [[mul(CRUST, 1 + rng.uniform(-.05, .05)) for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if (x + y) % 3 == 0 and 0 < y < h - 1: g[y][x] = CRUST_L if (x + y) % 6 == 0 else CRUST_D
    return g


def crust_side(w, h, face, rng):
    g = [[mul(CRUST, 1 + rng.uniform(-.06, .06)) for _ in range(w)] for _ in range(h)]
    if h >= 2: g[0] = [mul(CRUST_L, 1 + rng.uniform(-.04, .04)) for _ in range(w)]; g[-1] = [mul(CRUST_D, 1.05)] * w
    return g


def crumb(w, h, face, rng):                  # cut face: soft crumb inside a crust rim
    g = [[mul(CRUMB, 1 + rng.uniform(-.04, .04)) for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1): g[y][x] = CRUST if y else CRUST_L
            elif rng.random() < .16: g[y][x] = CRUMB_D
    return g


def charred(base, spots=.18):
    def paint(w, h, face, rng):
        g = [[mul(base, 1 + rng.uniform(-.07, .07)) for _ in range(w)] for _ in range(h)]
        for y in range(h):
            for x in range(w):
                if rng.random() < spots: g[y][x] = mul(base, .55)
        return g
    return paint


def ringed(edge, core):                      # carrot coin / courgette round seen from the cut side
    def paint(w, h, face, rng):
        if face not in ('up', 'down') and min(w, h) < 2: return [[edge] * w for _ in range(h)]
        g = [[edge] * w for _ in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1): g[y][x] = core
        return g
    return paint


IRON, IRON_D, IRON_L = (64, 66, 72), (38, 39, 44), (104, 108, 116)


def pan_floor(w, h, face, rng):              # seasoned cast iron with an oil sheen
    g = [[mul(IRON, 1 + rng.uniform(-.06, .06)) for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if rng.random() < .10: g[y][x] = (150, 112, 46)
            elif rng.random() < .05: g[y][x] = (196, 156, 70)
    return g



# Hammer-style ramps: 5 tones, highlight top-left, darkest bottom-right, tops a step lighter, bottoms darker.
R_IRON = [(214, 210, 202), (176, 171, 162), (138, 133, 126), (101, 97, 92), (72, 69, 66)]
R_CAST = [(122, 124, 132), (92, 94, 102), (68, 70, 78), (50, 51, 58), (34, 35, 40)]
R_WOOD = [(184, 142, 88), (152, 114, 66), (116, 86, 48), (92, 61, 36), (68, 45, 27)]
R_DARKWOOD = [(124, 82, 50), (98, 62, 38), (78, 48, 30), (60, 36, 22), (44, 26, 16)]
R_BRASS = [(250, 226, 140), (226, 190, 92), (190, 148, 60), (150, 110, 40), (110, 78, 28)]


def ramp(pal, shift=0):
    def paint(w, h, face, rng):
        sh = shift + (-1 if face == 'up' else 1 if face == 'down' else 0)
        g = []
        for y in range(h):
            row = []
            for x in range(w):
                t = ((x / (w - 1) if w > 1 else .5) + (y / (h - 1) if h > 1 else .5)) / 2
                i = 1 + round(t * 2) + sh
                if face not in ('up', 'down'):
                    if y == 0 and h > 1: i -= 1
                    if y == h - 1 and h > 2: i += 1
                row.append(pal[max(0, min(4, i))])
            g.append(row)
        return g
    return paint


def sprite(rows, pal):
    """Fixed pixel art, tiled/cropped to the face size."""
    def paint(w, h, face, rng):
        return [[pal[rows[y % len(rows)][x % len(rows[0])]] for x in range(w)] for y in range(h)]
    return paint


def knife_grip(w, h, face, rng):          # wood ramp with two brass rivets on the flat sides
    g = ramp(R_DARKWOOD)(w, h, face, rng)
    if face in ('west', 'east') and w >= 4 and h >= 2:
        for x in (1, w - 2): g[0 if h == 1 else h // 2 - 1 if h > 2 else 0][x] = R_BRASS[1]
    return g


def blade(w, h, face, rng):               # polished blade: bright edge row at the bottom, darker spine on top
    if face in ('west', 'east'):
        g = [[R_IRON[1] for _ in range(w)] for _ in range(h)]
        g[0] = [R_IRON[3]] * w
        g[-1] = [R_IRON[0]] * w
        for x in range(0, w, 2): g[-1][x] = (236, 240, 244)       # serrations catch the light
        return g
    return ramp(R_IRON, 1)(w, h, face, rng)


PINE = {'o': (110, 62, 22), 'd': (164, 96, 30), 'm': (206, 136, 44), 'l': (240, 186, 76), 'h': (255, 226, 140),
        'c': (78, 44, 18), 'y': (250, 226, 120), 'Y': (236, 196, 84), 'k': (214, 160, 60)}
PINE_SKIN = ["mlhl", "dmlm", "omdm", "cdmd"]            # one diamond scale; tiled, offset each row pair
def pine_skin(w, h, face, rng):
    g = []
    for y in range(h):
        row = []
        for x in range(w):
            r = PINE_SKIN[y % 4][(x + (2 if (y // 4) % 2 else 0)) % 4]
            row.append(PINE[r])
        g.append(row)
    for _ in range(max(1, w * h // 12)):               # caramelised spots
        g[rng.randrange(h)][rng.randrange(w)] = PINE['c']
    return g


def pine_end(w, h, face, rng):                          # cut end: skin ring, yellow flesh, paler core
    g = [[PINE['d']] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1): g[y][x] = PINE['Y']
    for y in range(2, h - 2):
        for x in range(2, w - 2): g[y][x] = PINE['y']
    return g


LEAF = [(98, 150, 60), (70, 122, 44), (48, 92, 34), (34, 66, 26), (24, 48, 20)]


def veg(rows, pal):
    return sprite(rows, pal)


VPAL = {'O': (236, 120, 30), 'o': (252, 168, 70), 'R': (204, 44, 36), 'r': (240, 96, 80), 'G': (60, 128, 46),
        'g': (226, 222, 160), 'B': (150, 104, 66), 'b': (226, 204, 168), 'T': (92, 156, 54), 't': (60, 116, 40),
        'Y': (240, 196, 52), 'y': (255, 232, 120), 'P': (124, 54, 120), 'p': (196, 120, 190)}

R_CRUST = [(244, 196, 116), (218, 154, 76), (190, 120, 54), (152, 90, 38), (112, 62, 28)]
R_SOUP = [(248, 150, 70), (230, 112, 46), (204, 86, 36), (170, 62, 30), (130, 44, 24)]


def crust_scored(w, h, face, rng):
    g = ramp(R_CRUST)(w, h, face, rng)
    for y in range(h):
        for x in range(w):
            if (x + y) % 3 == 0 and 0 < x < w - 1: g[y][x] = R_CRUST[3]
    return g


def crumb2(w, h, face, rng):
    g = [[(246, 226, 178)] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1): g[y][x] = R_CRUST[2] if y else R_CRUST[1]
            elif (x * 3 + y * 5) % 7 == 0: g[y][x] = (222, 196, 140)
    return g


BLADE = ["..MMMMMM", ".LLLLLLL", "HhHhHhHh"]
BPAL = {'M': R_IRON[3], 'L': R_IRON[1], 'H': (236, 240, 244), 'h': R_IRON[0], '.': None}
def blade2d(w, h, face, rng):              # u runs +z on the west face, -z on the east face; tip at low z
    rows = [r if face == 'west' else r[::-1] for r in BLADE]
    return [[BPAL[rows[y][x]] for x in range(w)] for y in range(h)]


def soup_surface(variant):
    """Translucent broth: the veg below shows through. Bubbles drift with the stirring."""
    def paint(w, h, face, rng):
        r = random.Random(variant * 7 + 1)
        g = [[(232, 146, 62, 140) if (x + y + variant) % 5 else (246, 176, 90, 150) for x in range(w)] for y in range(h)]
        for _ in range(3):
            x, y = r.randrange(1, w - 1), r.randrange(1, h - 1)
            g[y][x] = (255, 214, 150, 230); g[y][x - 1] = (250, 190, 110, 200)
        return g
    return paint

MAT = {
    'board': wood((178, 128, 76), (132, 88, 48)),
    'board_edge': solid((150, 104, 60), .05),
    'crust_top': crust_top, 'crust': crust_side, 'crumb': crumb,
    'blade': blade, 'grip': knife_grip, 'bolster': ramp(R_BRASS),
    'cast': ramp(R_CAST), 'cast_rim': ramp(R_CAST, -1), 'pan_grip': ramp(R_WOOD),
    'v_carrot': veg(["OO", "Oo"], VPAL), 'v_pepper': veg(["Rr", "RR"], VPAL), 'v_courgette': veg(["Gg", "gG"], VPAL),
    'v_mushroom': veg(["bB", "BB"], VPAL), 'v_broccoli': veg(["Tt", "tT"], VPAL), 'v_yellow': veg(["Yy", "YY"], VPAL),
    'crust2': ramp(R_CRUST), 'crust_top2': crust_scored, 'crumb2': crumb2, 'blade2d': blade2d,
    'board2': ramp(R_WOOD), 'soup0': soup_surface(0), 'soup1': soup_surface(1), 'soup2': soup_surface(2), 'soup3': soup_surface(3),
    'pine_skin': pine_skin, 'pine_end': pine_end, 'leaf': ramp(LEAF), 'leaf_dark': ramp(LEAF, 1),
    'wheel': ramp(R_IRON, 1), 'glaze': sprite(["h"], PINE), 'glaze_d': sprite(["k"], PINE),
    'crumbs': solid((214, 166, 98), .1, rim=False),
    'sparkle': solid((255, 246, 190), 0, rim=False),
    'iron': solid(IRON, .06), 'iron_rim': solid(IRON_L, .05, rim=False), 'pan_floor': pan_floor,
    'pan_handle': wood((120, 74, 40), (82, 48, 26)),
    'carrot': ringed((232, 116, 30), (250, 160, 64)), 'courgette': ringed((54, 120, 46), (226, 222, 160)),
    'red_pepper': solid((206, 46, 38), .06), 'yellow_pepper': solid((242, 196, 52), .06),
    'mushroom': ringed((168, 124, 88), (230, 210, 176)), 'onion': solid((236, 222, 196), .05),
    'oil': solid((214, 172, 74), .05, rim=False),
    'rod': solid((92, 96, 104), .05, rim=False), 'bracket': solid((70, 72, 80), .06),
    'sk_mushroom': charred((176, 128, 86)), 'sk_red': charred((198, 52, 40)), 'sk_onion': charred((232, 214, 182), .22),
    'sk_courgette': charred((70, 134, 54)), 'sk_yellow': charred((238, 186, 50)), 'sk_tomato': charred((214, 60, 40), .12),
}


# ---------------------------------------------------------------- engine
class Prop:
    def __init__(self, name, ticks):
        self.name, self.ticks, self.els, self.planes = name, ticks, [], []

    def box(self, lo, hi, mat, vis=None, rot=None, glow=False, drop=(), seed=None, name=''):
        """mat: material name, or {face: name} with optional '*' default. vis: frames shown (None = all)."""
        self.els.append(dict(lo=lo, hi=hi, mat=mat, vis=vis, rot=rot, glow=glow, drop=set(drop),
                             seed=seed if seed is not None else len(self.els), name=name or f'e{len(self.els)}'))

    def plane(self, lo, hi, rot, w, h, frames_px, glow=False, name='plane'):
        """A two-sided vertical plane (z = const before rotation). frames_px: {frame: {(x, y): rgb}}."""
        self.planes.append(dict(lo=lo, hi=hi, rot=rot, w=w, h=h, px=frames_px, glow=glow, name=name))

    def build(self, display, credit):
        global FS
        for FS in (128, 256):
            try: return self._build(display, credit)
            except AssertionError: continue
        raise AssertionError(f'{self.name}: atlas full at 256')

    def _build(self, display, credit):
        nf = len(self.ticks)
        img = Image.new('RGBA', (FS, FS * nf), (0, 0, 0, 0))
        cx = cy = shelf = 0                                     # shelf packer, 1 px gutter

        def alloc(w, h):
            nonlocal cx, cy, shelf
            if cx + w > FS: cx, cy, shelf = 0, cy + shelf + 1, 0
            r = (cx, cy); cx += w + 1; shelf = max(shelf, h)
            assert cy + h <= FS, f'{self.name}: atlas full'
            return r

        k = 16 / FS
        elements = []
        for e in self.els:
            (x1, y1, z1), (x2, y2, z2) = e['lo'], e['hi']
            size = {'north': (x2 - x1, y2 - y1), 'south': (x2 - x1, y2 - y1), 'west': (z2 - z1, y2 - y1),
                    'east': (z2 - z1, y2 - y1), 'up': (x2 - x1, z2 - z1), 'down': (x2 - x1, z2 - z1)}
            faces = {}
            for f in FACES:
                if f in e['drop']: continue
                w, h = (max(1, round(s)) for s in size[f])
                ox, oy = alloc(w, h)
                m = e['mat'].get(f, e['mat'].get('*')) if isinstance(e['mat'], dict) else e['mat']
                grid = MAT[m](w, h, f, random.Random(zlib.crc32(f"{self.name}|{e['seed']}|{f}".encode())))
                for fr in range(nf):
                    if e['vis'] is not None and fr not in e['vis']: continue
                    for y in range(h):
                        for x in range(w):
                            if grid[y][x] is not None: img.putpixel((ox + x, oy + y + fr * FS), tuple(grid[y][x]) + (() if len(grid[y][x]) == 4 else (255,)))
                faces[f] = {"uv": [ox * k, oy * k, (ox + w) * k, (oy + h) * k], "texture": "#0"}
            el = {"name": e['name'], "from": list(e['lo']), "to": list(e['hi']), "faces": faces}
            if e['rot']: el["rotation"] = e['rot']
            if e['glow']: el.update({"light_emission": 15, "shade": False})
            elements.append(el)
        for p in self.planes:
            ox, oy = alloc(p['w'], p['h'])
            for fr, pix in p['px'].items():
                for (x, y), c in pix.items():
                    if 0 <= x < p['w'] and 0 <= y < p['h']: img.putpixel((ox + x, oy + y + fr * FS), c + (255,))
            u1, v1, u2, v2 = ox * k, oy * k, (ox + p['w']) * k, (oy + p['h']) * k
            el = {"name": p['name'], "from": list(p['lo']), "to": list(p['hi']), "shade": False, "rotation": p['rot'],
                  "faces": {"south": {"uv": [u1, v1, u2, v2], "texture": "#0"}, "north": {"uv": [u2, v1, u1, v2], "texture": "#0"}}}
            if p['glow']: el["light_emission"] = 15
            elements.append(el)
        tid = f"realm:item/decorations/{self.name}"
        model = {"credit": credit, "texture_size": [FS, FS], "textures": {"0": tid, "particle": tid},
                 "elements": elements, "display": display}
        meta = {"animation": {"interpolate": False, "width": FS, "height": FS,
                              "frames": [{"index": i, "time": t} for i, t in enumerate(self.ticks)]}}
        return model, img, meta


TOP_FIXED = {"rotation": [-90, 180, 0], "translation": [0, 0, 0], "scale": [2, 2, 2]}
WALL_FIXED = {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [2, 2, 2]}


def hand_views(gui_t, gui_s):
    return {"gui": {"rotation": [30, 225, 0], "translation": gui_t, "scale": [gui_s] * 3},
            "ground": {"translation": [0, -2, 0], "scale": [.45] * 3},
            "thirdperson_righthand": {"rotation": [0, -30, 0], "translation": [0, -4, 0], "scale": [.45] * 3},
            "firstperson_righthand": {"rotation": [0, -30, 0], "translation": [0, -4, 0], "scale": [.45] * 3}}


# ---------------------------------------------------------------- bread board
def bread():
    # a floating bread knife saws a slice off a bloomer, the slice tips onto the pile, fades, and the loaf end
    # grows back with a twinkle (the magic loaf never runs out).
    # knife pose = (blade bottom y, saw offset dz). Half-pixel steps so it glides instead of jumping.
    # 1 px strokes, 3 ticks each: a little choppy, as if really sawing
    SAW = [(14, 0), (13, -1), (12.5, 0), (12, 1), (11, 0), (10.5, -1), (10, 0), (9, 1), (9, 0)]
    F = [((14, 0), 'up', 10)] + [(p, 'up', 3) for p in SAW[1:]] + \
        [((9, 0), 't1', 2), ((9, 0), 't2', 2), ((10.5, 0), 'flat', 2), ((12, 0), 'flat', 2), ((13.5, 0), 'flat', 2),
         ((14, 0), 'flat', 8), ((14, 0), 'twinkle', 4)]
    P = Prop('kitchen_bread_cutting', [t for *_, t in F])
    fr = lambda pred: {i for i, f in enumerate(F) if pred(f)}
    P.box((2, 8, 4), (14, 9, 12), {'*': 'board_edge', 'up': 'board'}, drop=('down',), name='board')
    P.box((14, 8, 6.5), (15.5, 8.9, 9.5), {'*': 'board_edge', 'up': 'board'}, drop=('down',), name='board_tab')
    P.box((3, 9, 5.5), (10, 12, 10.5), {'*': 'crust', 'east': 'crumb'}, drop=('down',), name='loaf')
    P.box((3.5, 12, 6), (10, 12.75, 10), {'*': 'crust', 'up': 'crust_top', 'east': 'crust'}, drop=('down',), name='loaf_top')
    P.box((2.5, 9, 6), (3, 11.5, 10), 'crust', drop=('down',), name='loaf_heel')
    sl = {'*': 'crust', 'west': 'crumb', 'east': 'crumb'}
    up = fr(lambda f: f[1] in ('up', 'twinkle'))
    P.box((10, 9, 5.5), (10.75, 12, 10.5), sl, vis=up, drop=('down',), name='slice_on_loaf')
    P.box((10, 12, 6), (10.75, 12.75, 10), 'crust', vis=up, drop=('down',), name='slice_on_loaf_top')
    for st, ang in (('t1', -22.5), ('t2', -45)):
        P.box((10, 9, 5.5), (10.75, 12.6, 10.5), sl, vis=fr(lambda f: f[1] == st), drop=('down',),
              rot={"angle": ang, "axis": "z", "origin": [10.75, 9, 8]}, name=f'slice_{st}')
    flat = {'*': 'crust', 'up': 'crumb', 'down': 'crumb'}
    P.box((11, 9, 5.6), (14, 9.75, 10.4), flat, drop=('down',), name='pile_slice')
    P.box((10.9, 9.75, 5.5), (13.6, 10.5, 10.5), flat, vis=fr(lambda f: f[1] == 'flat'), drop=('down',), name='slice_flat')
    for x, z in ((4, 11.2), (12.6, 4.6), (6.5, 4.7)):
        P.box((x, 9, z), (x + .5, 9.3, z + .5), 'crumbs', drop=('down',), name='crumb')
    # knife: flat two-sided blade sprite in the cut plane (inside the end slice, so it can't clip); brass
    # bolster and a chunky 2x2 grip like the anvil hammer
    for n, p in enumerate(dict.fromkeys(f[0] for f in F)):
        y, dz = p
        v = fr(lambda f: f[0] == p)
        P.box((10.05, y, 3 + dz), (10.05, y + 3, 11 + dz), 'blade2d', vis=v, drop=('north', 'south', 'up', 'down'),
              name=f'knife_blade_{n}')
        P.box((9.05, y + 1, 11 + dz), (11.05, y + 3, 12 + dz), 'bolster', vis=v, name=f'knife_bolster_{n}')
        P.box((9.05, y + 1, 12 + dz), (11.05, y + 3, 16 + dz), 'grip', vis=v, name=f'knife_grip_{n}')
    tw = fr(lambda f: f[1] == 'twinkle')
    P.plane((8, 9, 8), (14, 15, 8), {"angle": 45, "axis": "y", "origin": [10.4, 12, 8]}, 6, 6,
            {i: {(2, 1): (255, 250, 200), (3, 2): (255, 236, 150), (1, 2): (255, 236, 150), (2, 3): (255, 250, 200),
                 (2, 2): (255, 255, 240), (4, 4): (255, 230, 150)} for i in tw}, glow=True, name='twinkle')
    return P.build({"fixed": TOP_FIXED, **hand_views([0, -3, 0], 1.0)},
                   "Realms Beyond - bread board (tools/kitchen-props/gen_kitchen.py)")


# ---------------------------------------------------------------- vegetable pan
STEAM = [(244, 247, 250), (222, 228, 234), (196, 204, 213), (172, 181, 192)]


def wisps(nf, births, w, h, rng):
    out = {f: {} for f in range(nf)}
    for born in births:
        x0 = w / 2 + rng.uniform(-w / 2 + 2, w / 2 - 2)
        rise, drift, life = rng.uniform(1.6, 2.6), rng.uniform(-.5, .5), rng.choice([3, 4])
        for age in range(life):
            f = (born + age) % nf
            x, y = x0 + drift * age, h - 1 - rise * age
            dots = [(0, 0), (1, 0)] if age == 0 else [(0, 0)]
            for dx, dy in dots:
                out[f][(int(x) + dx, int(y) + dy)] = STEAM[min(3, age + (dx + dy) % 2)]
    return out


def pan():
    # Sizzle, shake the pan forward-back-forward, flick it up from the handle tip (so it never dips into the
    # block below), veg flies and tumbles, the pan rises to catch it, then settles. Janky on purpose.
    # frame: (pan pose, veg pose, ticks)
    # slowed for a floaty, magical feel: the veg hangs at the top of the toss
    F = [('rest', 'rest', 10), ('rest', 'rest', 8), ('fwd', 'fwd', 4), ('back', 'back', 4), ('fwd', 'fwd', 4),
         ('tilt', 'up1', 4), ('lift', 'top', 9), ('rest', 'fall', 4), ('lift', 'land', 4), ('rest', 'rest', 8)]
    P = Prop('kitchen_vegetable_pan', [t for *_, t in F])
    nf = len(F)
    pf = lambda p: {i for i, f in enumerate(F) if f[0] == p}
    vf = lambda p: {i for i, f in enumerate(F) if f[1] == p}
    # pan poses: (dx, dy, rotation). Tilt pivots on the end of the handle, so every point goes up.
    PAN = {'rest': (0, 0, None), 'fwd': (-1, 0, None), 'back': (1, 0, None), 'lift': (0, 1, None),
           'tilt': (0, 1, {"angle": -22.5, "axis": "z", "origin": [19, 10.5, 8]})}
    for name, (dx, dy, rot) in PAN.items():
        vis = pf(name)
        if not vis: continue
        dr = ('down',) if (dy == 0 and rot is None) else ()
        def b(lo, hi, m, n, drop=dr):
            P.box((lo[0] + dx, lo[1] + dy, lo[2]), (hi[0] + dx, hi[1] + dy, hi[2]), m, vis=vis, rot=rot, drop=drop, name=f'{n}_{name}')
        b((3, 8, 3), (13, 9, 13), {'*': 'cast', 'up': 'pan_floor'}, 'floor')
        for lo, hi in (((3, 9, 3), (13, 11, 4)), ((3, 9, 12), (13, 11, 13)), ((3, 9, 4), (4, 11, 12)), ((12, 9, 4), (13, 11, 12))):
            b(lo, hi, {'*': 'cast', 'up': 'cast_rim'}, 'wall', drop=())
        b((13, 9, 7), (15, 10, 9), 'cast', 'handle_neck', drop=())
        b((15, 9, 7), (19, 10, 9), 'pan_grip', 'handle_grip', drop=())
    VEG = [('v_carrot', 4, 4, 4, 'x'), ('v_pepper', 7, 4, 5, 'z'), ('v_courgette', 10, 5, 3, 'y'),
           ('v_mushroom', 4, 8, 5, 'z'), ('v_broccoli', 7, 7, 4, 'x'), ('v_carrot', 10, 9, 5, 'z'),
           ('v_yellow', 6, 10, 3, 'y'), ('v_pepper', 9, 7, 3, 'x')]
    for n, (m, x, z, top, ax) in enumerate(VEG):
        h = 2 if m == 'v_broccoli' else 1
        s_ = -1 if n % 2 else 1
        # veg pose: (dx, dy, dz, angle)
        poses = {'rest': (0, 0, 0, 0), 'fwd': (-1, 0, 0, 0), 'back': (1, 0, 0, 0),
                 'up1': (0, top // 2 + 3, 0, 22.5 * s_), 'top': (s_, top + 2, -s_, 45 if n % 2 else -22.5),
                 'fall': (0, top, s_, -22.5 * s_), 'land': (0, 1, 0, 0)}
        for p, (dx, dy, dz, ang) in poses.items():
            lo, hi = (x + dx, 9 + dy, z + dz), (x + dx + 2, 9 + dy + h, z + dz + 2)
            rot = {"angle": ang, "axis": ax, "origin": [x + dx + 1, 9 + dy + h / 2, z + dz + 1]} if ang else None
            P.box(lo, hi, m, vis=vf(p), rot=rot, drop=('down',) if p in ('rest', 'fwd', 'back', 'land') else (),
                  seed=n, name=f'{m}_{n}_{p}')
    for i, ang in enumerate((45, -45)):
        P.plane((2, 10.5, 8), (14, 20.5, 8), {"angle": ang, "axis": "y", "origin": [8, 8, 8]}, 12, 10,
                wisps(nf, [0, 1, 3, 9], 12, 10, random.Random(11 + i)), name=f'steam_{i}')
    # Low flames and embers on either side of the pan, just above the smoker.
    heat = {}
    for f in range(nf):
        pix = {}
        for x in range(12):
            height = 1 + ((x * 7 + f * 3) % 3)
            for y in range(4 - height, 4):
                pix[x, y] = (255, 215, 83) if y >= 3 else (255, 133, 28) if y >= 2 else (236, 72, 18)
        for x in ((f * 3) % 12, (f * 3 + 5) % 12): pix[x, 0] = (255, 185, 52)
        heat[f] = pix
    for i, z in enumerate((3.4, 12.6)):
        P.plane((2.7, 7.6, z), (13.3, 9.6, z), {"angle": 0, "axis": "y", "origin": [8, 8, 8]},
                12, 4, heat, glow=True, name=f'heat_flames_{i}')
    return P.build({"fixed": TOP_FIXED, **hand_views([0, -3, 0], 1.0)},
                   "Realms Beyond - vegetable pan (tools/kitchen-props/gen_kitchen.py)")


# ---------------------------------------------------------------- soup pot (item id kitchen_rotating_spit)
def spit():
    # A cast-iron pot of vegetable soup hanging from an iron bar over the campfire; a wooden ladle stirs it
    # round by itself, bits of veg drift, bubbles pop and steam rises. Same whole-pixel style as the pan.
    # The pot hangs tilted towards the viewer so the broth and the stirring show.
    nf = 24
    P = Prop('kitchen_rotating_spit', [3] * nf)
    Z = 16                                                     # centre of the fireplace slot
    P.box((-1, 11, Z - .5), (17, 12, Z + .5), 'wheel', name='bar')
    for x in (0, 15):
        P.box((x, 10, Z - 1), (x + 1, 13, Z + 1), 'cast', name='collar')
    # Follow the bail's tilted top centre; return to the fixed overhead bar.
    import math
    hook_z = Z + 3.5 * math.sin(math.radians(22.5))
    P.box((7.5, 8.1, hook_z), (8.5, 11.7, hook_z), 'cast', name='hook',
          rot={"angle": -22.5, "axis": "x", "origin": [8, 8.1, hook_z]},
          drop=('east', 'west', 'up', 'down'))
    BITS = [('v_carrot', 2.2, 0), ('v_broccoli', 2.4, 90), ('v_pepper', 1.6, 180), ('v_courgette', 2.6, 270),
            ('v_mushroom', 0.8, 45), ('v_yellow', 1.4, 300)]
    POS = [(0, -2.5), (2.5, 0), (0, 2.5), (-2.5, 0)]
    import math as _m
    # the hanging parts tilt 22.5 deg about x so the rim dips towards the viewer and the broth shows;
    # pivot low enough that the back of the pot stays out of the wall (z > 8)
    for tag, ang in (('tilt', 22.5),):
        frames = set(range(nf))
        rot = {"angle": ang, "axis": "x", "origin": [8, 5, Z]} if ang else None
        stir = lambda k: {f for f in frames if (f % 8) // 2 == k}
        def b(lo, hi, m, name, vis=frames, **kw):
            P.box(lo, hi, m, vis=vis, rot=rot, name=f'{name}_{tag}', **kw)
        b((2, 4, Z - .5), (3, 9, Z + .5), 'cast', 'bail_l')
        b((13, 4, Z - .5), (14, 9, Z + .5), 'cast', 'bail_r')
        b((3, 8, Z - .5), (13, 9, Z + .5), 'cast', 'bail_top')
        b((3, -2, Z - 5), (13, -1, Z + 5), 'cast', 'pot_floor')
        for lo, hi in (((3, -1, Z - 5), (13, 5, Z - 4)), ((3, -1, Z + 4), (13, 5, Z + 5)),
                       ((3, -1, Z - 4), (4, 5, Z + 4)), ((12, -1, Z - 4), (13, 5, Z + 4))):
            b(lo, hi, {'*': 'cast', 'up': 'cast_rim'}, 'pot_wall')
        for v in range(4):
            b((4, 3, Z - 4), (12, 4, Z + 4), f'soup{v}', f'soup_{v}', vis={f for f in frames if f % 4 == v},
              drop=('north', 'south', 'west', 'east', 'down'))
        for i, (dx, dz) in enumerate(POS):
            cx, cz = 8 + dx, Z + dz
            b((cx - .5, 2, cz - .5), (cx + .5, 8, cz + .5), 'pan_grip', f'ladle_{i}', vis=stir(i))
            b((cx - 1, 1.2, cz - 1), (cx + 1, 2.2, cz + 1), 'board2', f'ladle_bowl_{i}', vis=stir(i))
        for n, (m, r, a0) in enumerate(BITS):
            for k in range(4):
                a_ = _m.radians(a0 + 90 * k)
                x, z = 8 + r * _m.cos(a_) - .5, Z + r * _m.sin(a_) - .5
                b((x, 1.6, z), (x + 1, 2.6, z + 1), m, f'bit_{n}_{k}', vis=stir(k), seed=n)
    for i, ang in enumerate((45, -45)):
        P.plane((2, 4.5, Z), (14, 14.5, Z), {"angle": ang, "axis": "y", "origin": [8, 8, Z]}, 12, 10,
                wisps(nf, [0, 2, 3, 5, 6, 8, 10, 11, 13, 14, 16, 18, 19, 21, 22], 12, 10, random.Random(21 + i)),
                name=f'steam_{i}')
    return P.build({"fixed": WALL_FIXED,
                    "gui": {"rotation": [25, 160, 0], "translation": [0, 1, -6], "scale": [1, 1, 1]},
                    "ground": {"translation": [0, 0, -4], "scale": [.45] * 3},
                    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 0, -4], "scale": [.45] * 3},
                    "firstperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 0, -4], "scale": [.45] * 3}},
                   "Realms Beyond - soup pot over the fire (tools/kitchen-props/gen_kitchen.py)")


def main(root):
    a = os.path.join(root, 'assets', 'realm')
    for make in (bread, pan, spit):
        model, img, meta = make()
        name = model['textures']['0'].split('/')[-1]
        tex = os.path.join(a, 'textures', 'item', 'decorations', name + '.png')
        mdl = os.path.join(a, 'models', 'item', 'decorations', name + '.json')
        item = os.path.join(a, 'items', 'decorations', name + '.json')
        for p in (tex, mdl, item): os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(tex)
        json.dump(meta, open(tex + '.mcmeta', 'w'), indent=2)
        json.dump(model, open(mdl, 'w'), indent=1)
        json.dump({"model": {"type": "minecraft:model", "model": f"realm:item/decorations/{name}"}}, open(item, 'w'), indent=2)
        print(f'{name}: {len(model["elements"])} elements, {len(meta["animation"]["frames"])} frames, '
              f'{sum(f["time"] for f in meta["animation"]["frames"])} ticks')


if __name__ == '__main__':
    main(sys.argv[1])
