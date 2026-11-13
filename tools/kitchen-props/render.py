#!/usr/bin/env python3
"""Preview: render.py <pack_root> <out_dir>. Every frame of each kitchen prop, in model space, on stand-in blocks
(counter / furnace under the top props; brick cheeks, back wall and a campfire around the spit). Vanilla face-UV
conventions and element rotations. Not an in-game check."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

root, out = sys.argv[1], sys.argv[2]
a = os.path.join(root, 'assets', 'realm')


def rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array({'x': [[1, 0, 0], [0, c, -s], [0, s, c]], 'y': [[c, 0, s], [0, 1, 0], [-s, 0, c]],
                     'z': [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis])


def fq(e, n):
    (x1, y1, z1), (x2, y2, z2) = e['from'], e['to']
    T = {'north': ((x2, y2, z1), (x1 - x2, 0, 0), (0, y1 - y2, 0)), 'south': ((x1, y2, z2), (x2 - x1, 0, 0), (0, y1 - y2, 0)),
         'west': ((x1, y2, z1), (0, 0, z2 - z1), (0, y1 - y2, 0)), 'east': ((x2, y2, z2), (0, 0, z1 - z2), (0, y1 - y2, 0)),
         'up': ((x1, y2, z1), (x2 - x1, 0, 0), (0, 0, z2 - z1)), 'down': ((x1, y1, z2), (x2 - x1, 0, 0), (0, 0, z1 - z2))}[n]
    return [np.array(v, float) for v in T]


SH = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}
SCENES = {  # stand-in blocks: (lo, hi, rgb)
    'top': [((0, -8, 0), (16, 8, 16), (150, 98, 78))],
    'wall': [((-16, -16, -8), (0, 0, 24), (120, 120, 120)), ((16, -16, -8), (32, 0, 24), (120, 120, 120)),
             ((-16, 0, -8), (0, 16, 24), (168, 84, 64)), ((16, 0, -8), (32, 16, 24), (168, 84, 64)),   # cheeks
             ((0, 0, -8), (16, 16, 8), (150, 74, 58)),                 # back wall
             ((1, -16, 9), (15, -9, 23), (110, 80, 50))],             # campfire logs (in its own block)
}


def render(model, tex, frame, scene, C, S, size, centre):
    F = tex.width
    quads = []

    def add(p4, col):
        q = [C @ (np.array(p) - centre) for p in p4]
        quads.append((sum(v[2] for v in q) / 4, [(size[0] * .5 + v[0] * S, size[1] * .5 - v[1] * S) for v in q], col))
    for lo, hi, rgb in SCENES[scene]:
        e = {'from': lo, 'to': hi}
        for n in SH:
            tl, du, dv = fq(e, n); add([tl, tl + du, tl + du + dv, tl + dv], tuple(int(c * SH[n]) for c in rgb) + (255,))
    for e in model['elements']:
        r = e.get('rotation'); M = rot(r['axis'], r['angle']) if r else np.eye(3)
        o = np.array(r['origin'], float) if r else np.zeros(3)
        for n, f in e['faces'].items():
            tl, du, dv = fq(e, n); u1, v1, u2, v2 = [c * F / 16 for c in f['uv']]
            nu, nv = max(1, round(abs(u2 - u1))), max(1, round(abs(v2 - v1)))
            for i in range(nu):
                for j in range(nv):
                    px = tex.getpixel((int(u1 + (u2 - u1) * (i + .5) / nu), int(v1 + (v2 - v1) * (j + .5) / nv) + frame * F))
                    if px[3] < 128: continue
                    sh = SH[n] if e.get('shade', True) else 1.0
                    c4 = [tl + du * a_ / nu + dv * b_ / nv for a_, b_ in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
                    add([M @ (p - o) + o for p in c4], tuple(int(c * sh) for c in px[:3]) + (255,))
    im = Image.new('RGBA', size, (58, 64, 72, 255))
    for _, poly, col in sorted(quads, key=lambda q: q[0]):
        layer = Image.new('RGBA', size, (0, 0, 0, 0)); ImageDraw.Draw(layer).polygon(poly, fill=col)
        im = Image.alpha_composite(im, layer)
    return im


JOBS = [('kitchen_bread_cutting', 'top', rot('x', 35) @ rot('y', -30), 22, (8, 10, 8)),
        ('kitchen_vegetable_pan', 'top', rot('x', 35) @ rot('y', -30), 20, (9, 11, 8)),
        ('kitchen_rotating_spit', 'wall', rot('x', 30) @ rot('y', 20), 13, (8, 6, 14))]
os.makedirs(out, exist_ok=True)
for name, scene, C, S, centre in JOBS:
    model = json.load(open(os.path.join(a, 'models/item/decorations', name + '.json')))
    tex = Image.open(os.path.join(a, 'textures/item/decorations', name + '.png')).convert('RGBA')
    nf = tex.height // tex.width; cols = 5; W, H = 360, 300
    sheet = Image.new('RGBA', (W * cols, H * ((nf + cols - 1) // cols)), (58, 64, 72, 255))
    for f in range(nf):
        sheet.paste(render(model, tex, f, scene, C, S, (W, H), np.array(centre, float)), (W * (f % cols), H * (f // cols)))
    sheet.save(os.path.join(out, name + '_frames.png')); print('saved', name)
