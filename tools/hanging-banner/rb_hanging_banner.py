#!/usr/bin/env python3
"""Realms Beyond: hanging stag banner, animated, in all 16 Minecraft dye colours.

A small banner (about 1 x 2.5 blocks) that hangs from a pole running straight out of
the end of a bottom-half trapdoor: the pole's loops are flush with the trapdoor's
3px thickness and the banner hangs in the next block along. It is an item_display
model (see README for the summon commands), visible from both sides.

Art matches the clocktower war banner: the town's original stag (1x here, in its own
three golds at 2x, 1px black outline), star and corner flourishes above, fleur-de-lis below, ink + gold border,
three-point dagged hem with gold fringe, faint lozenge damask. On yellow and lime the
emblems use the royal banners' browns, because gold is hard to read there.
Animation: 32 frames (3.2 s loop), the same fold-light and sway method as the war banner.

Usage: rb_hanging_banner.py <pack_root> [preview_dir]
"""
import json
import math
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 34, 87                 # cloth texels (rows 0-86), fringe hangs below
PH = 91                       # rows covered by the cloth plane (cloth + fringe)
FW, FH = 64, 128              # one animation frame
N = 32
FRAMETIME = 2
M = 3                         # transparent margin each side, room for the sway
CW = W + 2 * M
HX = 44                       # hardware textures start here
TX = 0.45                     # model units per texel
SPLIT = 40                    # cloth row where the two cloth planes meet
Y0 = 20                       # model y of the trapdoor block's floor (the entity sits 0.75 block below it)

DYES = {
    'white': (249, 255, 254), 'orange': (249, 128, 29), 'magenta': (199, 78, 189), 'light_blue': (58, 179, 218),
    'yellow': (254, 216, 61), 'lime': (128, 199, 31), 'pink': (243, 139, 170), 'gray': (71, 79, 82),
    'light_gray': (157, 157, 151), 'cyan': (22, 156, 156), 'purple': (137, 50, 184), 'blue': (60, 68, 170),
    'brown': (131, 84, 50), 'green': (94, 124, 22), 'red': (176, 46, 38), 'black': (29, 29, 33),
}
GOLDS = ((225, 192, 87), (247, 236, 121), (199, 148, 72))     # mid, highlight, shadow
BROWNS = ((133, 86, 46), (170, 118, 68), (102, 65, 36))       # the royal banners' brown finish
BROWN_ON = ('yellow', 'lime')
INK = (24, 18, 16)

STAG = open(os.path.join(HERE, '..', 'war-banner', 'stag.txt')).read().split()
STAR = ["..#..", ".###.", "#####", ".###.", "..#.."]
FLEUR = [
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
BAND = 4                      # rows 0-3: ink / gold / gold / ink band under the pole
STAR_Y, STAG_Y, FLEUR_Y = 7, 18, 58
HEM_TOP, HEM_TIP = 79, 85
FLOURISH = ["####..", "#..#..", "#.##..", "#.....", ".#....", "..#..."]   # top-left corner; mirrored for top-right


def mul(rgb, k):
    return tuple(max(0, min(255, round(v * k))) for v in rgb)


def hem(x):
    centres = (W / 6 - 0.5, W / 2 - 0.5, 5 * W / 6 - 0.5)
    c = min(centres, key=lambda c: abs(x - c))
    return round(HEM_TIP - (HEM_TIP - HEM_TOP) * min(1, abs(x - c) / (W / 6)))


def base_art(dye):
    field = DYES[dye]
    damask = tuple(v + 13 for v in field) if sum(field) < 150 else mul(field, 0.9)
    gold, gold_hi, gold_lo = BROWNS if dye in BROWN_ON else GOLDS
    art = {}
    cloth = {(x, y) for x in range(W) for y in range(hem(x) + 1)}
    for (x, y) in cloth:
        art[(x, y)] = (damask if ((x + y) % 8 == 0 or (x - y) % 8 == 0) else field, 'field')

    def out(q):
        return q not in cloth
    for (x, y) in cloth:
        if y >= HEM_TOP - 1:
            below1, below2 = out((x, y + 1)), out((x, y + 2))
            if below1 or x in (0, W - 1):
                art[(x, y)] = (gold_lo if below1 else INK, 'gold' if below1 else 'ink')
            elif below2 or x in (1, W - 2):
                art[(x, y)] = (gold, 'gold')
            continue
        if x in (0, W - 1):
            art[(x, y)] = (INK, 'ink')
        elif x in (1, W - 2):
            art[(x, y)] = (gold, 'gold')
    for x in range(W):
        for y, c, k in ((0, INK, 'ink'), (1, gold_hi, 'gold'), (2, gold_lo, 'gold'), (3, INK, 'ink')):
            art[(x, y)] = (c, k)

    emb = {}

    def outline(shape):
        for (x, y) in shape:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in shape and q in art:
                    emb[q] = (INK, 'ink')

    def stamp(pattern, ox, oy):
        shape = {(ox + c, oy + r) for r, row in enumerate(pattern) for c, v in enumerate(row) if v == '#'}
        outline(shape)
        for (x, y) in shape:
            up, down = (x, y - 1) not in shape, (x, y + 1) not in shape
            emb[(x, y)] = (gold_hi if up else gold_lo if down else gold, 'gold')

    stamp(STAR, (W - 5) // 2, STAR_Y)
    stamp(FLOURISH, 3, STAR_Y - 1)
    stamp([r[::-1] for r in FLOURISH], W - 3 - 6, STAR_Y - 1)
    # The town's original banner stag at exactly 2x, as on the clocktower war banner.
    tone = {'h': gold_hi, '#': gold, 'd': gold_lo}
    ox = (W - 2 * len(STAG[0])) // 2
    stag = {(ox + 2 * c + i, STAG_Y + 2 * r + j): tone[ch] for r, row in enumerate(STAG)
            for c, ch in enumerate(row) if ch in tone for i in range(2) for j in range(2)}
    outline(stag)
    for p, c in stag.items():
        emb[p] = (c, 'gold')
    stamp(FLEUR, (W - 11) // 2, FLEUR_Y)
    for x in range(1, W - 1, 2):                 # fringe on alternate columns
        y0 = hem(x) + 1
        for i, c in enumerate((gold, gold, gold_lo)):
            art[(x, y0 + i)] = (c, 'fringe')
    return art, emb, field, (gold, gold_hi, gold_lo)


def frame(layers, t):
    art, emb, field, golds = layers
    img = Image.new('RGBA', (FW, FH), (0, 0, 0, 0))
    px = img.load()
    ph = 2 * math.pi * t / N
    features = [(STAR_Y - 2, STAR_Y + 6), (STAG_Y - 1, STAG_Y + 33), (FLEUR_Y - 1, FLEUR_Y + 14), (HEM_TOP - 1, H)]

    def rep(y):
        for a, b in features:
            if a <= y < b:
                return (a + b) // 2
        return y

    def sway_f(y):
        a = 0.0 if y < 16 else min(1.0, (y - 16) / (H - 16)) ** 1.6 * 2.3
        return a * (math.sin(2 * math.pi * y / 60 - ph) + 0.25 * math.sin(4 * math.pi * y / 60 - 2 * ph + 1.1))

    def light(x, y, rgb):
        amp = 0.45 + 0.55 * y / H
        m = amp * (0.75 * math.sin(2 * math.pi * x / 14 + 2 * math.pi * y / 46 - ph)
                   + 0.25 * math.sin(2 * math.pi * x / 7 - 2 * math.pi * y / 80 - 2 * ph))
        q = 2 if m > 0.62 else 1 if m > 0.28 else -2 if m < -0.62 else -1 if m < -0.28 else 0
        return mul(rgb, 1 + 0.13 * q * 0.55)

    def put(tx, y, rgb):
        tx += M
        if 0 <= tx < CW and 0 <= y < PH:
            px[tx, y] = rgb + (255,)

    hem_rows = HEM_TOP - 1

    def row_dx(y):
        return round(sway_f(y if y < hem_rows else (hem_rows + H) // 2))

    def draw_base(kinds):
        for y in range(PH):
            dx = row_dx(y)
            for x in range(W):
                if (x, y) not in art:
                    continue
                rgb, kind = art[(x, y)]
                if kind not in kinds:
                    continue
                if kind == 'fringe':
                    tip = y - hem(x)
                    lag = sway_f(HEM_TOP + 6 + 3 * tip) - sway_f(HEM_TOP + 6)
                    put(x + dx + round(lag + 0.5 * tip / 3 * math.sin(2 * math.pi * x / 9 - ph + math.pi / 2)), y, rgb)
                    continue
                if kind != 'ink' and y >= BAND:
                    rgb = light(x, y, rgb)
                put(x + dx, y, rgb)

    draw_base(('field',))
    for (x, y), (rgb, kind) in emb.items():
        dx = round(sway_f(rep(y)))
        if kind != 'ink':
            rgb = light(x, y, rgb)
        put(x + dx, y, rgb)
    draw_base(('gold', 'ink', 'fringe'))
    hardware(px, field, golds)
    return img


# Pole end: dark iron, the same stepped spike as the Blacksmith sign's bracket.
IRON = [(50, 50, 56), (66, 66, 73), (38, 38, 43), (28, 28, 32)]   # base, light, dark, edge
IRON_SIDE = [(66, 66, 73), (50, 50, 56), (44, 44, 50), (34, 34, 39)]  # lit top -> shaded bottom


def hardware(px, field, golds):
    """Pole, loops and finial at block-pixel density (1 texel = 1 model unit), so they
    match the trapdoor's own pixels: pole 17x3 at (44,0), loop face 2x4 at (44,8), loop
    side 4x4 at (48,8), iron spike side 1x4 at (54,8), iron spike end 4x4 at (58,8)."""
    rows = [(128, 98, 60), (113, 85, 52), (92, 68, 41)]
    for y, c in enumerate(rows):
        for x in range(17):
            k = 0.94 if (x * 5 + y * 3) % 7 == 0 else 1.05 if (x * 3 + y) % 11 == 0 else 1
            px[HX + x, y] = mul(c, k) + (255,)
    shades = (1.1, 1.0, 0.92, 0.78)
    for y in range(4):
        for x in range(2):
            px[HX + x, 8 + y] = mul(field, shades[y]) + (255,)
            px[HX + 10 + x, 8 + y] = IRON_SIDE[y] + (255,)
        for x in range(4):
            px[HX + 4 + x, 8 + y] = mul(field, shades[y] * (0.9 if x in (0, 3) else 1)) + (255,)
            edge = x in (0, 3) or y in (0, 3)
            px[HX + 14 + x, 8 + y] = (IRON[3] if edge else IRON[1] if (x, y) == (1, 1) else IRON[0]) + (255,)


def uv(x0, y0, x1, y1):
    return [x0 * 16 / FW, y0 * 16 / FH, x1 * 16 / FW, y1 * 16 / FH]


def model(name):
    """item_display model. Block-local x 0 = the trapdoor's end, x 16 = far side of the
    banner's block; model y Y0 = the trapdoor block's floor. The pole is 3x3 units, flush
    with a bottom-half trapdoor (y 0-3); the loops and finial stand half a pixel proud.
    The cloth is a plane at z 8 showing the same (unmirrored) art on both sides."""
    t = '#0'
    face = lambda box: {'uv': uv(*box), 'texture': t}
    cx = 8
    x0, x1 = cx - CW * TX / 2, cx + CW * TX / 2
    # The cloth is 40.95 units long, more than fits under the pole inside the -16..32
    # element bounds, so it is two planes: rows 0-SPLIT as they are, and the rest defined
    # upside down above the split line and turned 180 degrees about z (UVs flipped to match).
    ys = Y0 - SPLIT * TX
    els = [{'name': 'cloth_top', 'from': [round(x0, 3), round(ys, 3), 8], 'to': [round(x1, 3), Y0, 8],
            'faces': {'south': face((0, 0, CW, SPLIT)), 'north': face((0, 0, CW, SPLIT))}},
           {'name': 'cloth_bottom', 'from': [round(x0, 3), round(ys, 3), 8], 'to': [round(x1, 3), round(ys + (PH - SPLIT) * TX, 3), 8],
            'rotation': {'origin': [cx, round(ys, 3), 8], 'axis': 'z', 'angle': 180},
            'faces': {'south': face((CW, PH, 0, SPLIT)), 'north': face((CW, PH, 0, SPLIT))}}]
    wood, wood_end = (HX, 0, HX + 17, 3), (HX, 0, HX + 3, 3)
    els.append({'name': 'pole', 'from': [0, Y0, 6.5], 'to': [17, Y0 + 3, 9.5],
                'faces': {**{d: face(wood) for d in ('north', 'south', 'up', 'down')},
                          **{d: face(wood_end) for d in ('east', 'west')}}})
    loop, loop_side = (HX, 8, HX + 2, 12), (HX + 4, 8, HX + 8, 12)
    for i, lx in enumerate((2, 7, 12)):
        els.append({'name': f'loop_{i}', 'from': [lx, Y0 - 0.5, 6], 'to': [lx + 2, Y0 + 3.5, 10],
                    'faces': {**{d: face(loop) for d in ('north', 'south', 'up', 'down')},
                              **{d: face(loop_side) for d in ('east', 'west')}}})
    # Pole end: the Blacksmith bracket's stepped iron spike, scaled to the 3-unit pole:
    # a 4x4 collar, then 3x3, 2x2 and a 1x1 tip, one unit each, centred on the pole.
    for i, (size, name_) in enumerate(((4, 'spike_collar'), (3, 'spike_body'), (2, 'spike_taper'), (1, 'spike_tip'))):
        lo = (3 - size) / 2
        side = (HX + 10, 8, HX + 11, 8 + size)
        end = (HX + 14 + (4 - size) // 2, 8 + (4 - size) // 2, HX + 14 + (4 - size) // 2 + size, 8 + (4 - size) // 2 + size)
        els.append({'name': name_, 'from': [17 + i, Y0 + lo, 8 - size / 2], 'to': [18 + i, Y0 + lo + size, 8 + size / 2],
                    'faces': {**{d: face(side) for d in ('north', 'south', 'up', 'down')},
                              **{d: face(end) for d in ('east', 'west')}}})
    tex = f'realm:item/banner/hanging/{name}'
    return {
        'credit': 'Realms Beyond',
        'texture_size': [FW, FH],
        'textures': {'0': tex, 'particle': tex},
        'elements': els,
        'display': {
            'gui': {'translation': [0, -1, 0], 'scale': [0.36, 0.36, 0.36]},
            'ground': {'translation': [0, 0, 0], 'scale': [0.25, 0.25, 0.25]},
            'fixed': {'translation': [0, -4, 0], 'scale': [0.5, 0.5, 0.5]},
        },
    }


def main(root, preview=None):
    assets = os.path.join(root, 'assets', 'realm')
    tex_dir = os.path.join(assets, 'textures', 'item', 'banner', 'hanging')
    for d in (tex_dir, os.path.join(assets, 'models', 'item'), os.path.join(assets, 'items')):
        os.makedirs(d, exist_ok=True)
    shots = {}
    for dye in DYES:
        name = f'banner_stag_hanging_{dye}'
        layers = base_art(dye)
        frames = [frame(layers, t) for t in range(N)]
        strip = Image.new('RGBA', (FW, FH * N))
        for i, f in enumerate(frames):
            strip.paste(f, (0, i * FH))
        strip.save(os.path.join(tex_dir, name + '.png'))
        with open(os.path.join(tex_dir, name + '.png.mcmeta'), 'w') as fh:
            json.dump({'animation': {'frametime': FRAMETIME, 'width': FW, 'height': FH, 'interpolate': False}}, fh, indent=2)
        with open(os.path.join(assets, 'models', 'item', name + '.json'), 'w') as fh:
            json.dump(model(name), fh, indent=2)
        with open(os.path.join(assets, 'items', name + '.json'), 'w') as fh:
            json.dump({'model': {'type': 'minecraft:model', 'model': f'realm:item/{name}'}}, fh, indent=2)
        shots[dye] = frames
    if preview:
        os.makedirs(preview, exist_ok=True)
        s = 4

        def scene(f):
            """Flat side view: trapdoor stub, pole, loops, finial, cloth."""
            px_per_unit = s / TX
            bg = Image.new('RGBA', (int(40 * px_per_unit), int(51 * px_per_unit)), (142, 178, 222, 255))
            X = lambda u: int((u + 16) * px_per_unit)          # model x -> px (trapdoor block starts at -16)
            Y = lambda u: int((Y0 + 4 - u) * px_per_unit)      # model y -> px
            for a, b, c in ((0, 3, (104, 78, 47)), (2.2, 3, (124, 94, 58))):
                bg.paste(c + (255,), (X(-16), Y(Y0 + b), X(0), Y(Y0 + a)))
            bg.alpha_composite(f.crop((0, 0, CW, PH)).resize((CW * s, PH * s), Image.NEAREST), (X(8 - CW * TX / 2), Y(Y0)))
            def part(box, x0, y0, x1, y1):
                bg.alpha_composite(f.crop(box).resize((X(x1) - X(x0), Y(y0) - Y(y1)), Image.NEAREST), (X(x0), Y(y1)))
            part((HX, 0, HX + 17, 3), 0, Y0, 17, Y0 + 3)
            for lx in (2, 7, 12):
                part((HX, 8, HX + 2, 12), lx, Y0 - 0.5, lx + 2, Y0 + 3.5)
            part((HX + 10, 8, HX + 12, 12), 17, Y0 - 0.5, 19, Y0 + 3.5)
            return bg
        tiles = [scene(shots[d][6]) for d in DYES]
        w, h = tiles[0].size
        sheet = Image.new('RGBA', (8 * w, 2 * h))
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % 8) * w, (i // 8) * h))
        sheet.save(os.path.join(preview, 'hanging_all.png'))
        big = scene(shots['orange'][6])
        big.resize((w * 2, h * 2), Image.NEAREST).save(os.path.join(preview, 'hanging_orange.png'))
        gif = [scene(f).convert('P', palette=Image.ADAPTIVE) for f in shots['orange']]
        gif[0].save(os.path.join(preview, 'hanging_orange.gif'), save_all=True, append_images=gif[1:],
                    duration=FRAMETIME * 50, loop=0)


if __name__ == '__main__':
    main(*sys.argv[1:3])
