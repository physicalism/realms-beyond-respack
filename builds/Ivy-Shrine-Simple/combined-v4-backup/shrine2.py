#!/usr/bin/env python3
"""Ivy figurine, projected from the concept image.

Geometry is measured off the concept through an oblique camera fitted to it
(14.5 px per unit across and up, 8 px left and 2.2 px up per unit of depth).
Every face visible from that camera takes its texels straight from the image,
divided by Minecraft's face shading so the in-game render reproduces the image;
hidden faces are mirrored across the centre line, or filled from the part's own colours.
"""
import json, math, sys, io, base64, uuid
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
REF = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32)
TAG = sys.argv[2] if len(sys.argv) > 2 else 'x'
D = 4                                  # texels per unit (0.25-unit grid) so the image detail survives
A, B, C, EZ = 14.5, -8.0, 14.5, 2.2    # camera: x = X0 + A*(X-8) + B*Z ; y = Y0 - C*Y - EZ*Z
X0, Y0 = 380.0, 680.0
FACES = ('north', 'south', 'west', 'east', 'up', 'down')
SHADE = {'up': 1.0, 'down': .5, 'north': .8, 'south': .8, 'east': .6, 'west': .6}

def proj_dog(p):
    X, Y, Z = p
    return X0 + A * (X - 8) + B * Z, Y0 - C * Y - EZ * Z
SCX = np.array([12.552, -0.074, -6.118, 229.805]); SCY = np.array([-1.726, -17.897, -2.521, 673.568])
def proj_shrine(p):
    X, Y, Z = p
    return SCX @ (X, Y, Z, 1), SCY @ (X, Y, Z, 1)
import os
COMBINE = os.environ.get('COMBINE') == '1'
DOG_S, DOG_C = (0.8 if COMBINE else 0.85), np.array([8.0, 0.0, 5.0])   # dog scale
DOG_T = np.array([0.0, 1.0, 1.5]) if COMBINE else np.zeros(3)                  # placement on the detailed plinth
def proj(p, cam='dog'):
    if cam == 'dog': return proj_dog(tuple(DOG_C + (np.array(p) - DOG_C - DOG_T) / DOG_S))
    return proj_shrine(p)

E = []
def box(name, a, b, part='fur'):
    q = lambda v: round(v * D) / D
    E.append(dict(name=name, frm=[q(v) for v in a], to=[q(v) for v in b], part=part))

# ---- geometry measured off the concept (units; Y up, Z away from the viewer, dog faces -Z)
def sbox(name, a, b, part):
    q = lambda v: round(v * D) / D
    E.append(dict(name=name, frm=[q(v) for v in a], to=[q(v) for v in b], part=part, cam='shrine'))
# plinth with raised step and an amethyst set into each face
sbox('plinth', (-5, -9, -8), (21, -1, 18), 'stone')
sbox('step', (-1, -1, -3), (17, 0, 13), 'stone')
sbox('gem N', (5, -7.25, -8.25), (11, -2.75, -8), 'ameth'); sbox('gem S', (5, -7.25, 18), (11, -2.75, 18.25), 'ameth')
sbox('gem W', (-5.25, -7.25, 2), (-5, -2.75, 8), 'ameth'); sbox('gem E', (21, -7.25, 2), (21.25, -2.75, 8), 'ameth')
# four gold columns with bases, capitals and stepped corbels under the roof
for cx in (-2, 18):
    for cz in (-5, 15):
        t = ('W' if cx < 8 else 'E') + ('N' if cz < 5 else 'S')
        sbox('col base ' + t, (cx - 2, -1, cz - 2), (cx + 2, 1, cz + 2), 'gold')
        sbox('col shaft ' + t, (cx - 1, 1, cz - 1), (cx + 1, 22.75, cz + 1), 'gold')
        sbox('col capital ' + t, (cx - 1.5, 22.75, cz - 1.5), (cx + 1.5, 24, cz + 1.5), 'gold')
        for sg in (-1, 1):                                   # three-step corbels each way under the roof
            for n_, (d0, d1, y0) in enumerate(((1.5, 2.5, 20.5), (2.5, 3.5, 21.75), (3.5, 4.5, 23))):
                lo, hi = sorted((cx + sg * d0, cx + sg * d1))
                sbox(f'corbel {t} x{sg}{n_}', (lo, y0, cz - .5), (hi, 24, cz + .5), 'gold')
                lo, hi = sorted((cz + sg * d0, cz + sg * d1))
                sbox(f'corbel {t} z{sg}{n_}', (cx - .5, y0, lo), (cx + .5, 24, hi), 'gold')
# stepped gold roof and finial
sbox('roof', (-5.5, 24, -8.5), (21.5, 26.75, 18.5), 'gold')
sbox('roof tier', (-2.5, 26.75, -5.5), (18.5, 28.75, 15.5), 'gold')
sbox('roof tier 2', (0.5, 28.75, -2.5), (15.5, 30.75, 12.5), 'gold')
sbox('finial', (5.5, 30.75, 2.5), (10.5, 34.5, 7.5), 'gold')
if COMBINE:
    E.clear()                                                # the detailed shrine supplies the stone architecture...
    DET = json.load(open(os.environ['DETAILED']))
    GOLD_NAMES = ('gold capital', 'column shaft', 'roof slab', 'roof tier', 'roof upper tier', 'gold finial')
    for el in DET['elements']:                                 # ...its columns are repainted in the concept's gold, 2 units taller
        nm = el['name']
        if nm.startswith('column shaft'): sbox(nm, el['from'], [el['to'][0], el['to'][1] + 2, el['to'][2]], 'gold')
        elif nm.startswith('gold capital'): sbox(nm, [el['from'][0], el['from'][1] + 2, el['from'][2]], [el['to'][0], el['to'][1] + 2, el['to'][2]], 'gold')
    # Japanese-style roof: wide thin eave with upturned corner tips, concave steps to a ridge, gold spire
    sbox('eave', (-3, 27, -3), (19, 28.25, 19), 'gold')
    for cx_, cz_ in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        def corner(a, b): return (min(8 + cx_ * a, 8 + cx_ * b), max(8 + cx_ * a, 8 + cx_ * b))
        ax0, ax1 = corner(10, 11); az0, az1 = corner(10, 11) if False else (min(8 + cz_ * 10, 8 + cz_ * 11), max(8 + cz_ * 10, 8 + cz_ * 11))
        sbox(f'eave corner {cx_},{cz_}', (ax0, 28.25, az0), (ax1, 29, az1), 'gold')
        bx0, bx1 = min(8 + cx_ * 10.5, 8 + cx_ * 11.5), max(8 + cx_ * 10.5, 8 + cx_ * 11.5)
        bz0, bz1 = min(8 + cz_ * 10.5, 8 + cz_ * 11.5), max(8 + cz_ * 10.5, 8 + cz_ * 11.5)
        sbox(f'eave tip {cx_},{cz_}', (bx0, 29, bz0), (bx1, 30.5, bz1), 'gold')                # upturned tip
    for n_, (h0, h1, r) in enumerate(((28.25, 28.75, 9.5), (28.75, 29.5, 8), (29.5, 30.5, 6.5), (30.5, 31.75, 5), (31.75, 33.25, 3.5))):
        sbox(f'roof step {n_}', (8 - r, h0, 8 - r), (8 + r, h1, 8 + r), 'gold')
    sbox('ridge cap', (6, 33.25, 6), (10, 34, 10), 'gold'); sbox('ridge top', (6.75, 34, 6.75), (9.25, 34.5, 9.25), 'gold')
    sbox('spire', (7.25, 34.5, 7.25), (8.75, 35.5, 8.75), 'gold'); sbox('spire tip', (7.5, 35.5, 7.5), (8.5, 36, 8.5), 'gold')
    for cx in (1, 15):                                         # concept-style stepped corbels under the roof, inward
        for cz in (1, 15):
            sx, sz = (1 if cx < 8 else -1), (1 if cz < 8 else -1)
            for n_, (d0, d1, y0, y1) in enumerate(((1, 2, 23.75, 26), (2, 3, 24.75, 27), (3, 4, 25.75, 27))):
                a0, a1 = sorted((cx + sx * d0, cx + sx * d1)); sbox(f'corbel x {cx},{cz},{n_}', (a0, y0, cz - .5), (a1, y1, cz + .5), 'gold')
                a0, a1 = sorted((cz + sz * d0, cz + sz * d1)); sbox(f'corbel z {cx},{cz},{n_}', (cx - .5, y0, a0), (cx + .5, y1, a1), 'gold')
_n0 = len(E)
box('front paw L', (4, 0, 0), (7.5, 3, 4)); box('front paw R', (8.5, 0, 0), (12, 3, 4))
box('front leg L', (4, 3, 1), (7, 9, 4)); box('front leg R', (9, 3, 1), (12, 9, 4))
box('hind foot L', (1, 0, 1), (4, 2.5, 4.5)); box('hind foot R', (12, 0, 1), (15, 2.5, 4.5))
box('haunch L', (0.5, 0, 4.5), (4, 8, 9)); box('haunch R', (12, 0, 4.5), (15.5, 8, 9))
box('rump L', (0.5, 0, 9), (4, 6, 13)); box('rump R', (12, 0, 9), (15.5, 6, 13))      # haunches drop towards the back
box('body', (4, 3, 4), (12, 9, 13))
box('chest', (4, 9, 0.5), (12, 14, 8.5))
box('neck', (5, 14, 1.5), (11, 17.25, 6))
# collar: a ring round the neck plus a stepped V across the front, dipping to the tag
box('collar', (4.5, 15, 0.25), (11.5, 16.75, 6.5), 'collar')                            # plain band round the neck
box('tag', (7.5, 14, 0), (8.5, 15, 0.5), 'collar')                                         # small gold tag
box('head', (4.5, 17.25, 0), (11.5, 24.75, 6.5))
box('head back', (5.25, 18, 6.5), (10.75, 24, 7.25)); box('head back 2', (6, 19, 7.25), (10, 23.25, 7.75))   # fuller, rounded back of the skull
box('snout', (5.75, 17.75, -3), (10.25, 21.5, 0))     # short block set below the eyes
for sg, xo, xi in ((-1, 2.75, 4.5), (1, 11.5, 13.25)):
    lo, hi = (xo, xi) if sg < 0 else (xi - 1.75, xi)
    t = 'L' if sg < 0 else 'R'
    inset = lambda d: (lo + d, hi) if sg < 0 else (lo, hi - d)        # trim from the outer side
    box('ear top ' + t, (inset(0.75)[0], 24, 1.5), (inset(0.75)[1], 24.75, 5), 'ear')          # diagonal top outer corner...
    box('ear upper ' + t, (inset(0.25)[0], 23.25, 0.5), (inset(0.25)[1], 24, 6), 'ear')       # ...in two steps
    box('ear ' + t, (lo, 18.5, 0.5), (hi, 23.25, 6), 'ear')
    box('ear tip ' + t, (lo + (0.25 if sg < 0 else 0), 17.5, 1.25), (hi - (0 if sg < 0 else 0.25), 18.5, 5.25), 'ear')  # rounded lower edge
    box('ear bulge ' + t, ((lo - 0.25) if sg < 0 else hi, 19.5, 1.5), (lo if sg < 0 else hi + 0.25, 22.75, 5), 'ear')   # curve of the flap

# scale the dog about its footprint centre, then snap back to the 0.25 grid
for e in E[_n0:]:
    if 'ear_rot' in e:
        ang, o = e['ear_rot']
        e['rot'] = dict(angle=-ang, axis='z', origin=[float(DOG_C[q] + (o[q] - DOG_C[q]) * DOG_S + DOG_T[q]) for q in range(3)])
for e in E[_n0:]:
    e['cam'] = 'dog'
    for k in ('frm', 'to'):
        e[k] = [(DOG_C[q] + math.copysign(math.floor(abs(e[k][q] - DOG_C[q]) * DOG_S * D + 0.5) / D, e[k][q] - DOG_C[q]) if q == 0
                else round((DOG_C[q] + (e[k][q] - DOG_C[q]) * DOG_S) * D) / D) + DOG_T[q] for q in range(3)]
if COMBINE:
    def tbox(name, a, b, pose):
        E.append(dict(name=name, frm=list(a), to=list(b), part='fur', cam='dog', pose=pose))
    for pose in range(3):
        dx = pose - 1                                          # the part on the plinth swings for the wag
        tbox(f'tail root p{pose}', (8, 3.75, 12.75), (10.5, 5.75, 14.25), pose)
        tbox(f'tail drop p{pose}', (8.25 + dx / 2, 1.25, 13.75), (10.25 + dx / 2, 4, 15.25), pose)
        tbox(f'tail base p{pose}', (9 + dx, 1, 14.75), (11 + dx, 2.75, 16.5), pose)
        tbox(f'tail edge p{pose}', (10.5 + dx / 2, 1, 16.5), (12.5 + dx / 2, 2.75, 18), pose)
        tbox(f'tail hang p{pose}', (10.5, -2.5, 17), (12.5, 1, 18), pose)
        tbox(f'tail tip p{pose}', (10.75, -3.75, 17), (12.25, -2.5, 17.75), pose)

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

# ---- visibility from the concept camera: rasterise faces into an id/depth buffer at image resolution
Himg, Wimg = REF.shape[:2]
view = np.array([-B / A, -EZ / C, 1.0]); view /= np.linalg.norm(view)        # direction away from the viewer
NORM = {'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}
BUF = {}
faces = []
def view_dir(cam):
    # direction that projects to a point, i.e. straight away from the camera
    if cam == 'dog': v = np.array([-B / A, -EZ / C, 1.0])
    else:
        Mx = np.array([SCX[:3], SCY[:3]]); v = np.cross(Mx[0], Mx[1])
        if v[2] < 0: v = -v
    return v / np.linalg.norm(v)
VIEW = {c: view_dir(c) for c in ('dog', 'shrine')}
for ei, e in enumerate(E):
    for f in FACES:
        if np.dot(NORM[f], VIEW[e['cam']]) >= 0: continue                     # faces turned away from their camera
        faces.append((ei, f))
for cam in ('dog', 'shrine'): BUF[cam] = [np.full((Himg, Wimg), -1, np.int32), np.full((Himg, Wimg), 1e9)]
yy, xx = np.mgrid[0:Himg, 0:Wimg]
for fid, (ei, f) in enumerate(faces):
    e = E[ei]; w, h = face_size(e, f); cam = e['cam']; idbuf, zbuf = BUF[cam]; view = VIEW[cam]
    p00 = np.array(texel_pos(e, f, -.5, -.5)); p10 = np.array(texel_pos(e, f, w - .5, -.5)); p01 = np.array(texel_pos(e, f, -.5, h - .5))
    q00, q10, q01 = (np.array(proj(p_, cam)) for p_ in (p00, p10, p01))
    M = np.column_stack([q10 - q00, q01 - q00])
    if abs(np.linalg.det(M)) < 1e-6: continue
    Mi = np.linalg.inv(M)
    xs = [q00[0], q10[0], q01[0], (q10 + q01 - q00)[0]]; ys = [q00[1], q10[1], q01[1], (q10 + q01 - q00)[1]]
    x0, x1 = max(0, int(min(xs))), min(Wimg, int(max(xs)) + 1); y0, y1 = max(0, int(min(ys))), min(Himg, int(max(ys)) + 1)
    if x0 >= x1 or y0 >= y1: continue
    px = xx[y0:y1, x0:x1] + .5 - q00[0]; py = yy[y0:y1, x0:x1] + .5 - q00[1]
    uvw = Mi @ np.stack([px.ravel(), py.ravel()])
    inside = ((uvw[0] >= 0) & (uvw[0] <= 1) & (uvw[1] >= 0) & (uvw[1] <= 1)).reshape(px.shape)
    P3 = p00[None, :] + uvw[0][:, None] * (p10 - p00) + uvw[1][:, None] * (p01 - p00)
    depth = (P3 @ view).reshape(px.shape)
    sub_z = zbuf[y0:y1, x0:x1]; sub_i = idbuf[y0:y1, x0:x1]
    win = inside & (depth < sub_z - 1e-6)
    sub_z[win] = depth[win]; sub_i[win] = fid

# pixels that are not the dog in the concept (background, gold pillar, stone) never donate colour
r, g, b = REF[..., 0], REF[..., 1], REF[..., 2]
is_gold = (r > 120) & (r - b > 50)
is_bg = (r > 95) & (abs(r - g) < 18) & (abs(g - b) < 18) & (r < 200)      # warm grey backdrop and stone
pillar = (xx >= 194) & (xx <= 244)
is_purple = (b > r + 15) & (b > g + 30)
is_stone = (abs(r - g) < 22) & (abs(g - b) < 22) & ~is_gold & ~is_purple
def usable(part, xi, yi, cam):
    if part == 'gold': return bool(is_gold[yi, xi])
    if part == 'ameth': return bool(is_purple[yi, xi])
    if part == 'stone': return bool(is_stone[yi, xi]) and yi > 600 and REF[yi, xi].mean() > 72   # plinth stone, not the dog's shadow
    if pillar[yi, xi]: return False
    if part == 'collar': return bool(is_gold[yi, xi])
    return not is_gold[yi, xi] and not is_bg[yi, xi]

fid_of = {key: k for k, key in enumerate(faces)}
def sample(ei, f, p):
    """Image colour for 3D point p on face (ei, f) if that face is what the concept shows there."""
    if (ei, f) not in fid_of: return None
    cam = E[ei]['cam']; idbuf = BUF[cam][0]
    x, y = proj(p, cam); xi, yi = int(x), int(y)
    if not (0 <= xi < Wimg and 0 <= yi < Himg) or idbuf[yi, xi] != fid_of[(ei, f)]: return None
    if not usable(E[ei]['part'], xi, yi, cam): return None
    c = REF[yi, xi]; k = 1 / SHADE[f]
    k = min(k, 250 / max(1.0, float(c.max())))          # undo Minecraft's face shading without clipping the hue
    return c * k

MIRROR = {'west': 'east', 'east': 'west'}
MIRROR_Z = {'north': 'south', 'south': 'north'}
def find_box(mf, mt, cam):
    for k, o in enumerate(E):
        if o['cam'] == cam and all(abs(o['frm'][q] - mf[q]) < .3 and abs(o['to'][q] - mt[q]) < .3 for q in range(3)): return k
    return None
def mirror_box(ei):
    e = E[ei]; k = find_box([16 - e['to'][0], e['frm'][1], e['frm'][2]], [16 - e['frm'][0], e['to'][1], e['to'][2]], e['cam'])
    return ei if k is None else k
def mirror_box_z(ei):
    e = E[ei]; k = find_box([e['frm'][0], e['frm'][1], 10 - e['to'][2]], [e['to'][0], e['to'][1], 10 - e['frm'][2]], e['cam'])
    return ei if k is None else k

tex = {}
for ei, e in enumerate(E):
    for f in FACES:
        w, h = face_size(e, f); arr = np.full((h, w, 3), np.nan, np.float32)
        for j in range(h):
            for i in range(w):
                p = texel_pos(e, f, i, j)
                c = sample(ei, f, p)
                if c is None:                                               # mirror across the centre line
                    mf = MIRROR.get(f, f); mp = (16 - p[0], p[1], p[2])
                    c = sample(mirror_box(ei), mf, mp)
                if c is None and e['cam'] == 'shrine':                      # ...and front-to-back for the shrine
                    for ff, pp, kk in ((MIRROR_Z.get(f, f), (p[0], p[1], 10 - p[2]), mirror_box_z(ei)),):
                        c = sample(kk, ff, pp)
                        if c is None:
                            c = sample(mirror_box(kk), MIRROR.get(ff, ff), (16 - pp[0], pp[1], pp[2]))
                if c is not None: arr[j, i] = c
        tex[(ei, f)] = arr
# shrine textures: average the copied colours into 1-unit cells, the concept's own pixel size
for (ei, f), arr in tex.items():
    if E[ei]['cam'] != 'shrine': continue
    h, w = arr.shape[:2]
    for j0 in range(0, h, D):
        for i0 in range(0, w, D):
            cell = arr[j0:j0 + D, i0:i0 + D]; ok = ~np.isnan(cell[..., 0])
            if ok.any(): cell[:] = cell[ok].mean(axis=0)
# fill what neither the image nor the mirror can see from the part's own visible colours
for ei, e in enumerate(E):
    pool = np.concatenate([a[~np.isnan(a[..., 0])] for (k, f), a in tex.items() if k == ei] or [np.zeros((0, 3))])
    for f in FACES:
        arr = tex[(ei, f)]; miss = np.isnan(arr[..., 0])
        if not miss.any(): continue
        if len(pool):
            base = np.median(pool, axis=0)
            fill = base * (0.9 if f in ('south', 'down') else 1.0)
        else:
            base = {'stone': (110, 106, 112), 'collar': (210, 160, 64), 'gold': (214, 164, 70), 'ameth': (130, 80, 170)}.get(e['part'], (52, 46, 52)); fill = np.array(base, np.float32)
        arr[miss] = fill
        tex[(ei, f)] = arr

# ---- clean statue textures: the concept's palette and blocky style, mirrored left-right
# (and front-back on the shrine) so it reads as a carved, symmetrical model, not a lit photo.
FURP  = [(30, 25, 28), (42, 36, 40), (54, 47, 52), (68, 60, 65), (86, 76, 82)]
EMERP = [(18, 66, 44), (28, 98, 62), (40, 132, 82), (66, 170, 104), (132, 210, 152)]
GOLDP = [(140, 92, 32), (186, 132, 46), (214, 160, 62), (234, 186, 86), (246, 212, 132)]
STONP = [(72, 66, 72), (92, 86, 92), (112, 106, 112), (132, 126, 132), (154, 148, 154)]
AMEP  = [(64, 30, 104), (92, 50, 142), (124, 78, 172), (164, 116, 204), (214, 182, 236)]
NOSEC, EYEC = [(18, 14, 16), (30, 24, 27), (48, 40, 44)], [(14, 10, 11), (28, 22, 24)]
def Hs(*a):
    h = 2166136261
    for v in a: h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    h ^= h >> 13; h = (h * 0x5bd1e995) & 0xffffffff; return h ^ (h >> 15)
def to_dog(p): return DOG_C + (np.array(p) - DOG_C - DOG_T) / DOG_S  # dog design coordinates
def paint(e, f, i, j, w, h):
    x, y, z = texel_pos(e, f, i, j); part = e['part']; cam = e['cam']
    side = f in ('north', 'south', 'west', 'east')
    top_row = j < D and side and h >= 2 * D; bot_row = j >= h - D and side and h >= 2 * D
    mx = abs(x - 8); mz = abs(z - (8 if COMBINE else 5)) if cam == 'shrine' else z
    cell = (math.floor(mx), math.floor(y), math.floor(mz), {'north': 0, 'south': 0 if cam == 'shrine' else 1, 'west': 2, 'east': 2, 'up': 3, 'down': 4}[f])
    n = Hs(*cell, 11) % 9
    t = {'up': 3, 'down': 0}.get(f, 2)
    if top_row: t += 1
    elif bot_row: t -= 1
    if part in ('fur', 'ear') and 'paw' not in e['name']:
        X, Y, Z = to_dog((x, y, z)); MX = abs(X - 8); nm = e['name']
        FURD = [(12, 10, 12), (20, 17, 20), (32, 28, 32), (45, 40, 46), (61, 56, 63), (82, 76, 86)]
        t = {'up': 3, 'down': 0}.get(f, 2)
        tex_row = j                                             # texel rows from the top of this face
        if side and tex_row == 0: t += 1                        # light catches the top edge of every form
        if side and tex_row >= h - 1 and h > 2: t -= 1          # contact shadow at the base
        if f == 'up' and (Y > 24 or nm in ('chest', 'body') or nm.startswith(('haunch', 'rump'))): t += 1   # sheen on head, shoulders, back
        # natural shadows
        if nm == 'chest' and f == 'north' and Y > 12.75: t -= 1                     # under the chin and collar
        if nm in ('chest', 'body') and f == 'north' and MX < 1 and Y < 9.5: t -= 1  # between the front legs
        if nm.startswith('front leg') and f in ('east', 'west') and ((X < 8) == (f == 'east')): t -= 1   # inner sides of the legs
        if nm.startswith(('haunch', 'rump')) and f in ('north', 'south') and Y < 3: t -= 1
        if nm.startswith('rump') and f == 'south': t -= 1
        if part == 'ear':
            t -= 1
            if f in ('east', 'west') and ((X < 8) == (f == 'east')): t -= 1        # inside of the flap, against the head
        if nm.startswith('neck'): t -= 1
        if nm == 'head' and f == 'north' and Y < 18.5: t -= 1                       # under the jaw line
        if nm.startswith('head back') and f == 'south': t -= 1
        # short-coat fur strokes: thin vertical strands, mirrored left to right
        if not nm.startswith('tail') and f != 'down':
            col = int(math.floor((MX if f in ('north', 'south', 'up') else Z) * 4)); row = int(math.floor(Y * 4 / 3)) if f != 'up' else int(math.floor(Z * 4 / 3))
            r_ = Hs(col, row, {'north': 0, 'south': 1, 'west': 2, 'east': 2, 'up': 3}[f], 23) % 13
            if r_ == 0: t += 1
            elif r_ == 1: t -= 1
        if nm == 'snout':
            if f == 'north':
                if MX < 1.0 and 20.5 <= Y: return NOSEC[0]
                t = 3 if tex_row else 4
            if f == 'up':
                if MX < 1.0 and Z < -2.0: return NOSEC[1]
                t = 4
            if f == 'down': t = 0
        if nm == 'head' and f == 'north' and 1.25 <= MX < 2.5 and 22.5 <= Y < 23.75:
            return EYEC[1] if Y >= 23.5 else EYEC[0]
        return FURD[max(0, min(5, t))]
    if part in ('fur', 'ear'):
        X, Y, Z = to_dog((x, y, z)); MX = abs(X - 8)
        if part == 'ear': t -= 1 if f != 'up' else 0
        if not e['name'].startswith('tail'):
            if n == 0: t += 1
            elif n == 1: t -= 1
        if e['name'] == 'snout':
            if f == 'north':
                if MX < 1.0 and 20.5 <= Y: return NOSEC[0]                                                  # nose: a small block at the top front
                t = 3
            if f == 'up':
                if MX < 1.0 and Z < -2.0: return NOSEC[1]                                                     # nose wraps over the top edge
                t = 4
        if e['name'] == 'head' and f == 'north' and 1.25 <= MX < 2.5 and 22.5 <= Y < 23.75:
            return EYEC[1] if Y >= 23.5 else EYEC[0]                                                         # eyes
        if 'paw' in e['name'] and f == 'north' and Y < 2.5 and (abs(MX - 1.75 - (8 - 8)) < 0.15 or abs(MX - 3.0) < 0.15 or abs(MX - 2.5) < 0.13): t = 0
        return FURP[max(0, min(4, t))]
    if part == 'collar':
        if e['name'] == 'tag':
            return GOLDP[4] if (f == 'north' and abs(x - 8) < 0.5 and j < h // 2) else GOLDP[3]
        if n == 0: t += 1
        return EMERP[max(0, min(4, t))]                     # emerald collar, gold tag
    if part == 'gold':
        if n == 0: t += 1
        elif n == 1 and f != 'up': t -= 1
        return GOLDP[max(0, min(4, t))]
    if part == 'ameth':
        if not side: return AMEP[2]
        hz = abs(x - 8) if f in ('north', 'south') else abs(z - 5)
        d = max(hz / 3.0, abs(y + 5) / 2.25)                     # gem spans 6 x 4.5 units
        return AMEP[4] if d < 0.3 else AMEP[3] if d < 0.6 else AMEP[2] if d < 0.85 else AMEP[1]
    if part == 'stone':
        if e['name'] == 'plinth' and side:
            a = abs(x - 8) if f in ('north', 'south') else abs(z - 5); b = y + 9
            if b < 1: return STONP[1]
            if b >= 7: return STONP[3]
            if a < 4 and (a >= 3 or b < 1.75 or b >= 6.25): return STONP[0]                       # recess round the gem
            dd = max(abs(a - 8.5), abs(b - 4))
            if 1.5 <= dd < 2: return STONP[1]                                                     # carved square motif
            if dd < 0.75: return STONP[1]
            if a >= 12.25: return STONP[2]
            return STONP[3 if n == 0 else 2]
        if f == 'up':
            edge = e['name'] == 'plinth' and (abs(x - 8) > 12 or abs(z - 5) > 12)
            return STONP[2 if edge else (4 if n == 0 else 3)]
        return STONP[max(0, min(4, t))]
    return FURP[2]
for (ei, f) in list(tex):
    e = E[ei]; w, h = face_size(e, f)
    tex[(ei, f)] = np.array([[paint(e, f, i, j, w, h) for i in range(w)] for j in range(h)], np.float32)

# ---- atlas
rects = [(ei, f, *face_size(E[ei], f), np.clip(tex[(ei, f)], 0, 255).astype(np.uint8)) for ei in range(len(E)) for f in FACES]
for N in (128, 256, 512, 1024):
    x = y = shelf = 0; pos = {}; ok = True
    for k in sorted(range(len(rects)), key=lambda k: (-rects[k][3], -rects[k][2])):
        cw, ch = rects[k][2] + 2, rects[k][3] + 2
        if x + cw > N: x = 0; y += shelf; shelf = 0
        if y + ch > N: ok = False; break
        pos[k] = (x, y); x += cw; shelf = max(shelf, ch)
    if ok: break
atlas = np.zeros((N, N, 4), np.uint8); uv = {}
for k, (ei, f, w, h, arr) in enumerate(rects):
    x0, y0 = pos[k][0] + 1, pos[k][1] + 1
    atlas[y0:y0 + h, x0:x0 + w, :3] = arr; atlas[y0:y0 + h, x0:x0 + w, 3] = 255
    atlas[y0 - 1, x0:x0 + w] = atlas[y0, x0:x0 + w]; atlas[y0 + h, x0:x0 + w] = atlas[y0 + h - 1, x0:x0 + w]
    atlas[y0 - 1:y0 + h + 1, x0 - 1] = atlas[y0 - 1:y0 + h + 1, x0]; atlas[y0 - 1:y0 + h + 1, x0 + w] = atlas[y0 - 1:y0 + h + 1, x0 + w - 1]
    uv[(ei, f)] = (x0, y0, x0 + w, y0 + h)

# ---- renders: (1) through the concept camera itself, (2) ordinary orbit views
def render_concept_cam():
    out = REF.copy() * 0 + np.array([112, 104, 100], np.float32)
    hit = idbuf >= 0
    for fid, (ei, f) in enumerate(faces):
        m = idbuf == fid
        if not m.any(): continue
        e = E[ei]; w, h = face_size(e, f)
        p00 = np.array(texel_pos(e, f, -.5, -.5)); p10 = np.array(texel_pos(e, f, w - .5, -.5)); p01 = np.array(texel_pos(e, f, -.5, h - .5))
        q00, q10, q01 = map(np.array, (proj(p00), proj(p10), proj(p01)))
        Mi = np.linalg.inv(np.column_stack([q10 - q00, q01 - q00]))
        uvw = Mi @ np.stack([xx[m] + .5 - q00[0], yy[m] + .5 - q00[1]])
        ii = np.clip((uvw[0] * w).astype(int), 0, w - 1); jj = np.clip((uvw[1] * h).astype(int), 0, h - 1)
        u0, v0 = uv[(ei, f)][:2]
        out[m] = atlas[v0 + jj, u0 + ii, :3] * SHADE[f]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))

AXD = {'north': (2, -1), 'south': (2, 1), 'west': (0, -1), 'east': (0, 1), 'down': (1, -1), 'up': (1, 1)}
def render(yaw, pitch, ppu=12, W=26, Hh=34, center=(8, 11, 6), bg=(112, 104, 100)):
    th, ph = math.radians(yaw), math.radians(pitch)
    fw = -np.array([math.sin(th) * math.cos(ph), math.sin(ph), -math.cos(th) * math.cos(ph)])
    rr = np.cross(fw, [0, 1, 0]); rr /= np.linalg.norm(rr); up = np.cross(rr, fw)
    wpx, hpx = int(W * ppu), int(Hh * ppu)
    sx = (np.arange(wpx) + .5) / ppu - W / 2; sy = Hh / 2 - (np.arange(hpx) + .5) / ppu
    P = ((np.array(center) - fw * 80)[None, None, :] + rr[None, None, :] * sx[None, :, None] + up[None, None, :] * sy[:, None, None]).reshape(-1, 3)
    best = np.full(len(P), 1e18); out = np.tile(np.array(bg, np.float32), (len(P), 1))
    for ei, e in enumerate(E):
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
            u0, v0 = uv[(ei, fc)][:2]
            out[m] = atlas[v0 + jj, u0 + ii, :3].astype(np.float32) * SHADE[fc]; best[m] = t[m]
    return Image.fromarray(out.reshape(hpx, wpx, 3).clip(0, 255).astype(np.uint8))

if __name__ == '__main__':
    hero = render(26, 11, ppu=19, W=34, Hh=50, center=(8, 12.5, 5))
    ref = Image.fromarray(REF.astype(np.uint8)).resize((int(608 * hero.height / 912), hero.height), Image.LANCZOS)
    cmp_ = Image.new('RGB', (ref.width + hero.width, hero.height), (112, 104, 100)); cmp_.paste(ref, (0, 0)); cmp_.paste(hero, (ref.width, 0))
    cmp_.save(OUT / f'shrine-compare-{TAG}.png')
    views = [render(y, p, ppu=8, W=34, Hh=50, center=(8, 12.5, 5)) for y, p in ((0, 8), (26, 17), (90, 6), (154, 17), (200, 30))]
    sheet = Image.new('RGB', (sum(v.width for v in views), views[0].height), (112, 104, 100)); x = 0
    for v in views: sheet.paste(v, (x, 0)); x += v.width
    sheet.save(OUT / f'shrine-views-{TAG}.png')
    # overlap audit
    AXL = {'north': (2, -1), 'south': (2, 1), 'west': (0, -1), 'east': (0, 1), 'down': (1, -1), 'up': (1, 1)}
    import itertools
    bad = []
    for a_, b_ in itertools.combinations(E, 2):
        if 'rot' in a_ or 'rot' in b_: continue
        if a_.get('pose') is not None and b_.get('pose') is not None and a_['pose'] != b_['pose']: continue
        for f in FACES:
            ax, sg = AXL[f]
            ca = a_['to'][ax] if sg > 0 else a_['frm'][ax]; cb = b_['to'][ax] if sg > 0 else b_['frm'][ax]
            if ca != cb: continue
            ov = 1
            for q in range(3):
                if q != ax: ov *= max(0, min(a_['to'][q], b_['to'][q]) - max(a_['frm'][q], b_['frm'][q]))
            if ov > 0: bad.append((a_['name'], b_['name'], f))
    ys = [v for e in E for v in (e['frm'][1], e['to'][1])]
    print('elements', len(E), 'atlas', N, 'height', max(ys) - min(ys), 'overlaps', bad[:8] or 0)

# ---- export as a Minecraft item model (Y shifted so the 43.5-unit height fits Java's -16..32 limit)
if __name__ == '__main__' and not COMBINE:
    NAME = 'ivy_shrine_simple'
    SH = 32 - max(e['to'][1] for e in E)
    ybot = min(e['frm'][1] for e in E) + SH
    disp = {'fixed': {'rotation': [-90, 0, 0], 'translation': [0, 0, round(2 * (ybot - 8), 3)], 'scale': [2, 2, 2]},
            'gui': {'rotation': [25, 225, 0], 'translation': [0, -1.5, 0], 'scale': [0.3, 0.3, 0.3]},
            'ground': {'translation': [0, 3, 0], 'scale': [0.25, 0.25, 0.25]}}
    els = []
    for ei, e in enumerate(E):
        a_ = list(e['frm']); b_ = list(e['to']); a_[1] += SH; b_[1] += SH
        els.append({'name': e['name'], 'from': a_, 'to': b_,
                    'faces': {f: {'uv': [round(v * 16 / N, 6) for v in uv[(ei, f)]], 'texture': '#atlas'} for f in FACES}})
    model = {'credit': 'Ivy shrine (simple) - Realms Beyond; projected from the concept art', 'texture_size': [N, N],
             'textures': {'atlas': 'realm:item/decorations/' + NAME, 'particle': 'realm:item/decorations/' + NAME},
             'elements': els, 'display': disp}
    ex = OUT / 'export'; ex.mkdir(exist_ok=True)
    buf = io.BytesIO(); Image.fromarray(atlas, 'RGBA').save(buf, 'PNG', optimize=True); png = buf.getvalue()
    (ex / f'{NAME}.png').write_bytes(png)
    (ex / f'{NAME}.json').write_text(json.dumps(model, indent=2) + '\n')
    (ex / f'{NAME}_item.json').write_text(json.dumps({'model': {'type': 'minecraft:model', 'model': 'realm:item/decorations/' + NAME}}, indent=2) + '\n')
    bb = {'meta': {'format_version': '4.10', 'model_format': 'java_block', 'box_uv': False}, 'name': 'Ivy Shrine (simple)',
          'resolution': {'width': N, 'height': N},
          'elements': [{'name': d['name'], 'from': d['from'], 'to': d['to'], 'type': 'cube', 'uuid': str(uuid.uuid4()), 'box_uv': False,
                        'origin': [8, 0, 8], 'faces': {f: {'uv': list(uv[(ei, f)]), 'texture': 0} for f in FACES}} for ei, d in enumerate(els)],
          'textures': [{'name': NAME + '.png', 'id': '0', 'uuid': str(uuid.uuid4()), 'width': N, 'height': N, 'uv_width': N, 'uv_height': N,
                        'particle': True, 'source': 'data:image/png;base64,' + base64.b64encode(png).decode()}], 'display': disp}
    bb['outliner'] = [el['uuid'] for el in bb['elements']]
    (ex / 'Ivy-Shrine-Simple.bbmodel').write_text(json.dumps(bb, indent=2))
    print('export: shift', SH, 'y', ybot, '..', 32, '| range ok', all(-16 <= v <= 32 for d in els for v in d['from'] + d['to']),
          '| uv ok', all(0 <= v <= 16 for d in els for fc in d['faces'].values() for v in fc['uv']))

# ---- combined export: the detailed Ivy shrine's architecture + this dog (two textures)
if __name__ == '__main__' and COMBINE:
    NAME = 'ivy_shrine_simple'
    det = json.load(open(os.environ['DETAILED']))
    arch = [e for e in det['elements'] if not e['name'].startswith('Ivy ')]
    GOLD_NAMES = ('gold capital', 'column shaft', 'roof slab', 'roof tier', 'roof upper tier', 'gold finial', 'finial amethyst')
    arch = [e for e in det['elements'] if not e['name'].startswith('Ivy ') and not e['name'].startswith(GOLD_NAMES)]
    def el(ei, e):
        d = {'name': e['name'] if e['cam'] == 'shrine' else 'Ivy ' + e['name'], 'from': e['frm'], 'to': e['to']}
        if 'rot' in e: d['rotation'] = e['rot']
        d['faces'] = {f: {'uv': [round(v * 16 / N, 6) for v in uv[(ei, f)]], 'texture': '#dog'} for f in FACES}
        return d
    dog = [el(ei, e) for ei, e in enumerate(E) if 'pose' not in e]
    DROP = -4                                                   # room for the taller roof inside Java's -16..32
    import copy
    arch = copy.deepcopy(arch)
    def drop(els_):
        for d_ in els_:
            d_['from'] = [d_['from'][0], d_['from'][1] + DROP, d_['from'][2]]; d_['to'] = [d_['to'][0], d_['to'][1] + DROP, d_['to'][2]]
            if 'rotation' in d_: d_['rotation']['origin'][1] += DROP
    drop(arch); drop(dog)
    disp = copy.deepcopy(det['display'])
    disp['fixed']['translation'][2] += 2 * DROP
    for k_ in ('gui', 'ground'):
        if k_ in disp:
            sc = disp[k_].get('scale', [1, 1, 1])[1]; tr = disp[k_].setdefault('translation', [0, 0, 0]); tr[1] = round(tr[1] - DROP * sc, 3)
    det = dict(det, display=disp)
    poses = {p_: [el(ei, e) for ei, e in enumerate(E) if e.get('pose') == p_] for p_ in range(3)}
    for p_ in poses: drop(poses[p_])
    tex_slots = {'atlas': det['textures']['atlas'], 'dog': 'realm:item/decorations/' + NAME, 'particle': det['textures']['atlas']}
    model = {'credit': 'Ivy shrine (simple dog) - Realms Beyond', 'texture_size': det['texture_size'], 'textures': tex_slots,
             'elements': arch + dog, 'display': det['display']}
    ex = OUT / 'export-combined'; ex.mkdir(exist_ok=True)
    buf = io.BytesIO(); Image.fromarray(atlas, 'RGBA').save(buf, 'PNG', optimize=True)
    (ex / f'{NAME}.png').write_bytes(buf.getvalue())
    (ex / f'{NAME}.json').write_text(json.dumps(model, indent=2) + '\n')
    for p_, els_ in poses.items():
        (ex / f'{NAME}_tail_{p_}.json').write_text(json.dumps({'texture_size': det['texture_size'], 'textures': tex_slots,
                                                                 'elements': els_, 'display': det['display']}, indent=2) + '\n')
    seq = [1, 2, 2, 1, 0, 0, 1, 2, 1, 0]
    tail = lambda p_: {'type': 'minecraft:model', 'model': f'realm:item/decorations/{NAME}_tail_{p_}'}
    item = {'model': {'type': 'minecraft:composite', 'models': [
        {'type': 'minecraft:model', 'model': 'realm:item/decorations/' + NAME},
        {'type': 'minecraft:select', 'property': 'minecraft:local_time', 'pattern': 'S',
         'cases': [{'when': [str(d_) for d_ in range(10) if seq[d_] == p_], 'model': tail(p_)} for p_ in range(3)], 'fallback': tail(1)}]}}
    (ex / f'{NAME}_item.json').write_text(json.dumps(item, indent=2) + '\n')
    dog = dog + [e for p_ in poses for e in poses[p_]]
    # audit against the architecture: same-direction coplanar overlaps, Java limits
    AXL = {'north': (2, -1), 'south': (2, 1), 'west': (0, -1), 'east': (0, 1), 'down': (1, -1), 'up': (1, 1)}
    bad = []
    for a_ in dog:
        if 'rotation' in a_: continue
        for b_ in arch:
            for f in FACES:
                ax, sg = AXL[f]
                ca = a_['to'][ax] if sg > 0 else a_['from'][ax]; cb = b_['to'][ax] if sg > 0 else b_['from'][ax]
                if ca != cb: continue
                ov = 1
                for q in range(3):
                    if q != ax: ov *= max(0, min(a_['to'][q], b_['to'][q]) - max(a_['from'][q], b_['from'][q]))
                if ov > 0: bad.append((a_['name'], b_['name'], f))
    inter = [(a_['name'], b_['name']) for a_ in dog for b_ in arch
             if all(min(a_['to'][q], b_['to'][q]) - max(a_['from'][q], b_['from'][q]) > 0 for q in range(3)) and not b_['name'].startswith('plinth')]
    lo = [min(e['from'][q] for e in dog) for q in range(3)]; hi = [max(e['to'][q] for e in dog) for q in range(3)]
    print('combined:', len(arch), 'shrine parts +', len(dog), 'dog cubes | dog bounds', lo, hi)
    print('coplanar overlaps:', bad or 0, '| dog intersecting columns/feet:', inter or 0)
    print('range ok', all(-16 <= v <= 32 for e in arch + dog for v in e['from'] + e['to']))
