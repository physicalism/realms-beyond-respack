#!/usr/bin/env python3
"""Lucky Ivy: a gold seated Ivy on a red tasselled cushion, waving one paw like a lucky cat.

Hand-sculpted cuboids on a 0.25-unit grid (16 units = 1 block, about 7/8 block tall),
painted in the same flat OR/Mojang style as the Ivy shrine: a flat tone per face,
a light top band, a dark bottom band and sparse one-unit speckle.

The waving paw has three poses (raised, halfway, resting). They share one animated
texture whose frames are opaque only on the current pose's faces, so the paw moves
every game tick without swapping models. Two static variants hold a single pose.

Usage: python3 lucky_ivy.py [outdir] [gold|coloured]
"""
import json, math, sys, io, itertools
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'export')
OUT.mkdir(parents=True, exist_ok=True)
D = 4                                   # texels per unit
FACES = ('north', 'south', 'west', 'east', 'up', 'down')
SHADE = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}
VARIANT = sys.argv[2] if len(sys.argv) > 2 else 'gold'          # 'gold' figurine or 'coloured' (Ivy's real black coat)
assert VARIANT in ('gold', 'coloured')
NAME = 'lucky_ivy' if VARIANT == 'gold' else 'lucky_ivy_coloured'
NS = 'realm:item/decorations/'

E = []
def box(name, a, b, part='fur', pose=None):
    q = lambda v: round(v * D) / D
    E.append(dict(name=name, frm=[q(v) for v in a], to=[q(v) for v in b], part=part, pose=pose))

# ---------------- cushion: red velvet with gold piping and gold corner tassels
box('cushion', (2.5, 0, 2.5), (13.5, 2.5, 13.5), 'cushion')
box('cushion top', (3.5, 2.5, 3.5), (12.5, 3, 12.5), 'cushion')
for cx in (2.5, 13.5):
    for cz in (2.5, 13.5):
        t = ('W' if cx < 8 else 'E') + ('N' if cz < 8 else 'S')
        box('tassel ' + t, (cx - 1, 0, cz - 1), (cx + 1, 1.75, cz + 1), 'gold')
        box('tassel cap ' + t, (cx - .75, 1.75, cz - .75), (cx + .75, 2.75, cz + .75), 'gold')

# ---------------- Ivy (faces -Z / north; sits on the cushion top at y = 3)
Y = 3
# slimmer and taller, like the shrine dog: x squeezed about the centre line, y stretched up from the cushion,
# and the head squeezed a little more on top of that
# Closer to the shrine's Ivy: narrower head carried higher on a longer neck, ears hanging lower
SX, SY, SXH = 0.92, 1.08, 0.9
NECK = 0.75                                      # head, collar and tag lifted by this much (design units)
HEAD = ('head', 'snout', 'ear')
LIFT = HEAD + ('collar', 'tag')
def dbox(name, a, b, part='fur', pose=None):
    sx = SX * (SXH if name.startswith(HEAD) else 1)
    dy = NECK if name.startswith(LIFT) else 0
    mx = lambda v: 8 + (v - 8) * sx
    my = lambda v: Y + (v + dy) * SY
    box(name, (mx(a[0]), my(a[1]), a[2]), (mx(b[0]), my(b[1]), b[2]), part, pose)
    E[-1].update(sx=sx, sy=SY, dy=dy)
dbox('hind paw L', (3.5, 0, 4.75), (5.5, 1.25, 7)); dbox('hind paw R', (10.5, 0, 4.75), (12.5, 1.25, 7))
dbox('haunch L', (3.75, 0, 7), (5.5, 3.75, 11.25)); dbox('haunch R', (10.5, 0, 7), (12.25, 3.75, 11.25))
dbox('haunch top L', (4, 3.75, 7.5), (5.5, 4.25, 10.75)); dbox('haunch top R', (10.5, 3.75, 7.5), (12, 4.25, 10.75))
dbox('body', (5.5, 0, 6), (10.5, 5, 11.5))
dbox('body back', (6, 0, 11.5), (10, 4, 12))
dbox('chest', (5.25, 2, 4.5), (10.75, 6.5, 7.5))
dbox('back', (5.5, 5, 7.5), (10.5, 6.75, 10))
dbox('front leg R', (8.75, 0, 3.75), (10.5, 3.75, 5.5)); dbox('front paw R', (8.5, 0, 2.75), (10.75, 1.25, 4.75))
dbox('neck', (5.75, 6.25, 4.75), (10.25, 8, 7.75))
dbox('collar', (5.25, 5.75, 4), (10.75, 7, 8.25), 'collar')
dbox('tag', (7.5, 5, 3.75), (8.5, 6, 4), 'tag')
dbox('head', (4.75, 7, 3.25), (11.25, 11.25, 8.5))
dbox('head top', (5.5, 11.25, 3.75), (10.5, 11.75, 8))
dbox('head back', (5.5, 7.5, 8.5), (10.5, 10.75, 9))
dbox('snout', (6.25, 7.25, 1.5), (9.75, 9.25, 3.25))
for t, lo, hi in (('L', 3.75, 4.75), ('R', 11.25, 12.25)):
    o = (lambda d: (lo + d, hi)) if t == 'L' else (lambda d: (lo, hi - d))
    dbox('ear ' + t, (lo, 6.75, 4), (hi, 10.75, 7.25), 'ear')
    dbox('ear top ' + t, (o(.25)[0], 10.75, 4.25), (o(.25)[1], 11.25, 7), 'ear')
    dbox('ear tip ' + t, (o(.25)[0], 6.25, 4.5), (o(.25)[1], 6.75, 6.75), 'ear')
# thick tail, like the shrine's: rises out of the rump, runs back over the seat and hangs over the cushion's back edge, curving round to her right
dbox('tail root', (8.75, 0.5, 11.5), (10.75, 2.75, 13))
dbox('tail', (9.25, -0.5, 12.75), (11.25, 1.25, 14.25))
dbox('tail hang', (10, -1.75, 13.5), (11.75, -0.5, 14.75))           # each segment steps out to her right,
dbox('tail tip', (11, -2.5, 13.25), (12.5, -1.75, 14.5))             # so the tail curves gently round as it hangs
dbox('tail curl', (12.25, -2.5, 12.75), (13.25, -2, 13.75))          # tip just turning forward

# waving paw (dog's left, viewer's right). Three keyframes (raised, halfway, resting) with two
# in-between poses on each swing, so 7 poses in all; boxes are interpolated and snapped to the 0.25 grid.
KEYS = [
    [('upper arm', (4, 4.75, 4.25), (5.75, 7.25, 5.75)), ('forearm', (2.5, 7, 3.25), (4.25, 9.75, 5.25)),   # raised level with her cheek
     ('paw', (1.75, 9.5, 2.75), (4.5, 11.75, 5.5))],
    [('upper arm', (4.25, 4, 3.75), (6, 5.5, 5.5)), ('forearm', (3.25, 5.5, 3), (4.75, 7.25, 4.75)),
     ('paw', (2.75, 6.75, 2.25), (5.25, 8.75, 4.5))],
    [('upper arm', (5.75, 2.5, 4.75), (7, 3.5, 5.5)), ('forearm', (5.5, 0, 3.75), (7.25, 3.75, 5.5)),   # upper arm tucks into the chest
     ('paw', (5.25, 0, 2.75), (7.5, 1.25, 4.75))],
]
TWEENS = 2
POSES = {}
for s_ in range(len(KEYS) - 1):
    for t_ in range(TWEENS + 1):
        u = t_ / (TWEENS + 1)
        POSES[len(POSES)] = [(nm, tuple(a0 + (a1 - a0) * u for a0, a1 in zip(A0, A1)), tuple(b0 + (b1 - b0) * u for b0, b1 in zip(B0, B1)))
                             for (nm, A0, B0), (_, A1, B1) in zip(KEYS[s_], KEYS[s_ + 1])]
POSES[len(POSES)] = KEYS[-1]
REST = len(POSES) - 1
NUDGE = {}                                                       # (pose, part) -> replacement box, filled in after the audit
for k, parts in POSES.items():
    for nm, a, b in parts:
        a, b = NUDGE.get((k, nm), (a, b))
        floor = k > REST // 2                                     # lower half of the swing: paw reads as a standing paw
        dbox(f'wave {"front " + nm if floor and nm == "paw" else nm} {k}', a, b, 'fur', k)

# in-between arm poses can land flush with the body: pull the arm's touching face in by one grid step
def coplanar(E_):
    AX = {'north': (2, -1), 'south': (2, 1), 'west': (0, -1), 'east': (0, 1), 'down': (1, -1), 'up': (1, 1)}
    for a_, b_ in itertools.combinations(E_, 2):
        if a_['pose'] is not None and b_['pose'] is not None and a_['pose'] != b_['pose']: continue
        for f in AX:
            ax, sg = AX[f]
            ca = a_['to'][ax] if sg > 0 else a_['frm'][ax]; cb = b_['to'][ax] if sg > 0 else b_['frm'][ax]
            if ca != cb or (f == 'down' and ca in (0, Y)): continue
            if all(min(a_['to'][q], b_['to'][q]) - max(a_['frm'][q], b_['frm'][q]) > 0 for q in range(3) if q != ax):
                yield a_, b_, f, ax, sg
for _ in range(50):
    hit = next(coplanar(E), None)
    if hit is None: break
    a_, b_, f, ax, sg = hit
    m = b_ if b_['pose'] is not None and (a_['pose'] is None or 'paw' in a_['name']) else a_
    if sg > 0: m['to'][ax] -= 1 / D
    else: m['frm'][ax] += 1 / D

# ---------------- painting
GOLDF = [(118, 70, 16), (156, 100, 24), (194, 136, 32), (222, 168, 46), (240, 196, 76), (252, 224, 130)]   # gold figurine
METAL = [(128, 84, 26), (176, 124, 40), (212, 160, 60), (236, 190, 88), (250, 220, 140)]                 # tassels and tag
EMER = [(16, 62, 40), (26, 94, 58), (38, 128, 78), (62, 166, 100)]
RED = [(66, 12, 20), (96, 20, 30), (128, 28, 38), (154, 40, 48), (180, 60, 64)]
EYE, EYE2, SHINE, NOSE = (34, 20, 12), (60, 36, 20), (255, 244, 214), (46, 26, 14)
EYEBLK = (14, 10, 11)                                           # the shrine's black
if VARIANT == 'coloured':                                       # black Labrador: the shrine's fur tones, brown eyes, near-black nose
    GOLDF = [(12, 10, 12), (17, 15, 17), (27, 24, 27), (40, 36, 40), (54, 49, 55), (70, 65, 72)]   # one step darker, as on the shrine
    EYE, EYE2, NOSE = (78, 46, 22), (112, 70, 34), (10, 8, 9)       # brown eyes

def Hs(*a):
    h = 2166136261
    for v in a: h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xffffffff; return h ^ (h >> 15)
def dims(e): return [b - a for a, b in zip(e['frm'], e['to'])]
def face_size(e, f):
    dx, dy, dz = dims(e)
    w, h = {'north': (dx, dy), 'south': (dx, dy), 'west': (dz, dy), 'east': (dz, dy), 'up': (dx, dz), 'down': (dx, dz)}[f]
    return int(round(w * D)), int(round(h * D))
def texel_pos(e, f, i, j):
    fx, fy, fz = e['frm']; tx, ty, tz = e['to']; c = .5 / D; i /= D; j /= D
    return {'north': (tx - i - c, ty - j - c, fz), 'south': (fx + i + c, ty - j - c, tz),
            'west': (fx, ty - j - c, fz + i + c), 'east': (tx, ty - j - c, tz - i - c),
            'up': (fx + i + c, ty, fz + j + c), 'down': (fx + i + c, fy, tz - j - c)}[f]

def paint(e, f, i, j, w, h):
    x, y, z = texel_pos(e, f, i, j); part, nm = e['part'], e['name']
    rx, ry = x, y
    if 'sx' in e: x, y = 8 + (x - 8) / e['sx'], Y + (y - Y) / e['sy'] - e['dy']        # back to design coordinates
    side = f in ('north', 'south', 'west', 'east')
    tall = side and h >= 2 * D
    top_row, bot_row = tall and j < D // 2 + 1, tall and j >= h - D // 2
    t = {'up': 4, 'down': 1}.get(f, 3)
    if top_row: t += 1
    elif bot_row: t -= 1
    n = Hs(math.floor(abs(x - 8)), math.floor(y), math.floor(z), FACES.index(f) // 2, 7) % 13
    if part in ('fur', 'ear'):
        if part == 'ear': t -= 1
        if n == 0: t += 1
        elif n == 1: t -= 1
        if 'paw' in nm:
            # toe grooves: two dark lines on the front of every paw
            if f == 'north':
                xs = (e['to'][0] - e['frm'][0]) / 3
                if any(abs(rx - (e['frm'][0] + k * xs)) < .13 for k in (1, 2)) and (j >= h // 2 if 'wave paw' not in nm else j < h // 2 + 1):
                    return GOLDF[1]
            if 'wave paw' in nm and f == 'north' and h // 2 + 1 <= j and abs(rx - (e['frm'][0] + e['to'][0]) / 2) < .75:
                return GOLDF[2]                                         # palm pad on the raised paw
        if nm == 'snout':
            if f == 'north':
                if abs(x - 8) < .75 and y >= Y + 8.5: return NOSE                # nose block at the top front
                r, c = h - 1 - j, i - w // 2                                       # texel row from the bottom, column from centre
                if r == 1 and -3 <= c < 3: return GOLDF[1]                          # subtle closed smile, one texel thick...
                if r == 2 and c in (-4, 3): return GOLDF[1]                         # ...one pixel raised at each corner
                t = 4
            if f == 'up':
                if abs(x - 8) < .75 and z < Y * 0 + 2.25: return NOSE
                t = 5
        if nm == 'head' and f == 'north':
            # eyes: exact 4 x 4-texel black squares, placed in real (texel) space so scaling can't stretch them;
            # one sparkle in the same top corner of both (top-left as you face her), so the light reads as one-sided
            top = round((Y + (10.5 + e['dy']) * e['sy'] - Y + Y) * D) / D
            for ex in (6.25, 9.75):
                cx = round((8 + (ex - 8) * e['sx']) * 2) / 2                  # eye centre on a texel edge
                if abs(rx - cx) < .5 and top - 1 <= ry < top:
                    ii = int((cx + .5 - rx) * D); jj = int((top - ry) * D)    # ii = 0 at the eye's left edge as you face her
                    if ii == 1 and jj == 1: return SHINE              # one texel in from the top-left corner, not on it
                    return EYEBLK
            if abs(x - 8) < 1.5 and y < Y + 7.5: t = 2                        # cheeks shade under the muzzle
        return GOLDF[max(0, min(5, t))]
    if part == 'collar':
        return EMER[max(0, min(3, t - 1 if side else 2))]
    if part == 'tag':
        return METAL[4] if (f == 'north' and j < 2) else METAL[3]
    if part == 'gold':
        if 'cap' in nm and f == 'up': return METAL[4]
        if side and bot_row: return METAL[1]
        return METAL[max(0, min(4, t + (1 if n == 0 else 0)))]
    if part == 'cushion':
        if side and nm == 'cushion':
            if j == 0: return METAL[3]                                     # gold piping round the top edge
            if j == 1: return METAL[1]
            if j >= h - 1: return RED[1]
            return RED[2 if n else 3]
        if f == 'up':
            if nm == 'cushion': return RED[3]
            d = max(abs(x - 8), abs(z - 8))
            if abs(d - 4.25) < .13 and Y > 0: return RED[2]               # tufted seam round the seat
            return RED[4 if n == 0 else 3]
        return RED[max(0, min(4, t - 1))]
    return GOLDF[2]

tex = {}
for ei, e in enumerate(E):
    for f in FACES:
        w, h = face_size(e, f)
        tex[(ei, f)] = np.array([[paint(e, f, i, j, w, h) for i in range(w)] for j in range(h)], np.uint8).reshape(h, w, 3)

# ---------------- atlases: main (everything) and the animated paw strip (pose faces only)
def pack(keys, sizes):
    for N in (32, 64, 128, 256, 512, 1024):
        x = y = shelf = 0; pos = {}; ok = True
        for k in sorted(keys, key=lambda k: (-sizes[k][1], -sizes[k][0])):
            cw, ch = sizes[k][0] + 2, sizes[k][1] + 2
            if x + cw > N: x = 0; y += shelf; shelf = 0
            if y + ch > N: ok = False; break
            pos[k] = (x + 1, y + 1); x += cw; shelf = max(shelf, ch)
        if ok: return N, pos
def blit(img, x0, y0, arr):
    h, w = arr.shape[:2]
    img[y0:y0 + h, x0:x0 + w, :3] = arr; img[y0:y0 + h, x0:x0 + w, 3] = 255
    img[y0 - 1, x0:x0 + w] = img[y0, x0:x0 + w]; img[y0 + h, x0:x0 + w] = img[y0 + h - 1, x0:x0 + w]
    img[y0 - 1:y0 + h + 1, x0 - 1] = img[y0 - 1:y0 + h + 1, x0]; img[y0 - 1:y0 + h + 1, x0 + w] = img[y0 - 1:y0 + h + 1, x0 + w - 1]

sizes = {k: face_size(E[k[0]], k[1]) for k in tex}
N, pos = pack(list(tex), sizes)
atlas = np.zeros((N, N, 4), np.uint8); uv = {}
for k, (x0, y0) in pos.items():
    blit(atlas, x0, y0, tex[k]); w, h = sizes[k]; uv[k] = (x0, y0, x0 + w, y0 + h)

pkeys = [k for k in tex if E[k[0]]['pose'] is not None]
S, ppos = pack(pkeys, sizes)
strip = np.zeros((S * len(POSES), S, 4), np.uint8); puv = {}
for k, (x0, y0) in ppos.items():
    p = E[k[0]]['pose']; blit(strip, x0, y0 + p * S, tex[k]); w, h = sizes[k]; puv[k] = (x0, y0, x0 + w, y0 + h)

# ---------------- models
def element(ei, which):
    e = E[ei]
    if which == 'paw':
        faces = {f: {'uv': [round(v * 16 / S, 6) for v in puv[(ei, f)]], 'texture': '#paw'} for f in FACES}
    else:
        faces = {f: {'uv': [round(v * 16 / N, 6) for v in uv[(ei, f)]], 'texture': '#atlas'} for f in FACES}
    return {'name': ('Ivy ' if e['part'] in ('fur', 'ear', 'collar', 'tag') else '') + e['name'], 'from': e['frm'], 'to': e['to'], 'faces': faces}
ybot = min(e['frm'][1] for e in E)
DISPLAY = {
    'fixed': {'rotation': [-90, 0, 0], 'translation': [0, 0, round(2 * (ybot - 8), 3)], 'scale': [2, 2, 2]},
    'gui': {'rotation': [30, 225, 0], 'translation': [0, 0.5, 0], 'scale': [0.66, 0.66, 0.66]},
    'ground': {'translation': [0, 3, 0], 'scale': [0.25, 0.25, 0.25]},
    'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]},
    'thirdperson_lefthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.375, 0.375, 0.375]},
    'firstperson_righthand': {'rotation': [0, 45, 0], 'scale': [0.4, 0.4, 0.4]},
    'firstperson_lefthand': {'rotation': [0, 225, 0], 'scale': [0.4, 0.4, 0.4]},
}
body = [ei for ei, e in enumerate(E) if e['pose'] is None]
def write_model(name, els, slots, credit):
    m = {'credit': credit, 'texture_size': [N, N], 'textures': slots, 'elements': els, 'display': DISPLAY}
    (OUT / f'{name}.json').write_text(json.dumps(m, indent=2) + '\n')
base_slots = {'atlas': NS + NAME, 'particle': NS + NAME}
write_model(NAME, [element(i, 'atlas') for i in body] + [element(i, 'paw') for i, e in enumerate(E) if e['pose'] is not None],
            dict(base_slots, paw=NS + NAME + '_paw'), f'Lucky Ivy ({VARIANT}) - Realms Beyond')
Image.fromarray(atlas, 'RGBA').save(OUT / f'{NAME}.png', optimize=True)
Image.fromarray(strip, 'RGBA').save(OUT / f'{NAME}_paw.png', optimize=True)
# a beckoning wave: hold up 1 s, swing down through every in-between pose, rest, swing back up (~2.5 s a cycle)
(OUT / f'{NAME}_paw.png.mcmeta').write_text(json.dumps({'animation': {'interpolate': False, 'frames': [
    {'index': 0, 'time': 20}] + [{'index': k, 'time': 2} for k in range(1, REST)] + [{'index': REST, 'time': 10}]
    + [{'index': k, 'time': 2} for k in range(REST - 1, 0, -1)]}}, indent=2) + '\n')
for nm in (NAME,):
    (OUT / f'{nm}_item.json').write_text(json.dumps({'model': {'type': 'minecraft:model', 'model': NS + nm}}, indent=2) + '\n')

# ---------------- audit
AXL = {'north': (2, -1), 'south': (2, 1), 'west': (0, -1), 'east': (0, 1), 'down': (1, -1), 'up': (1, 1)}
bad = []
for a_, b_ in itertools.combinations(E, 2):
    if a_['pose'] is not None and b_['pose'] is not None and a_['pose'] != b_['pose']: continue
    for f in FACES:
        ax, sg = AXL[f]
        ca = a_['to'][ax] if sg > 0 else a_['frm'][ax]; cb = b_['to'][ax] if sg > 0 else b_['frm'][ax]
        if ca != cb: continue
        ov = 1
        for q in range(3):
            if q != ax: ov *= max(0, min(a_['to'][q], b_['to'][q]) - max(a_['frm'][q], b_['frm'][q]))
        if ov > 0 and not (f == 'down' and ca in (0, Y)): bad.append((a_['name'], b_['name'], f))
lo = [min(e['frm'][q] for e in E) for q in range(3)]; hi = [max(e['to'][q] for e in E) for q in range(3)]
print('elements', len(E), 'atlas', N, 'paw frame', S, 'bounds', lo, hi, '| coplanar overlaps:', bad or 0)

# ---------------- preview renders (orthographic, Minecraft face shading)
AXD = {'north': (2, -1), 'south': (2, 1), 'west': (0, -1), 'east': (0, 1), 'down': (1, -1), 'up': (1, 1)}
def render(pose, yaw, pitch, ppu=24, W=20, Hh=20, center=(8, 7.5, 8), bg=(44, 38, 36)):
    th, ph = math.radians(yaw), math.radians(pitch)
    fw = -np.array([math.sin(th) * math.cos(ph), math.sin(ph), -math.cos(th) * math.cos(ph)])
    rr = np.cross(fw, [0, 1, 0]); rr /= np.linalg.norm(rr); up = np.cross(rr, fw)
    wpx, hpx = int(W * ppu), int(Hh * ppu)
    sx = (np.arange(wpx) + .5) / ppu - W / 2; sy = Hh / 2 - (np.arange(hpx) + .5) / ppu
    P = ((np.array(center) - fw * 80)[None, None, :] + rr[None, None, :] * sx[None, :, None] + up[None, None, :] * sy[:, None, None]).reshape(-1, 3)
    best = np.full(len(P), 1e18); out = np.tile(np.array(bg, np.float32), (len(P), 1))
    for ei, e in enumerate(E):
        if e['pose'] is not None and e['pose'] != pose: continue
        for fc in FACES:
            ax, sg = AXD[fc]
            if sg * fw[ax] >= -1e-9: continue
            coord = e['to'][ax] if sg > 0 else e['frm'][ax]
            t = (coord - P[:, ax]) / fw[ax]; q = P + t[:, None] * fw[None, :]; m = t < best
            for kq in range(3):
                if kq != ax: m &= (q[:, kq] >= e['frm'][kq] - 1e-9) & (q[:, kq] <= e['to'][kq] + 1e-9)
            if not m.any(): continue
            fx, fy, fz = e['frm']; tx, ty, tz = e['to']; qx, qy, qz = q[m, 0], q[m, 1], q[m, 2]
            w, h = face_size(e, fc)
            ii, jj = {'north': (tx - qx, ty - qy), 'south': (qx - fx, ty - qy), 'west': (qz - fz, ty - qy), 'east': (tz - qz, ty - qy),
                      'up': (qx - fx, qz - fz), 'down': (qx - fx, tz - qz)}[fc]
            ii = np.clip(np.floor(ii * D).astype(int), 0, w - 1); jj = np.clip(np.floor(jj * D).astype(int), 0, h - 1)
            out[m] = tex[(ei, fc)][jj, ii].astype(np.float32) * SHADE[fc]; best[m] = t[m]
    return Image.fromarray(out.reshape(hpx, wpx, 3).clip(0, 255).astype(np.uint8))
if '--preview' in sys.argv or True:
    hero = [render(p, -30, 24, ppu=26) for p in (0, REST)]          # 3/4 front, like the concept
    sheet = Image.new('RGB', (sum(v.width for v in hero), hero[0].height)); x = 0
    for v in hero: sheet.paste(v, (x, 0)); x += v.width
    sheet.save(OUT / f'preview-hero-{VARIANT}.png')
    views = [render(0, y, p, ppu=14) for y, p in ((0, 8), (40, 20), (90, 6), (180, 15), (-60, 30))] + [render(1, -30, 24, ppu=14)]
    sheet = Image.new('RGB', (sum(v.width for v in views), views[0].height)); x = 0
    for v in views: sheet.paste(v, (x, 0)); x += v.width
    sheet.save(OUT / f'preview-views-{VARIANT}.png')
