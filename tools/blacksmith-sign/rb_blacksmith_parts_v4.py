#!/usr/bin/env python3
"""Realms Beyond: Blacksmith sign 3D parts, v4.

Run after rb_blacksmith_v3_square.py. Turns the v2/v3 model into v4:
  * Raised frame: four strips stand 0.5 units proud of both faces of the board,
    so the lettering panel sits recessed. The board keeps only its front and
    back faces; the strips provide the edges.
  * The two solid hanger blocks become vanilla-style crossed chain planes
    (rotated 45 deg on y), drawn in deepslate tones.
  * The diagonal brace is 1.5 units thick instead of 1. Its faces sit 0.25 inside
    the bracket's faces, so nothing is coplanar and nothing z-fights.
Texture additions (free atlas space, nothing existing is moved):
  * frame wood for the strip edges: px 0-79 x 200-251
  * chain sprites, 8x12 px each: px 96-103 (plane A) and 104-111 (plane B) x 128-139
  * a 1px shadow along the top of the recessed panel (board row 4)
Running it again on its own output is a no-op.

Usage: rb_blacksmith_parts_v4.py <model.json> <texture.png>   (edits both in place)
"""
import json
import random
import sys
from PIL import Image

U = 8.0    # px per uv unit horizontally (128 / 16)
V = 16.0   # px per uv unit vertically (256 / 16)
BX0, BX1, BY0, BY1 = -16, 4, 4, 17   # board extent in model units
ZF, ZB = 7, 9                         # board front/back faces
LIP = 0.5                             # frame height above the board faces
FW_Y = 200                            # frame wood region top row (px)
CH_X, CH_Y = 96, 128                  # chain sprites (px)
FRAME_PAL = [(47, 33, 25), (44, 30, 22), (49, 35, 27), (41, 27, 19)]
CHAIN = {'m': (66, 71, 80), 'h': (92, 98, 110), 'd': (40, 44, 52)}


def r(v):
    return round(v, 6)


def board_uv(face, x1, y1, x2, y2):
    """UV on the board artwork for a sub-rectangle of the board front (north) or back (south)."""
    v1, v2 = (BY1 - y2) * 0.25, (BY1 - y1) * 0.25
    if face == 'north':
        u1, u2 = (BX1 - x2) / 2, (BX1 - x1) / 2
    else:
        u1, u2 = (x1 - BX0) / 2, (x2 - BX0) / 2
    return [r(u1), r(v1), r(u2), r(v2)]


def wood_uv(w, h):
    """UV for a w x h (model units) patch of the frame wood region, at 4 px per unit."""
    return [0, r(FW_Y / V), r(w * 4 / U), r(FW_Y / V + h * 4 / V)]


def face(uv):
    return {'uv': uv, 'texture': '#sign'}


def strip(name, x1, y1, x2, y2, outer):
    z1, z2 = ZF - LIP, ZB + LIP
    dz = z2 - z1
    f = {'north': face(board_uv('north', x1, y1, x2, y2)),
         'south': face(board_uv('south', x1, y1, x2, y2))}
    for d in outer:
        if d in ('up', 'down'):
            f[d] = face(wood_uv(x2 - x1, dz))
        else:
            f[d] = face(wood_uv(dz, y2 - y1))
    return {'name': name, 'from': [x1, y1, z1], 'to': [x2, y2, z2], 'faces': f}


def chain(name, cx):
    ua = [r(CH_X / U), r(CH_Y / V), r((CH_X + CW) / U), r((CH_Y + 12) / V)]
    ub = [r((CH_X + CW) / U), r(CH_Y / V), r((CH_X + 2 * CW) / U), r((CH_Y + 12) / V)]
    rot = {'origin': [cx, 18.5, 8], 'axis': 'y', 'angle': 45}
    a = {'name': name + '_a', 'from': [cx - 1, 17, 8], 'to': [cx + 1, 20, 8],
         'shade': False, 'rotation': rot, 'faces': {'north': face(ua), 'south': face(ua)}}
    b = {'name': name + '_b', 'from': [cx, 17, 7], 'to': [cx, 20, 9],
         'shade': False, 'rotation': rot, 'faces': {'east': face(ub), 'west': face(ub)}}
    return [a, b]


def same(e, frm, to):
    return e.get('from') == frm and e.get('to') == to


def edit_model(path):
    m = json.load(open(path))
    els = m['elements']
    if any(e.get('name') == 'frame_top' for e in els):
        print('model already v4: unchanged')
        return
    out = []
    for e in els:
        if same(e, [-16, 4, 7], [4, 17, 9]):
            e = {'name': 'board', 'from': e['from'], 'to': e['to'],
                 'faces': {k: e['faces'][k] for k in ('north', 'south')}}
            out.append(e)
            out += [
                strip('frame_top', BX0, BY1 - 1, BX1, BY1, ('up', 'down', 'east', 'west')),
                strip('frame_bottom', BX0, BY0, BX1, BY0 + 1, ('up', 'down', 'east', 'west')),
                strip('frame_left', BX0, BY0 + 1, BX0 + 1, BY1 - 1, ('east', 'west')),
                strip('frame_right', BX1 - 1, BY0 + 1, BX1, BY1 - 1, ('east', 'west')),
            ]
        elif same(e, [-12, 17, 7], [-10, 20, 9]):
            out += chain('chain_left', -11)
        elif same(e, [-1, 17, 7], [1, 20, 9]):
            out += chain('chain_right', 0)
        elif same(e, [-1, 21, 7.5], [8, 22, 8.5]):
            v0 = 4.0
            v1 = r(v0 + 1.5 * 4 / V)
            e['name'] = 'brace'
            e['from'], e['to'] = [-1, 21, 7.25], [8, 22.5, 8.75]
            for k, fc in e['faces'].items():
                w = 0.75 if k in ('east', 'west') else 4.5
                fc['uv'] = [0, v0, w, v1]
            out.append(e)
        else:
            out.append(e)
    m['elements'] = out
    with open(path, 'w') as fh:
        json.dump(m, fh, indent=2)
        fh.write('\n')
    print(f'model: {len(els)} -> {len(out)} elements')


# Chain sprites, 8 x 12 px each (2px-thick links). Links L1 (rows 0-4) and L3 (rows 7-11) face
# plane A; L2 (rows 3-8) faces plane B. Each plane shows the other links edge-on.
CHAIN_A = [".hmmmmd.",
           "hm....md",
           "hm....md",
           "hm....md",
           ".hmmmmd.",
           "...md...",
           "...md...",
           ".hmmmmd.",
           "hm....md",
           "hm....md",
           "hm....md",
           ".hmmmmd."]
CHAIN_B = ["...md...",
           "...md...",
           "...md...",
           ".hmmmmd.",
           "hm....md",
           "hm....md",
           "hm....md",
           "hm....md",
           ".hmmmmd.",
           "...md...",
           "...md...",
           "...md..."]
CW = 8   # chain sprite width in px (2 model units)


def edit_texture(path):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    # Frame wood: 4x4 cells in the frame tones, fixed seed so re-runs match.
    rng = random.Random(1474)
    for cy in range(FW_Y, FW_Y + 52, 4):
        for cx in range(0, 80, 4):
            c = rng.choice(FRAME_PAL) + (255,)
            for j in range(4):
                for i in range(4):
                    px[cx + i, cy + j] = c
    for k, spr in ((0, CHAIN_A), (CW, CHAIN_B)):
        for y, row in enumerate(spr):
            for x, ch in enumerate(row):
                px[CH_X + k + x, CH_Y + y] = (CHAIN[ch] + (255,)) if ch != '.' else (0, 0, 0, 0)
    # Panel shadow under the raised top strip: board row 4 = row 5 darkened.
    for x in range(4, 76):
        p = px[x, 5]
        px[x, 4] = (round(p[0] * 0.78), round(p[1] * 0.78), round(p[2] * 0.78), 255)
    im.save(path)
    print('texture: frame wood, chain sprites, panel shadow written')


if __name__ == '__main__':
    edit_model(sys.argv[1])
    edit_texture(sys.argv[2])
