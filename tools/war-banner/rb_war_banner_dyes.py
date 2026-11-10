#!/usr/bin/env python3
"""Realms Beyond: the stag war banner in all 16 Minecraft dye colours.

Reuses rb_war_banner.py (same art, animation and model) and only swaps the colours:
field = the dye colour, as on the royal banners. Emblems stay in the stag's golds,
except on yellow and lime, where gold is hard to read and the royal banners' browns
are used instead. The pole finials are always gold. The azure original is untouched.

Usage: rb_war_banner_dyes.py <pack_root> [preview_dir]
"""
import json
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rb_war_banner as wb

DYES = {
    'white': (249, 255, 254), 'orange': (249, 128, 29), 'magenta': (199, 78, 189), 'light_blue': (58, 179, 218),
    'yellow': (254, 216, 61), 'lime': (128, 199, 31), 'pink': (243, 139, 170), 'gray': (71, 79, 82),
    'light_gray': (157, 157, 151), 'cyan': (22, 156, 156), 'purple': (137, 50, 184), 'blue': (60, 68, 170),
    'brown': (131, 84, 50), 'green': (94, 124, 22), 'red': (176, 46, 38), 'black': (29, 29, 33),
}
GOLDS = ((225, 192, 87), (247, 236, 121), (199, 148, 72))     # mid, highlight, shadow
BROWNS = ((133, 86, 46), (170, 118, 68), (102, 65, 36))       # the royal banners' brown finish
BROWN_ON = ('yellow', 'lime')


def mul(rgb, k):
    return tuple(max(0, min(255, round(v * k))) for v in rgb)


def palette(dye):
    """(field, damask, sleeve, (mid, hi, lo)) for a dye."""
    rgb = DYES[dye]
    dark = sum(rgb) < 150
    damask = tuple(v + 13 for v in rgb) if dark else mul(rgb, 0.9)
    return rgb, damask, mul(rgb, 0.72), BROWNS if dye in BROWN_ON else GOLDS


_hardware = wb.hardware


def hardware(px):
    saved = wb.GOLD, wb.GOLD_HI, wb.GOLD_LO
    wb.GOLD, wb.GOLD_HI, wb.GOLD_LO = GOLDS
    _hardware(px)
    wb.GOLD, wb.GOLD_HI, wb.GOLD_LO = saved


wb.hardware = hardware


def main(root, preview=None):
    assets = os.path.join(root, 'assets', 'realm')
    tex_dir = os.path.join(assets, 'textures', 'item', 'banner', 'war')
    for d in (tex_dir, os.path.join(assets, 'models', 'item'), os.path.join(assets, 'items')):
        os.makedirs(d, exist_ok=True)
    sheet = []
    for dye in DYES:
        wb.NAME = name = f'banner_stag_war_{dye}'
        wb.FIELD, wb.FIELD_DAMASK, wb.SLEEVE, (wb.GOLD, wb.GOLD_HI, wb.GOLD_LO) = palette(dye)
        layers = wb.base_art()
        frames = [wb.frame(layers, t) for t in range(wb.N)]
        strip = Image.new('RGBA', (wb.FW, wb.FH * wb.N))
        for i, f in enumerate(frames):
            strip.paste(f, (0, i * wb.FH))
        strip.save(os.path.join(tex_dir, name + '.png'))
        with open(os.path.join(tex_dir, name + '.png.mcmeta'), 'w') as fh:
            json.dump({'animation': {'frametime': wb.FRAMETIME, 'width': wb.FW, 'height': wb.FH, 'interpolate': False}}, fh, indent=2)
        with open(os.path.join(assets, 'models', 'item', name + '.json'), 'w') as fh:
            json.dump(wb.model(), fh, indent=2)
        with open(os.path.join(assets, 'items', name + '.json'), 'w') as fh:
            json.dump({'model': {'type': 'minecraft:model', 'model': f'realm:item/{name}'}}, fh, indent=2)
        sheet.append(frames[6].crop((0, 0, wb.CW, wb.FH)))
    if preview:
        os.makedirs(preview, exist_ok=True)
        s = 4
        out = Image.new('RGBA', (8 * (wb.CW + 4) * s, 2 * (wb.H + 8) * s), (92, 94, 104, 255))
        for i, im in enumerate(sheet):
            im = im.crop((0, 0, wb.CW, wb.H + 4))
            out.alpha_composite(im.resize((im.width * s, im.height * s), Image.NEAREST),
                                ((i % 8) * (wb.CW + 4) * s + 2 * s, (i // 8) * (wb.H + 8) * s + 2 * s))
        out.save(os.path.join(preview, 'war_dyes.png'))


if __name__ == '__main__':
    main(*sys.argv[1:3])
