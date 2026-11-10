#!/usr/bin/env python3
"""Realms Beyond: ALL-CAPS test versions of the Blacksmith and Clocktower signs.

A variant of rb_clocktower_sign.py (which stays as the lowercase generator). Both
signs are rebuilt from the lowercase Blacksmith sign's model and texture: same
bracket, spike, brace, chains, colours, raised frame and full-bright lettering.
  * capitals in the same v3 square font: 14 rows tall, 2px strokes, 2px counters, 2px gaps
  * "CLOCKTOWER" is 80 px and "BLACKSMITH" 77 px, so both boards are 23 x 13 units
    (92 x 52 px), x -18..5 (the Blacksmith board was 20 wide, the Clocktower 22)
  * emblem: the clock, or the anvil copied from the Blacksmith texture

Usage: rb_sign_caps.py <lowercase_blacksmith_model.json> <lowercase_blacksmith.png>
                       <out_model.json> <out.png> <WORD> <clock|anvil> <texture_id>
The lowercase originals are in builds/sign-caps-backups/. Re-running gives the same result.
"""
import copy
import json
import random
import sys
from PIL import Image

# ---- atlas (128 x 256: 8 px per u unit, 16 px per v unit) -------------------
TW, TH = 128, 256
BW, BH = 92, 52                     # board face
BOARD = (0, 0)
OVL = (0, 72)
DEEP = (0, 144)                     # copy of the Blacksmith atlas rows 64-107
FW = (0, 188)                       # frame-edge wood, 88 x 44
CHAIN = (96, 0)                     # copy of the Blacksmith chain sprites
FRAME = 4
BOARD_R = 5                         # board right edge (1 unit from the wall post); it grows leftwards

GLYPH = (255, 255, 249, 255)
EMBLEM = (239, 232, 211, 255)       # the anvil's colour
OUTLINE = (28, 21, 17, 255)
PANEL = [(70, 48, 34, 255)] * 5 + [(67, 45, 31, 255)] * 3 + [(72, 50, 36, 255)] * 3
SEAM = (64, 42, 28, 255)
BORDER = [(47, 33, 25, 255), (44, 30, 22, 255), (49, 35, 27, 255)]
BORDER_SEAM = (41, 27, 19, 255)
FRAME_WOOD = BORDER * 2 + [BORDER_SEAM]

EMBLEM_TOP = 7                      # rows 7-20, as the anvil
LINES = [("CLOCKTOWER", 26)]       # cap top row (set from the command line)
EMBLEM_KIND = "clock"
GAP = 2

# Capitals, 14 rows each: 2px strokes, 2px counters, square corners.
G = {
 'A': ["######", "######"] + ["##..##"] * 4 + ["######", "######"] + ["##..##"] * 6,
 'B': ["######", "######"] + ["##..##"] * 4 + ["#####.", "#####."] + ["##..##"] * 4 + ["######", "######"],
 'C': ["######", "######"] + ["##...."] * 10 + ["######", "######"],
 'E': ["#####", "#####"] + ["##..."] * 4 + ["####.", "####."] + ["##..."] * 4 + ["#####", "#####"],
 'H': ["##..##"] * 6 + ["######", "######"] + ["##..##"] * 6,
 'I': ["##"] * 14,
 'K': ["##..##"] * 4 + ["##.##.", "##.##.", "####..", "####..", "##.##.", "##.##."] + ["##..##"] * 4,
 'L': ["##..."] * 12 + ["#####", "#####"],
 'M': ["####..####", "##########"] + ["##..##..##"] * 12,
 'O': ["######", "######"] + ["##..##"] * 10 + ["######", "######"],
 'R': ["######", "######"] + ["##..##"] * 4 + ["######", "######", "####..", "####..", "##.##.", "##.##.", "##..##", "##..##"],
 'S': ["######", "######"] + ["##...."] * 4 + ["######", "######"] + ["....##"] * 4 + ["######", "######"],
 'T': ["######", "######"] + ["..##.."] * 12,
 'W': ["##..##..##"] * 12 + ["##########", "####..####"],
}

# Clock emblem, 14 x 14: a disc with the hands cut out. The cut-outs get the
# dark outline colour, so the hands read dark on the light face (
# long hand at 12, short hand at 3) and
# 2x2 hour ticks at 6 and 9.
CLOCK = [
 "....######....",
 "..##########..",
 ".#####..#####.",
 ".#####..#####.",
 "######..######",
 "######..######",
 "##..##....####",
 "##..##....####",
 "##############",
 "##############",
 ".#####..#####.",
 ".#####..#####.",
 "..##########..",
 "....######....",
]


def uv(x0, y0, x1, y1):
    return [x0 / 8, y0 / 16, x1 / 8, y1 / 16]


def wood(img):
    """Board face (4x4 cells, plank seams every 5 cells) and frame-edge wood."""
    rnd = random.Random(272)
    px = img.load()
    cols, rows = BW // 4, BH // 4
    for cy in range(rows):
        seam = cy % 5 == 0 and 0 < cy < rows - 1
        for cx in range(cols):
            edge = cx in (0, cols - 1) or cy in (0, rows - 1)
            if edge:
                c = BORDER_SEAM if seam else rnd.choice(BORDER)
            else:
                c = SEAM if seam else rnd.choice(PANEL)
            for j in range(4):
                for i in range(4):
                    px[BOARD[0] + cx * 4 + i, BOARD[1] + cy * 4 + j] = c
    # 1 px panel shadow under the top frame strip.
    for x in range(FRAME, BW - FRAME):
        r, g, b, a = px[x, FRAME]
        px[x, FRAME] = (max(0, r - 15), max(0, g - 11), max(0, b - 7), a)
    for cy in range((BH - 8) // 4):
        for cx in range(BW // 4):
            c = rnd.choice(FRAME_WOOD)
            for j in range(4):
                for i in range(4):
                    px[FW[0] + cx * 4 + i, FW[1] + cy * 4 + j] = c


def text_ink(word, top):
    for ch in word:
        assert len(G[ch]) == 14 and len({len(r) for r in G[ch]}) == 1, ch
    widths = [len(G[c][0]) for c in word]
    total = sum(widths) + GAP * (len(word) - 1)
    x = FRAME + (BW - 2 * FRAME - total) // 2
    x0 = x
    ink = set()
    for ch, w in zip(word, widths):
        for r, row in enumerate(G[ch]):
            for c, v in enumerate(row):
                if v == '#':
                    ink.add((x + c, top + r))
        x += w + GAP
    return ink, x0, total


ANVIL = None                        # set in main(): anvil pixels from the Blacksmith overlay


def emblem_ink():
    if EMBLEM_KIND == 'anvil':
        xs = [x for x, _ in ANVIL]
        x0 = (BW - (max(xs) - min(xs) + 1)) // 2 - min(xs)
        return {(x0 + x, y) for x, y in ANVIL}
    w = len(CLOCK[0])
    x0 = (BW - w) // 2
    return {(x0 + c, EMBLEM_TOP + r) for r, row in enumerate(CLOCK) for c, v in enumerate(row) if v == '#'}


def paint(img):
    px = img.load()
    glyphs = set()
    for word, top in LINES:
        ink, x0, total = text_ink(word, top)
        print(f'{word}: x {x0}..{x0 + total - 1} ({total} px), rows {top}..{top + 13}')
        glyphs |= ink
    clock = emblem_ink()
    for p in glyphs:
        px[OVL[0] + p[0], OVL[1] + p[1]] = GLYPH
    for p in clock:
        px[OVL[0] + p[0], OVL[1] + p[1]] = EMBLEM
    lit = glyphs | clock
    ring = set()
    for (x, y) in lit:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in lit:
                ring.add(q)
    for q in ring:
        assert FRAME < q[0] < BW - FRAME - 1 and FRAME < q[1] < BH - FRAME - 1, f'outline too close to frame at {q}'
        px[BOARD[0] + q[0], BOARD[1] + q[1]] = OUTLINE


def mirrored(el):
    """Place an element past x=-16 by defining its mirror and rotating 180 about y."""
    (x1, y1, z1), (x2, y2, z2) = el['from'], el['to']
    out = copy.deepcopy(el)
    out['from'] = [12 - x2, y1, 16 - z2]
    out['to'] = [12 - x1, y2, 16 - z1]
    swap = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'up', 'down': 'down'}
    faces = {}
    for d, f in el['faces'].items():
        f = dict(f)
        if d in ('up', 'down'):
            f['rotation'] = 180
        faces[swap[d]] = f
    out['faces'] = faces
    out['rotation'] = {'origin': [6, (y1 + y2) / 2, 8], 'axis': 'y', 'angle': 180}
    return out


# OVERLAY GAP: the full-bright lettering planes sit 1/8 unit in front of the board
# (was 1/64), so they don't z-fight it at a distance, especially with shaders.
def board_elements():
    L, R, B, T = BOARD_R - BW // 4, BOARD_R, 17 - BH // 4, 17
    face = uv(0, 0, BW, BH)
    fwud = uv(FW[0], FW[1], FW[0] + BW, FW[1] + 12)
    fwend = uv(FW[0], FW[1], FW[0] + 12, FW[1] + 4)
    fwside = uv(FW[0], FW[1], FW[0] + 12, FW[1] + BH - 8)
    ovl = uv(OVL[0], OVL[1], OVL[0] + BW, OVL[1] + BH)
    rowband = lambda y0, y1: uv(0, y0, BW, y1)
    colband = lambda x0, x1: uv(x0, FRAME, x1, BH - FRAME)
    t = '#sign'
    els = [
        {'name': 'board', 'from': [L, B, 7], 'to': [R, T, 9],
         'faces': {'north': {'uv': face, 'texture': t}, 'south': {'uv': face, 'texture': t}}},
        {'name': 'frame_top', 'from': [L, T - 1, 6.5], 'to': [R, T, 9.5],
         'faces': {'north': {'uv': rowband(0, 4), 'texture': t}, 'south': {'uv': rowband(0, 4), 'texture': t},
                   'up': {'uv': fwud, 'texture': t}, 'down': {'uv': fwud, 'texture': t},
                   'east': {'uv': fwend, 'texture': t}, 'west': {'uv': fwend, 'texture': t}}},
        {'name': 'frame_bottom', 'from': [L, B, 6.5], 'to': [R, B + 1, 9.5],
         'faces': {'north': {'uv': rowband(BH - 4, BH), 'texture': t}, 'south': {'uv': rowband(BH - 4, BH), 'texture': t},
                   'up': {'uv': fwud, 'texture': t}, 'down': {'uv': fwud, 'texture': t},
                   'east': {'uv': fwend, 'texture': t}, 'west': {'uv': fwend, 'texture': t}}},
        {'name': 'frame_left', 'from': [L, B + 1, 6.5], 'to': [L + 1, T - 1, 9.5],
         'faces': {'north': {'uv': colband(BW - 4, BW), 'texture': t}, 'south': {'uv': colband(0, 4), 'texture': t},
                   'east': {'uv': fwside, 'texture': t}, 'west': {'uv': fwside, 'texture': t}}},
        {'name': 'frame_right', 'from': [R - 1, B + 1, 6.5], 'to': [R, T - 1, 9.5],
         'faces': {'north': {'uv': colband(0, 4), 'texture': t}, 'south': {'uv': colband(BW - 4, BW), 'texture': t},
                   'east': {'uv': fwside, 'texture': t}, 'west': {'uv': fwside, 'texture': t}}},
        {'name': 'lettering_north', 'from': [L, B, 6.875], 'to': [R, T, 6.875], 'shade': False,
         'light_emission': 15, 'faces': {'north': {'uv': ovl, 'texture': t}}},
        {'name': 'lettering_south', 'from': [L, B, 9.125], 'to': [R, T, 9.125], 'shade': False,
         'light_emission': 15, 'faces': {'south': {'uv': ovl, 'texture': t}}},
    ]
    return [mirrored(e) if e['from'][0] < -16 else e for e in els]


def main(src_model, src_png, dst_model, dst_png, word, emblem, texture_id):
    global LINES, EMBLEM_KIND, ANVIL
    LINES, EMBLEM_KIND = [(word, 26)], emblem
    bs = json.load(open(src_model))
    old = Image.open(src_png).convert('RGBA')
    assert old.size == (TW, TH)
    opx = old.load()
    ANVIL = {(x, y) for x in range(80) for y in range(52) if opx[x, 144 + y] == EMBLEM}
    assert ANVIL, 'no anvil found in the Blacksmith overlay'
    img = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
    img.paste(old.crop((0, 64, 96, 108)), DEEP)
    img.paste(old.crop((96, 128, 112, 140)), CHAIN)
    wood(img)
    paint(img)
    img.save(dst_png)

    bracket, chains = [], []
    for e in bs['elements']:
        name = e.get('name', '')
        if name.startswith('chain_'):
            chains.append(e)
        elif name == 'brace' or (not name and 'light_emission' not in e):
            bracket.append(e)
    assert len(bracket) == 7 and len(chains) == 4, (len(bracket), len(chains))
    for e in bracket:                       # deepslate: old v 4..6.75 -> new rows 144..
        for f in e['faces'].values():
            u0, v0, u1, v1 = f['uv']
            assert 4 <= v0 and v1 <= 6.75
            f['uv'] = [u0, v0 + (DEEP[1] - 64) / 16, u1, v1 + (DEEP[1] - 64) / 16]
    # The wall post (x 6..8) had no east face, so it showed a hole whenever it
    # wasn't perfectly flush with a wall. Give it one, textured like its west face.
    posts = [e for e in bracket if e['from'][0] == 6 and e['to'][0] == 8]
    assert len(posts) == 1
    posts[0]['faces'].setdefault('east', dict(posts[0]['faces']['west']))
    mid = BOARD_R - BW / 8
    centre = {'left': mid - 5.5, 'right': mid + 5.5}     # chains 5.5 either side of the board centre
    for e in chains:
        side = e['name'].split('_')[1]
        dx = centre[side] - e['rotation']['origin'][0]
        e['from'][0] += dx
        e['to'][0] += dx
        e['rotation']['origin'][0] += dx
        for f in e['faces'].values():
            u0, v0, u1, v1 = f['uv']
            f['uv'] = [u0, v0 - 8, u1, v1 - 8]

    model = {
        'textures': {'sign': texture_id},
        'elements': board_elements() + bracket + chains,
        'display': {'gui': {'rotation': [12, 24, 0], 'translation': [4.5, -1, 0], 'scale': [0.42, 0.42, 0.42]}},
    }
    for e in model['elements']:
        for k in ('from', 'to'):
            assert all(-16 <= v <= 32 for v in e[k]), (e.get('name'), e[k])
    json.dump(model, open(dst_model, 'w'), indent=2)
    print(f'{len(model["elements"])} elements')


if __name__ == '__main__':
    main(*sys.argv[1:8])
