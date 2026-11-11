#!/usr/bin/env python3
"""Quenching horseshoe for a water cauldron (Realms Beyond). Usage: gen_horseshoe.py <pack_root>
Writes assets/realm/{items,models/item/decorations,textures/item/decorations}/quenching_horseshoe*.
A glowing horseshoe floats down into the cauldron, hisses, stays under for about two seconds while it cools,
lifts out dark, reheats in the air and goes in again. Model space: 1 unit = 1 block px; with the item in an
INVISIBLE item frame on top of the cauldron, model (x, y, z) is block-space (x/16, 1 + (y-8)/16, z/16):
y 8 is the cauldron's rim and WATER_Y the surface of a full cauldron (block y 15)."""
import json, os, random, sys
from PIL import Image

F = 64
WATER_Y = 7
# frame: (pose, state, ticks). pose 0 = under water, 1 = half way, 2 = raised
FRAMES = [(2, 'white', 8), (1, 'white', 2), (0, 'orange', 3), (0, 'red', 4), (0, 'cool', 5), (0, 'cool', 6),
          (0, 'cool', 12), (0, 'cool', 12), (1, 'cool', 2), (2, 'cool', 6), (2, 'red', 6), (2, 'orange', 6)]
NF = len(FRAMES)
POSE_DY = {0: 0, 1: 5, 2: 11}
# Three poses, each with a hot and cool UV slot. Keep the six 11x11 icons separate.
POSE_ORIGIN = {0: (0, 16), 1: (16, 16), 2: (32, 16)}
COOL_ORIGIN = {0: (0, 32), 1: (16, 32), 2: (32, 32)}
STEAM_ORIGIN = [(0, 0), (16, 0)]
SW, SH_ = 16, 12
Y0 = -4                                  # bottom of underwater horseshoe; above the cauldron floor

# An 11x11, pixel-sculpted farrier's horseshoe. Flared heel tips, two bowed branches,
# rounded toe, and four nail holes along each branch. The interior is deliberately empty.
# The curved outline is literal model geometry, not transparent pixels on big cuboids.
SHAPE = [
    "XXX.....XXX",  # widened heels, cut off square like a forged shoe
    ".XX.....XX.",
    ".XX.....XX.",
    ".XX.....XX.",
    ".XX.....XX.",
    ".XX.....XX.",
    ".XXX...XXX.",
    "..XX...XX..",
    "..XXX.XXX..",
    "..XXXXXXX..",
    "...XXXXX...",  # a broad, gently rounded toe
]
HEIGHT = len(SHAPE)
WIDTH = len(SHAPE[0])
assert all(len(row) == WIDTH for row in SHAPE)
# Holes are a single pixel across for good legibility at actual Minecraft scale.
HOLES = {(1, 2), (1, 4), (2, 6), (3, 8),
         (9, 2), (9, 4), (8, 6), (7, 8)}
# Slightly golden highlights when the shoe is blazing, then blue-grey forged iron.
# Each tuple is (highlight, face, shadow, nail recess).
STATE = {
    'white': ((255, 253, 207), (255, 213, 104), (238, 150, 55), (181, 90, 33)),
    'orange': ((255, 215, 99), (247, 139, 39), (190, 71, 27), (117, 42, 21)),
    'red': ((233, 115, 61), (163, 56, 37), (110, 39, 31), (68, 27, 27)),
    'cool': ((190, 194, 195), (138, 144, 148), (83, 91, 98), (45, 51, 57)),
}

def filled(x, y):
    return 0 <= x < WIDTH and 0 <= y < HEIGHT and SHAPE[y][x] == 'X'

def paint_shoe(img, ox, oy, state):
    light, mid, dark, hole = STATE[state]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if not filled(x, y):
                continue
            # A crisp bevel: the top-left edge catches the forge glow / ambient light,
            # but the inner curve and outer underside have a heavier iron edge.
            top = not filled(x, y - 1)
            left = not filled(x - 1, y)
            bottom = not filled(x, y + 1)
            right = not filled(x + 1, y)
            if (x, y) in HOLES:
                c = hole
            elif top or (left and y < HEIGHT - 3):
                c = light
            elif bottom or right:
                c = dark
            else:
                c = mid
            img.putpixel((ox + x, oy + y), c + (255,))


STEAM_COL = [(244, 247, 250), (222, 228, 234), (196, 204, 213), (172, 181, 192)]
def steam_plane(rng):
    out = {f: {} for f in range(NF)}
    births = [2] * 5 + [3] * 4 + [4] * 2
    for born in births:
        x0 = SW / 2 + rng.choice([-1, 1]) * rng.uniform(1.0, 6.0)
        rise, drift, life = rng.uniform(1.5, 2.6), rng.uniform(-0.5, 0.5), rng.choice([3, 4, 4])
        for age in range(life):
            f = born + age
            x, y = x0 + drift * age, SH_ - 1 - rise * age
            size = [(0, 0), (1, 0), (0, -1), (1, -1)] if age < 2 else ([(0, 0), (0, -1)] if age == 2 else [(0, 0)])
            for dx, dy in size:
                px, py = int(x) + dx, int(y) + dy
                if 0 <= px < SW and 0 <= py < SH_: out[f][(px, py)] = STEAM_COL[min(3, age + (dx + dy) % 2)]
    for f in (6, 7):                                   # a last lazy wisp while it sits under water
        out[f][(int(SW / 2 + rng.choice([-3, 2])), SH_ - 1 - (f - 6))] = STEAM_COL[2]
    for dy_, x in ((1, 7), (2, 8)):                    # two drips as it lifts clear
        out[9][(x, SH_ - dy_)] = (150, 190, 232)
    return out

def build_texture():
    rng = random.Random(3)
    img = Image.new('RGBA', (F, F * NF), (0, 0, 0, 0))
    planes = [steam_plane(rng), steam_plane(rng)]
    for f, (pose, state, _) in enumerate(FRAMES):
        ox, oy = (COOL_ORIGIN if state == 'cool' else POSE_ORIGIN)[pose]
        paint_shoe(img, ox, oy + f * F, state)
        for (px, py), data in zip(STEAM_ORIGIN, planes):
            for (x, y), rgb in data[f].items(): img.putpixel((px + x, py + y + f * F), rgb + (255,))
    return img

def face(px_rect):
    x, y, w, h = px_rect; k = 16 / F
    return {"uv": [x * k, y * k, (x + w) * k, (y + h) * k], "texture": "#0"}

def silhouette_boxes():
    """Greedily merge adjacent, equal horizontal runs of pixels into cuboids.

    This preserves the curved outline while keeping element count modest.
    The atlas supplies animation and nail recess shading.
    """
    result = []
    for y, row in enumerate(SHAPE):
        x = 0
        while x < WIDTH:
            if row[x] != 'X':
                x += 1
                continue
            x0 = x
            while x < WIDTH and row[x] == 'X':
                x += 1
            w = x - x0
            if result and any(box[0] == x0 and box[2] == w and box[1]+box[3] == y for box in result):
                k = next(i for i, box in enumerate(result) if box[0] == x0 and box[2] == w and box[1]+box[3] == y)
                px, py, pw, ph = result[k]
                result[k] = (px, py, pw, ph + 1)
            else:
                result.append((x0, y, w, 1))
    return result

BOXES = silhouette_boxes()

def shoe(pose, hot):
    dy = POSE_DY[pose]
    ox, oy = (POSE_ORIGIN if hot else COOL_ORIGIN)[pose]
    els = []
    for i, (x, y, w, h) in enumerate(BOXES):
        # Three-pixel thickness in depth; the face is a real curved horseshoe,
        # not a thin, flat decal and not a set of overlapping rectangular legs.
        e = {"name": f"{'hot' if hot else 'cool'}_{i}_p{pose}",
             "from": [(16 - WIDTH) / 2 + x, Y0 + dy + HEIGHT - y - h, 6.75],
             "to": [(16 - WIDTH) / 2 + x + w, Y0 + dy + HEIGHT - y, 9.25],
             "faces": {
                 "north": face((ox + x, oy + y, w, h)),
                 "south": face((ox + x, oy + y, w, h)),
                 "west": face((ox + x, oy + y, 1, h)),
                 "east": face((ox + x + w - 1, oy + y, 1, h)),
                 "up": face((ox + x, oy + y, w, 1)),
                 "down": face((ox + x, oy + y + h - 1, w, 1))}}
        if hot:
            e.update({"light_emission": 15, "shade": False})
        els.append(e)
    return els

def steam():
    els = []
    for i, ang in enumerate((45, -45)):
        ox, oy = STEAM_ORIGIN[i]; k = 16 / F
        u1, v1, u2, v2 = ox * k, oy * k, (ox + SW) * k, (oy + SH_) * k
        els.append({"name": f"steam_{i}", "from": [0, WATER_Y, 8], "to": [16, WATER_Y + SH_, 8], "shade": False,
                    "rotation": {"angle": ang, "axis": "y", "origin": [8, 8, 8]},
                    "faces": {"south": {"uv": [u1, v1, u2, v2], "texture": "#0"}, "north": {"uv": [u2, v1, u1, v2], "texture": "#0"}}})
    return els

def build_model():
    els = []
    for p in (0, 1, 2): els += shoe(p, True) + shoe(p, False)
    els += steam()
    return {
        "credit": "Realms Beyond - quenching horseshoe (tools/quenching-horseshoe/gen_horseshoe.py)",
        "texture_size": [F, F],
        "textures": {"0": "realm:item/decorations/quenching_horseshoe", "particle": "realm:item/decorations/quenching_horseshoe"},
        "elements": els,
        "display": {
            "fixed": {"rotation": [-90, 180, 0], "translation": [0, 0, 0], "scale": [2, 2, 2]},
            "gui": {"rotation": [10, 20, 0], "translation": [0, -9, 0], "scale": [1.3, 1.3, 1.3]},
            "ground": {"translation": [0, -8, 0], "scale": [0.6, 0.6, 0.6]},
            "thirdperson_righthand": {"translation": [0, -8, 0], "scale": [0.6, 0.6, 0.6]},
            "firstperson_righthand": {"rotation": [0, 20, 0], "translation": [0, -10, 0], "scale": [0.6, 0.6, 0.6]},
        },
    }

def main(root):
    a = os.path.join(root, 'assets', 'realm')
    item = os.path.join(a, 'items', 'quenching_horseshoe.json')
    model = os.path.join(a, 'models', 'item', 'decorations', 'quenching_horseshoe.json')
    tex = os.path.join(a, 'textures', 'item', 'decorations', 'quenching_horseshoe.png')
    for p in (item, model, tex): os.makedirs(os.path.dirname(p), exist_ok=True)
    build_texture().save(tex)
    json.dump({"animation": {"interpolate": False, "frames": [{"index": i, "time": t} for i, (_, _, t) in enumerate(FRAMES)]}},
              open(tex + '.mcmeta', 'w'), indent=2)
    json.dump(build_model(), open(model, 'w'), indent=1)
    json.dump({"model": {"type": "minecraft:model", "model": "realm:item/decorations/quenching_horseshoe"}}, open(item, 'w'), indent=2)
    print('wrote', item, model, tex, sep='\n ')

if __name__ == '__main__':
    main(sys.argv[1])
