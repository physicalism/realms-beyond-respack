#!/usr/bin/env python3
"""Realms Beyond: long stag war banner (deep azure), animated.

2 x 5.6 blocks at native pixel density (1 texel = 1/16 block), hung from a
stripped-spruce pole with gold finials, placed in an invisible item frame like the
other banners (the frame goes on the block where the pole should be).

Art: gold border with corner flourishes, crown, the town's original banner stag at 2x,
fleur-de-lis, three-point dagged hem with gold fringe, faint lozenge damask.
Animation: 32 frames (3.2 s loop). Light/dark fold bands travel down the cloth (stronger
towards the hem) and the lower third sways sideways, so the tails flutter.

Usage: rb_war_banner.py <out_dir>   (writes texture, .mcmeta, model, item, preview.gif)
"""
import json
import math
import os
import sys
from PIL import Image

W, H = 34, 90                 # cloth texels
FW, FH = 64, 128              # one animation frame
N = 32                        # frames
FRAMETIME = 2                 # ticks per frame (3.2 s loop)
M = 3                         # transparent margin each side, room for the sway
CW = W + 2 * M                # cloth region width in the frame
HX = 44                       # hardware textures start here
NAME = 'banner_stag_war_azure'

FIELD = (34, 58, 116)
FIELD_DAMASK = (30, 51, 104)
SLEEVE = (24, 40, 82)
# The original banner stag's three golds, used for every gold on the banner.
GOLD = (225, 192, 87)
GOLD_HI = (247, 236, 121)
GOLD_LO = (199, 148, 72)
INK = (24, 18, 16)

STAG = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stag.txt')).read().split()

CROWN = [
 ".......#.......",
 "......###......",
 ".#.....#.....#.",
 "###...###...###",
 ".#...#####...#.",
 ".##.#######.##.",
 ".#############.",
 ".##.##.#.##.##.",
 ".#############.",
 "..###########..",
]
LAUREL = [
 ".....#.....",
 "....###....",
 "...#####...",
 "...#####...",
 ".#..###..#.",
 "###.###.###",
 "#.#######.#",
 "#...###...#",
 ".#.#####.#.",
 "..#######..",
 ".....#.....",
 "....###....",
 "...#.#.#...",
]
FLOURISH = [            # top-left corner; mirrored for top-right
 "####..",
 "#..#..",
 "#.##..",
 "#.....",
 ".#....",
 "..#...",
]
STAR = [
 "..#..",
 ".###.",
 "#####",
 ".###.",
 "..#..",
]

SLEEVE_ROWS = 6               # rows 0-5 wrap the pole
HEM_TOP, HEM_TIP = 78, 84     # dagged hem: notches at row 80, points at row 88


def hem(x):
    """Last cloth row in column x: three points at x 5, 16, 26."""
    centres = (W / 6 - 0.5, W / 2 - 0.5, 5 * W / 6 - 0.5)
    c = min(centres, key=lambda c: abs(x - c))
    return round(HEM_TIP - (HEM_TIP - HEM_TOP) * min(1, abs(x - c) / (W / 6)))


def base_art():
    """Static design: dict (x,y) -> (rgb, kind). kind: field/gold/ink/sleeve."""
    art = {}
    cloth = {(x, y) for x in range(W) for y in range(hem(x) + 1)}
    for (x, y) in cloth:
        if y < SLEEVE_ROWS:
            art[(x, y)] = (SLEEVE, 'field')
        elif ((x + y) % 8 == 0 or (x - y) % 8 == 0):
            art[(x, y)] = (FIELD_DAMASK, 'field')
        else:
            art[(x, y)] = (FIELD, 'field')
    # Edge: ink outline + gold border, following the silhouette (sides and hem).
    def out(q):
        return q not in cloth
    for (x, y) in cloth:
        if y < SLEEVE_ROWS:
            continue
        if y >= HEM_TOP - 1:
            # Dagged hem: a 2px gold band with no outline, so the fringe hangs cleanly.
            below1, below2 = out((x, y + 1)), out((x, y + 2))
            if below1 or x in (0, W - 1):
                art[(x, y)] = (GOLD_LO if below1 else INK, 'gold' if below1 else 'ink')
            elif below2 or x in (1, W - 2):
                art[(x, y)] = (GOLD, 'gold')
            continue
        n1 = [(x + 1, y), (x - 1, y), (x, y + 1)]
        n2 = [(x + 2, y), (x - 2, y), (x, y + 2), (x + 1, y + 1), (x - 1, y + 1)]
        if any(out(q) for q in n1):
            art[(x, y)] = (INK, 'ink')
        elif any(out(q) for q in n2):
            art[(x, y)] = (GOLD, 'gold')
    for x in range(W):           # hem line under the sleeve
        art[(x, SLEEVE_ROWS)] = (INK, 'ink')
        art[(x, SLEEVE_ROWS + 1)] = (GOLD_HI, 'gold')
        art[(x, SLEEVE_ROWS + 2)] = (GOLD_LO, 'gold')
        art[(x, SLEEVE_ROWS + 3)] = (INK, 'ink')
        art[(x, 2)] = (GOLD_LO, 'gold') if 0 < x < W - 1 else art[(x, 2)]
    for y in range(SLEEVE_ROWS):  # sleeve side edges
        art[(0, y)] = art[(W - 1, y)] = (INK, 'ink')

    emb = {}

    def stamp(pattern, ox, oy):
        ink = {(ox + c, oy + r) for r, row in enumerate(pattern) for c, v in enumerate(row) if v == '#'}
        for (x, y) in ink:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in ink and q in art:
                    emb[q] = (INK, 'ink')
        for (x, y) in ink:
            up, down = (x, y - 1) not in ink, (x, y + 1) not in ink
            emb[(x, y)] = (GOLD_HI if up else GOLD_LO if down else GOLD, 'gold')

    stamp(FLOURISH, 3, 11)
    stamp([r[::-1] for r in FLOURISH], W - 3 - 6, 11)
    stamp(CROWN, (W - 15) // 2, 11)
    # The town's original banner stag, at exactly 2x (each pixel a 2x2 block),
    # in its own three golds, with a 1px black outline like the other emblems.
    tone = {'h': GOLD_HI, '#': GOLD, 'd': GOLD_LO}
    ox, oy = (W - 2 * len(STAG[0])) // 2, 23
    stag = {}
    for r, row in enumerate(STAG):
        for c, ch in enumerate(row):
            if ch in tone:
                for i in range(2):
                    for j in range(2):
                        stag[(ox + 2 * c + i, oy + 2 * r + j)] = tone[ch]
    for (x, y) in stag:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in stag:
                emb[q] = (INK, 'ink')
    for p, c in stag.items():
        emb[p] = (c, 'gold')
    stamp(LAUREL, (W - 11) // 2, 59)
    # Fringe: gold tassels under the hem on alternate columns.
    for x in range(1, W - 1, 2):
        y0 = hem(x) + 1
        for i, c in enumerate((GOLD, GOLD, GOLD_LO)):
            art[(x, y0 + i)] = (c, 'fringe')
    return art, emb


def shade(rgb, q):
    k = 1 + 0.13 * q
    return tuple(max(0, min(255, round(v * k))) for v in rgb)


def frame(layers, t):
    art, emb = layers
    img = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
    px = img.load()
    ph = 2 * math.pi * t / N

    # Emblems move as one piece (no torn pixel art): each row in a feature uses
    # the sway of the feature's centre row.
    features = [(10, 22), (22, 56), (58, 73), (HEM_TOP - 1, H)]
    def rep(y):
        for a, b in features:
            if a <= y < b:
                return (a + b) // 2
        return y

    def sway_f(y):
        """Sideways sway: a wave travelling down the cloth, pinned at the pole."""
        a = 0.0 if y < 20 else min(1.0, (y - 20) / (H - 20)) ** 1.6 * 2.3
        return a * (math.sin(2 * math.pi * y / 70 - ph) + 0.25 * math.sin(4 * math.pi * y / 70 - 2 * ph + 1.1))

    def light(x, y, rgb):
        amp = 0.45 + 0.55 * y / H
        # Vertical folds whose light rolls downward and across.
        m = amp * (0.75 * math.sin(2 * math.pi * x / 14 + 2 * math.pi * y / 52 - ph)
                   + 0.25 * math.sin(2 * math.pi * x / 7 - 2 * math.pi * y / 90 - 2 * ph))
        q = 2 if m > 0.62 else 1 if m > 0.28 else -2 if m < -0.62 else -1 if m < -0.28 else 0
        return shade(rgb, q * 0.55)

    def put(tx, y, rgb):
        tx += M
        if 0 <= tx < CW:
            px[tx, y] = rgb + (255,)

    hem_rows = HEM_TOP - 1
    # Cloth rows sway one by one, so the edges ripple smoothly; the dagged hem
    # moves as one piece so its diagonals stay intact.
    def row_dx(y):
        return round(sway_f(y if y < hem_rows else (hem_rows + H) // 2))

    def draw_base(kinds):
        for y in range(H):
            dx = row_dx(y)
            for x in range(W):
                if (x, y) not in art:
                    continue
                rgb, kind = art[(x, y)]
                if kind not in kinds:
                    continue
                if kind == 'fringe':
                    # Tassels trail the hem and swing further at the tips.
                    tip = y - hem(x)
                    lag = sway_f(HEM_TOP + 6 + 3 * tip) - sway_f(HEM_TOP + 6)
                    put(x + dx + round(lag + 0.5 * tip / 3 * math.sin(2 * math.pi * x / 9 - ph + math.pi / 2)), y, rgb)
                    continue
                if kind != 'ink' and y >= SLEEVE_ROWS:
                    rgb = light(x, y, rgb)
                put(x + dx, y, rgb)

    draw_base(('field',))
    # Emblems float on the cloth, each moving as one piece.
    for (x, y), (rgb, kind) in emb.items():
        dx = round(sway_f(rep(y)))
        if kind != 'ink':
            rgb = light(x, y, rgb)
        put(x + dx, y, rgb)
    # Border, hem and fringe go on top, so the edge always stays clean.
    draw_base(('gold', 'ink', 'fringe'))
    hardware(px)
    return img


def hardware(px):
    """Static pole and finial textures at x HX-63 of each frame."""
    # Stripped spruce: warm mid-brown with long grain streaks along the pole.
    base = [(115, 87, 53), (122, 93, 57), (108, 81, 49), (128, 98, 60)]
    for y in range(8):
        for x in range(HX, 64):
            c = base[(y * 7 + ((x - HX) // 5) * 3 + (x * y) % 3) % 4] if 0 < y < 7 else (86, 64, 38)
            if y in (2, 5) and (x - HX + y) % 7 < 4:
                c = (97, 72, 43)                      # grain line
            px[x, y] = c + (255,)
    for y in range(8, 16):
        for x in range(HX, HX + 8):
            c = GOLD_HI if y < 10 else GOLD_LO if y > 13 else GOLD
            if x in (HX, HX + 7):
                c = GOLD_LO
            px[x, y] = c + (255,)


def u(px_x):
    return px_x * 16 / FW


def v(px_y):
    return px_y * 16 / FH


WALL_Z = round(8 + 1 / (2 * 1.75), 4)   # model z of the wall plane (translation z -1, scale 3.5 x 0.5)


def model():
    """Item frames (invisible) centre the item ON the wall plane, scaled x2 here
    (fixed 4 x frame 0.5); the outward side is -z. The fixed translation moves
    everything 1/16 block off the wall so the cloth can't z-fight the stone."""
    t = '#0'
    cloth = [u(0), v(0), u(CW), v(H)]
    wood = lambda w: [u(HX), v(0), u(HX + w), v(8)]
    gold = [u(HX), v(8), u(HX + 8), v(16)]
    half = M / 2                         # 1 texel = 0.5 units
    els = [
        {'name': 'cloth', 'from': [8 - W / 4 - half, -16, 8], 'to': [8 + W / 4 + half, -16 + H / 2, 8],
         'faces': {'north': {'uv': cloth, 'texture': t}, 'south': {'uv': cloth, 'texture': t}}},
    ]
    # Pole (centre y 28): back face sits exactly on the wall (model z WALL_Z). Textured
    # from this banner's own atlas (stripped-spruce colours): a model can't mix the
    # banner's item-atlas texture with a vanilla block texture.
    els.append({'name': 'pole', 'from': [8 - W / 4 - 2, 27.25, WALL_Z - 1.5], 'to': [8 + W / 4 + 2, 28.75, WALL_Z],
                'faces': {d: {'uv': wood(20), 'texture': t} for d in ('north', 'south', 'up', 'down')}})
    for name, x0 in (('finial_left', 8 - W / 4 - 3.5), ('finial_right', 8 + W / 4 + 2)):
        els.append({'name': name, 'from': [x0, 27, WALL_Z - 1.9], 'to': [x0 + 1.5, 29, WALL_Z],
                    'faces': {d: {'uv': gold, 'texture': t} for d in ('north', 'south', 'up', 'down', 'east', 'west')}})
    return {
        'credit': 'Realms Beyond',
        'texture_size': [FW, FH],
        'textures': {'0': f'realm:item/banner/war/{NAME}', 'particle': f'realm:item/banner/war/{NAME}'},
        'elements': els,
        'display': {
            # Scale 3.5 (x0.5 in the frame): a little smaller than block pixels.
            # Pole at y 28 is 20 units above centre -> 35/16 block; translation -57 puts the
            # pole centre 0.4 block above the frame's centre, so its top sits just under the
            # bottom of the block above. The frame goes on the wall block under a protruding
            # beam: the pole tucks in under the beam and the banner lies flat on the wall.
            # z -1: the cloth (model z 8) sits 1/32 block off the wall, enough to stop z-fighting.
            'fixed': {'translation': [0, -57, -1], 'scale': [3.5, 3.5, 3.5]},
            'gui': {'rotation': [0, 180, 0], 'translation': [0, 0, 0], 'scale': [0.3, 0.3, 0.3]},
            'ground': {'translation': [0, 3, 0], 'scale': [0.2, 0.2, 0.2]},
        },
    }


def main(out):
    layers = base_art()
    frames = [frame(layers, t) for t in range(N)]
    strip = Image.new('RGBA', (FW, FH * N))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * FH))
    os.makedirs(out, exist_ok=True)
    strip.save(os.path.join(out, f'{NAME}.png'))
    json.dump({'animation': {'frametime': FRAMETIME, 'width': FW, 'height': FH, 'interpolate': False}},
              open(os.path.join(out, f'{NAME}.png.mcmeta'), 'w'), indent=2)
    json.dump(model(), open(os.path.join(out, f'{NAME}.json'), 'w'), indent=2)
    json.dump({'model': {'type': 'minecraft:model', 'model': f'realm:item/{NAME}'}},
              open(os.path.join(out, f'{NAME}.item.json'), 'w'), indent=2)
    # Preview GIF (cloth only, 6x, on stone-grey).
    s = 6
    gif = []
    for f in frames:
        bg = Image.new('RGBA', (CW * s + 40, H * s + 40), (92, 94, 104, 255))
        bg.alpha_composite(f.crop((0, 0, CW, H)).resize((CW * s, H * s), Image.NEAREST), (20, 20))
        gif.append(bg.convert('P', palette=Image.ADAPTIVE))
    gif[0].save(os.path.join(out, 'preview.gif'), save_all=True, append_images=gif[1:],
                duration=FRAMETIME * 50, loop=0, disposal=2)
    frames[0].crop((0, 0, CW, H)).resize((CW * 8, H * 8), Image.NEAREST).save(os.path.join(out, 'frame0.png'))


if __name__ == '__main__':
    main(sys.argv[1])
