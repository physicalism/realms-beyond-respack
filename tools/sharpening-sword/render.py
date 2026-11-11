#!/usr/bin/env python3
"""Preview: render.py <pack_root> <out.png>. Every frame on a stand-in stonecutter, vanilla face-UV conventions,
plus a numeric check of the wall item-frame transform."""
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw
root, out = sys.argv[1], sys.argv[2]
a = os.path.join(root, 'assets', 'realm')
model = json.load(open(os.path.join(a, 'models/item/decorations/sharpening_sword.json')))
tex = Image.open(os.path.join(a, 'textures/item/decorations/sharpening_sword.png')).convert('RGBA')
F = tex.width; NF = tex.height // F
def rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array({'x': [[1,0,0],[0,c,-s],[0,s,c]], 'y': [[c,0,s],[0,1,0],[-s,0,c]], 'z': [[c,-s,0],[s,c,0],[0,0,1]]}[axis])
# south-facing invisible frame in block (0,0,0), hanging on the block at z = -1 (the stonecutter)
d = model['display']['fixed']
Rd = rot('x', d['rotation'][0]) @ rot('y', d['rotation'][1]) @ rot('z', d['rotation'][2])
def world(m):
    local = Rd @ (np.array(d['scale']) * (np.array(m) - 8) / 16) + np.array(d['translation']) / 16
    return np.array([.5, .5, .5]) + rot('y', 180) @ (np.array([0, 0, .5]) + 0.5 * local)
for m in ([8, 8, 8], [0, 0, -8], [16, 16, 8], [8, 16, 0]):
    assert np.allclose(world(m), [m[0] / 16, m[1] / 16, m[2] / 16 - .5]), m
print('frame transform OK: model (x, y, z) -> (x/16, y/16, z/16 - 0.5); stonecutter block is z -1..0')
def fq(e, n):
    (x1,y1,z1),(x2,y2,z2) = e['from'], e['to']
    T = {'north': ((x2,y2,z1),(x1-x2,0,0),(0,y1-y2,0)), 'south': ((x1,y2,z2),(x2-x1,0,0),(0,y1-y2,0)),
         'west': ((x1,y2,z1),(0,0,z2-z1),(0,y1-y2,0)), 'east': ((x2,y2,z2),(0,0,z1-z2),(0,y1-y2,0)),
         'up': ((x1,y2,z1),(x2-x1,0,0),(0,0,z2-z1)), 'down': ((x1,y1,z2),(x2-x1,0,0),(0,0,z1-z2))}[n]
    return [np.array(v, float) for v in T]
SH = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}
def render(frame, C, S=13, size=(420, 400)):
    quads = []
    def add(p4, col):
        q = [C @ (np.array(p) - np.array([8, 12, 0])) for p in p4]
        quads.append((sum(v[2] for v in q) / 4, [(size[0] * .45 + v[0] * S, size[1] * .5 - v[1] * S) for v in q], col))
    bm = os.path.join(root, 'assets/minecraft/models/block/stonecutter.json')
    if os.path.exists(bm) and os.path.exists(os.path.join(a, 'textures/block/stonecutter_saw.png')):   # only if the pack owns a saw texture
        saw = Image.open(os.path.join(a, 'textures/block/stonecutter_saw.png')).convert('RGBA')
        for e in json.load(open(bm))['elements']:
            e = {**e, 'from': [e['from'][0], e['from'][1], e['from'][2] - 8], 'to': [e['to'][0], e['to'][1], e['to'][2] - 8]}
            for n, f in e['faces'].items():
                tl, du, dv = fq(e, n)
                if f['texture'] != '#saw':
                    g = int(120 * SH[n] + 20); add([tl, tl+du, tl+du+dv, tl+dv], (g, g, g, 255)); continue
                u1, v1, u2, v2 = f['uv']; nu, nv = max(1, round(abs(u2-u1))), max(1, round(abs(v2-v1)))
                for i in range(nu):
                    for j in range(nv):
                        px = saw.getpixel((int(u1 + (u2-u1)*(i+.5)/nu), int(v1 + (v2-v1)*(j+.5)/nv) + (frame % (saw.height // 16)) * 16))
                        add([tl + du*a_/nu + dv*b_/nv for a_, b_ in ((i,j),(i+1,j),(i+1,j+1),(i,j+1))], tuple(int(c * SH[n]) for c in px[:3]) + (255,))
    else:
        e = {'from': (0, 0, -8), 'to': (16, 9, 8)}
        for n in SH:
            tl, du, dv = fq(e, n); g = int(120 * SH[n] + 20); add([tl, tl+du, tl+du+dv, tl+dv], (g, g, g, 255))
        for i in range(28):                                   # flat vanilla saw in the plane z = 0
            x = 1 + i * .5; h = math.sqrt(max(0, 49 - (x + .25 - 8) ** 2))
            add([(x, 9, 0), (x + .5, 9, 0), (x + .5, 9 + h, 0), (x, 9 + h, 0)], (176, 176, 180, 255))
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
    im = Image.new('RGBA', size, (58, 64, 72, 255)); dr = ImageDraw.Draw(im)
    for _, poly, col in sorted(quads, key=lambda q: q[0]): dr.polygon(poly, fill=col)
    return im
views = [rot('x', 20) @ rot('y', -30), rot('x', 25) @ rot('y', -75), rot('x', 70) @ rot('y', -20)]   # frame side; sword side; above
sheet = Image.new('RGBA', (420 * NF, 400 * len(views)))
for vi, C in enumerate(views):
    for f in range(NF): sheet.paste(render(f, C), (420 * f, 400 * vi))
sheet.save(out); print('saved', out)
