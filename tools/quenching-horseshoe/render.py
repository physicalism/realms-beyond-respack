#!/usr/bin/env python3
"""Preview: render.py <pack_root> <out.png>. Every frame on a stand-in cauldron (near walls left off so the
horseshoe shows), vanilla face-UV conventions, plus a numeric check of the floor item-frame transform."""
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw
root, out = sys.argv[1], sys.argv[2]
a = os.path.join(root, 'assets', 'realm')
model = json.load(open(os.path.join(a, 'models/item/decorations/quenching_horseshoe.json')))
tex = Image.open(os.path.join(a, 'textures/item/decorations/quenching_horseshoe.png')).convert('RGBA')
F = tex.width; NF = tex.height // F
def rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array({'x': [[1,0,0],[0,c,-s],[0,s,c]], 'y': [[c,0,s],[0,1,0],[-s,0,c]], 'z': [[c,-s,0],[s,c,0],[0,0,1]]}[axis])
d = model['display']['fixed']
Rd = rot('x', d['rotation'][0]) @ rot('y', d['rotation'][1]) @ rot('z', d['rotation'][2])
def world(m):
    local = Rd @ (np.array(d['scale']) * (np.array(m) - 8) / 16) + np.array(d['translation']) / 16
    return np.array([.5, 1.5, .5]) + rot('x', -90) @ rot('y', 180) @ (np.array([0, 0, .5]) + 0.5 * local)
for m in ([8, 8, 8], [0, -2, 0], [16, 24, 16]):
    assert np.allclose(world(m), [m[0] / 16, 1 + (m[1] - 8) / 16, m[2] / 16]), m
print('frame transform OK: model (x, y, z) -> block-space (x/16, 1 + (y-8)/16, z/16)')
def fq(e, n):
    (x1,y1,z1),(x2,y2,z2) = e['from'], e['to']
    T = {'north': ((x2,y2,z1),(x1-x2,0,0),(0,y1-y2,0)), 'south': ((x1,y2,z2),(x2-x1,0,0),(0,y1-y2,0)),
         'west': ((x1,y2,z1),(0,0,z2-z1),(0,y1-y2,0)), 'east': ((x2,y2,z2),(0,0,z1-z2),(0,y1-y2,0)),
         'up': ((x1,y2,z1),(x2-x1,0,0),(0,0,z2-z1)), 'down': ((x1,y1,z2),(x2-x1,0,0),(0,0,z1-z2))}[n]
    return [np.array(v, float) for v in T]
SH = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}
# cauldron in model coords (rim at y 8): floor, back and left walls only, and a water sheet
CAULDRON = [((0, -8, 0), (16, -4, 16)), ((0, -4, 0), (16, 8, 2)), ((0, -4, 2), (2, 8, 16))]
def render(frame, C, S=13, size=(330, 440)):
    quads = []
    def add(p4, col):
        q = [C @ (np.array(p) - np.array([8, 9, 8])) for p in p4]
        quads.append((sum(v[2] for v in q) / 4, [(size[0] * .5 + v[0] * S, size[1] * .55 - v[1] * S) for v in q], col))
    for lo, hi in CAULDRON:
        e = {'from': lo, 'to': hi}
        for n in SH:
            tl, du, dv = fq(e, n); g = int(70 * SH[n] + 24); add([tl, tl+du, tl+du+dv, tl+dv], (g, g, g + 4, 255))
    add([(2, 7, 2), (16, 7, 2), (16, 7, 16), (2, 7, 16)], (52, 92, 170, 150))
    for e in model['elements']:
        r = e.get('rotation'); M = rot(r['axis'], r['angle']) if r else np.eye(3); o = np.array(r['origin'], float) if r else np.zeros(3)
        for n, f in e['faces'].items():
            tl, du, dv = fq(e, n); u1, v1, u2, v2 = [c * F / 16 for c in f['uv']]
            nu, nv = max(1, round(abs(u2 - u1))), max(1, round(abs(v2 - v1)))
            for i in range(nu):
                for j in range(nv):
                    px = tex.getpixel((int(u1 + (u2-u1)*(i+.5)/nu), int(v1 + (v2-v1)*(j+.5)/nv) + frame * F))
                    if px[3] < 128: continue
                    sh = SH[n] if e.get('shade', True) else 1.0
                    c4 = [tl + du*a_/nu + dv*b_/nv for a_, b_ in ((i,j),(i+1,j),(i+1,j+1),(i,j+1))]
                    add([M @ (p - o) + o for p in c4], tuple(int(c * sh) for c in px[:3]) + (255,))
    im = Image.new('RGBA', size, (58, 64, 72, 255))
    for _, poly, col in sorted(quads, key=lambda q: q[0]):
        layer = Image.new('RGBA', size, (0, 0, 0, 0)); ImageDraw.Draw(layer).polygon(poly, fill=col); im = Image.alpha_composite(im, layer)
    return im
C = rot('x', 22) @ rot('y', -32)
cols = 4
rows = (NF + cols - 1) // cols
sheet = Image.new('RGBA', (330 * cols, 440 * rows), (58, 64, 72, 255))
for f in range(NF):
    sheet.paste(render(f, C), (330 * (f % cols), 440 * (f // cols)))
sheet.save(out); print('saved', out)
