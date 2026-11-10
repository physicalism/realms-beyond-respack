#!/usr/bin/env python3
"""Tiny software renderer for Minecraft item models (preview only).
render.py model.json texture.png out.png yaw pitch [scale] [dark]"""
import json, math, sys
from PIL import Image

model = json.load(open(sys.argv[1]))
tex = Image.open(sys.argv[2]).convert('RGBA')
TW, TH = tex.size
tp = tex.load()
yaw, pitch = math.radians(float(sys.argv[4])), math.radians(float(sys.argv[5]))
S = float(sys.argv[6]) if len(sys.argv) > 6 else 24
DARK = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
W, H = 900, 640
img = Image.new('RGBA', (W, H), (140, 170, 120, 255))
ip = img.load()
zbuf = [[-1e9] * W for _ in range(H)]


def rot(p, axis, ang, o):
    a = math.radians(ang)
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    c, s = math.cos(a), math.sin(a)
    if axis == 'y':
        x, z = x * c + z * s, -x * s + z * c
    elif axis == 'x':
        y, z = y * c - z * s, y * s + z * c
    else:
        x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def corners(f, t, d):
    x1, y1, z1 = f; x2, y2, z2 = t
    # corners in order: (u0,v0) (u1,v0) (u1,v1) (u0,v1) -> top-left, top-right, bottom-right, bottom-left
    return {
        'north': [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)],
        'south': [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)],
        'east':  [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)],
        'west':  [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)],
        'up':    [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)],
        'down':  [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)],
    }[d]


NORM = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}
SHADE = {'up': 1.0, 'down': 0.5, 'north': 0.8, 'south': 0.8, 'east': 0.6, 'west': 0.6}


def view(p):
    x, y, z = p[0] - 0, p[1] - 15, p[2] - 8
    c, s = math.cos(yaw), math.sin(yaw)
    x, z = x * c + z * s, -x * s + z * c
    c, s = math.cos(pitch), math.sin(pitch)
    y, z = y * c - z * s, y * s + z * c
    return (W / 2 + x * S, H / 2 - y * S, z)


for e in model['elements']:
    r = e.get('rotation')
    emit = e.get('light_emission', 0)
    for d, fc in e['faces'].items():
        cs = corners(e['from'], e['to'], d)
        n = NORM[d]
        if r:
            cs = [rot(p, r['axis'], r['angle'], r['origin']) for p in cs]
            n = rot(n, r['axis'], r['angle'], (0, 0, 0))
        vc = [view(p) for p in cs]
        # back-face cull using projected winding
        ax, ay = vc[1][0] - vc[0][0], vc[1][1] - vc[0][1]
        bx, by = vc[3][0] - vc[0][0], vc[3][1] - vc[0][1]
        if ax * by - ay * bx <= 0:
            continue
        u0, v0, u1, v1 = fc['uv']
        sh = 1.0 if (e.get('shade') is False) else SHADE[d]
        # rasterize as bilinear quad via parameter sampling
        steps = int(max(abs(vc[1][0] - vc[0][0]) + abs(vc[1][1] - vc[0][1]), abs(vc[3][0] - vc[0][0]) + abs(vc[3][1] - vc[0][1])) * 2) + 2
        su = int(max(math.dist(vc[0][:2], vc[1][:2]), math.dist(vc[3][:2], vc[2][:2])) * 2) + 2
        sv = int(max(math.dist(vc[0][:2], vc[3][:2]), math.dist(vc[1][:2], vc[2][:2])) * 2) + 2
        for j in range(sv):
            b = (j + 0.5) / sv
            for i in range(su):
                a = (i + 0.5) / su
                L = [vc[0][k] * (1 - b) + vc[3][k] * b for k in range(3)]
                R = [vc[1][k] * (1 - b) + vc[2][k] * b for k in range(3)]
                P = [L[k] * (1 - a) + R[k] * a for k in range(3)]
                px, py = int(P[0]), int(P[1])
                if not (0 <= px < W and 0 <= py < H):
                    continue
                tu = u0 + (u1 - u0) * a; tv = v0 + (v1 - v0) * b
                tx = min(TW - 1, max(0, int(tu / 16 * TW))); ty = min(TH - 1, max(0, int(tv / 16 * TH)))
                c = tp[tx, ty]
                if c[3] < 128:
                    continue
                if P[2] <= zbuf[py][px] + 1e-4:
                    continue
                zbuf[py][px] = P[2]
                k = sh if emit else sh * DARK
                ip[px, py] = (int(c[0] * k), int(c[1] * k), int(c[2] * k), 255)
img.save(sys.argv[3])
