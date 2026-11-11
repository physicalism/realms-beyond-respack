#!/usr/bin/env python3
"""Preview: render.py <pack_root> <out.png>. Renders every animation frame on a stand-in vanilla anvil,
using vanilla face-UV conventions, and checks the item-frame transform chain numerically."""
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw
root, out = sys.argv[1], sys.argv[2]
a = os.path.join(root, 'assets', 'realm')
model = json.load(open(os.path.join(a, 'models/item/decorations/anvil_hammer.json')))
tex = Image.open(os.path.join(a, 'textures/item/decorations/anvil_hammer.png')).convert('RGBA')
meta = json.load(open(os.path.join(a, 'textures/item/decorations/anvil_hammer.png.mcmeta')))
F = tex.width; NF = tex.height // F

def rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array({'x': [[1, 0, 0], [0, c, -s], [0, s, c]], 'y': [[c, 0, s], [0, 1, 0], [-s, 0, c]],
                     'z': [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis])

# --- item-frame chain check: up-facing invisible frame on block (0,0,0) => frame block is (0,1,0)
d = model['display']['fixed']
Rd = rot('x', d['rotation'][0]) @ rot('y', d['rotation'][1]) @ rot('z', d['rotation'][2])
def world(m):
    local = Rd @ (np.array(d['scale']) * (np.array(m) - 8) / 16) + np.array(d['translation']) / 16
    return np.array([.5, 1.5, .5]) + rot('x', -90) @ rot('y', 180) @ (np.array([0, 0, .5]) + 0.5 * local)
for m in ([8, 8, 8], [0, 8, 0], [16, 24, 16], [3, 9, 13]):
    w = world(m); exp = np.array([m[0] / 16, 1 + (m[1] - 8) / 16, m[2] / 16])
    assert np.allclose(w, exp), (m, w, exp)
print('frame transform OK: model (x, y, z) -> block-space (x/16, 1 + (y-8)/16, z/16)')

# face: (TL corner fn, u dir, v dir, normal)
def face_quad(e, name):
    (x1, y1, z1), (x2, y2, z2) = e['from'], e['to']
    T = {'north': ((x2, y2, z1), (x1 - x2, 0, 0), (0, y1 - y2, 0)), 'south': ((x1, y2, z2), (x2 - x1, 0, 0), (0, y1 - y2, 0)),
         'west': ((x1, y2, z1), (0, 0, z2 - z1), (0, y1 - y2, 0)), 'east': ((x2, y2, z2), (0, 0, z1 - z2), (0, y1 - y2, 0)),
         'up': ((x1, y2, z1), (x2 - x1, 0, 0), (0, 0, z2 - z1)), 'down': ((x1, y1, z2), (x2 - x1, 0, 0), (0, 0, z1 - z2))}[name]
    return [np.array(v, float) for v in T]
SHADE = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}
ANVIL = [((2, -8, 2), (14, -4, 14)), ((4, -4, 3), (12, -3, 13)), ((6, -3, 4), (10, 2, 12)), ((3, 2, 0), (13, 8, 16))]

def cam(yaw, pitch): return rot('x', pitch) @ rot('y', yaw)
def render(frame, C, S=14, size=(420, 470)):
    quads = []
    def add(p4, col):
        q = [C @ (p - 8) for p in p4]
        quads.append((sum(v[2] for v in q) / 4, [(size[0] / 2 + v[0] * S, size[1] * .55 - v[1] * S) for v in q], col))
    for lo, hi in ANVIL:
        e = {'from': lo, 'to': hi}
        for n in SHADE:
            tl, du, dv = face_quad(e, n); g = int(74 * SHADE[n] + 20)
            add([tl, tl + du, tl + du + dv, tl + dv], (g, g, g + 4, 255))
    for e in model['elements']:
        r = e.get('rotation'); M = rot(r['axis'], r['angle']) if r else np.eye(3); o = np.array(r['origin'], float) if r else np.zeros(3)
        for n, f in e['faces'].items():
            tl, du, dv = face_quad(e, n); u1, v1, u2, v2 = [c * F / 16 for c in f['uv']]
            nu, nv = max(1, round(abs(u2 - u1))), max(1, round(abs(v2 - v1)))
            for i in range(nu):
                for j in range(nv):
                    px = tex.getpixel((int(u1 + (u2 - u1) * (i + .5) / nu), int(v1 + (v2 - v1) * (j + .5) / nv) + frame * F))
                    if px[3] < 128: continue
                    sh = SHADE[n] if e.get('shade', True) else 1.0
                    c4 = [tl + du * a / nu + dv * b / nv for a, b in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
                    add([M @ (p - o) + o for p in c4], tuple(int(c * sh) for c in px[:3]) + (255,))
    im = Image.new('RGBA', size, (58, 64, 72, 255)); dr = ImageDraw.Draw(im)
    for _, poly, col in sorted(quads, key=lambda q: q[0]): dr.polygon(poly, fill=col)
    return im
views = [cam(-35, 25), cam(55, 55)]
sheet = Image.new('RGBA', (420 * NF, 470 * len(views)))
for vi, C in enumerate(views):
    for f in range(NF): sheet.paste(render(f, C), (420 * f, 470 * vi))
sheet.save(out); print('saved', out, 'frames', NF, 'times', [x['time'] for x in meta['animation']['frames']])
