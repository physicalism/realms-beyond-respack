#!/usr/bin/env python3
"""Anvil hammer + sparks, and the hand-held blacksmith hammer (Realms Beyond). Usage: gen_hammer.py <pack_root>
Writes assets/realm/{items,models/item/decorations,textures/item/decorations}/{anvil_hammer,blacksmith_hammer}*.
The hand-held hammer is the same hammer, static, with its grip at the model centre.
Model space: 1 unit = 1 px of the anvil block; y=8 is the anvil's top surface
(the fixed display transform puts model (8,8,8) at the centre of the anvil top
when the item sits in an INVISIBLE item frame placed on top of the anvil)."""
import json, math, os, random, sys
from PIL import Image

F = 64                      # frame size in px (uv 16 = 64 px, 1 px per model unit)
# frame: 0 raised, 1 mid (down), 2 strike flash, 3 strike spread, 4 mid (up), 5 raised + embers
TIMES = [8, 1, 2, 2, 2, 2]
POSE_FRAMES = {0: (2, 3), 1: (1, 4), 2: (0, 5)}   # pose index -> frames it is visible in
POSE_ANGLE = {0: 0, 1: 22.5, 2: 45}
POSE_ORIGIN = {0: (0, 16), 1: (16, 16), 2: (32, 16)}  # 16x16 px block per pose

IRON = {'H': (214, 210, 202), 'L': (176, 171, 162), 'M': (138, 133, 126), 'D': (101, 97, 92), 'O': (72, 69, 66)}
WOOD = {'l': (184, 142, 88), 'm': (152, 114, 66), 'd': (116, 86, 48), 'g': (92, 61, 36), 'k': (68, 45, 27)}
PAL = {**IRON, **WOOD}

HEAD_SIDE = ["HLLM", "LMMD", "LMMD", "LMMD", "MMDD", "DDDO"]      # 4x6
HEAD_TOP  = ["HLLM", "LLMM", "LMMD", "MMDD"]                      # 4x4
HEAD_BOT  = ["DDDO", "DMMO", "DMMO", "OOOO"]                      # 4x4
# handle 2x2 section, 10 long; grip wrap on the last 3 px (pivot end, +z)
H_UP   = ["lm"] * 7 + ["gk", "gg", "gk"]                          # 2x10, v -> +z
H_DOWN = ["dd"] * 7 + ["kk", "gk", "kk"]
H_SIDE = ["m" * 7 + "ggk", "d" * 7 + "kgk"]                       # 10x2, u -> +z
H_END  = ["gk", "kk"]
NUB    = ["lm", "md"]

def paint(img, ox, oy, rows):
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            img.putpixel((ox + x, oy + y), PAL[c] + (255,))

# px rects inside a pose block: (x, y, w, h)
R = dict(side=(0, 0, 4, 6), top=(4, 0, 4, 4), bot=(8, 0, 4, 4), hup=(12, 0, 2, 10), hdn=(14, 0, 2, 10),
         hside=(0, 8, 10, 2), hend=(0, 12, 2, 2), nub=(4, 12, 2, 2))

def pose_block(img, ox, oy):
    paint(img, ox, oy, HEAD_SIDE); paint(img, ox + 4, oy, HEAD_TOP); paint(img, ox + 8, oy, HEAD_BOT)
    paint(img, ox + 12, oy, H_UP); paint(img, ox + 14, oy, H_DOWN)
    paint(img, ox, oy + 8, H_SIDE); paint(img, ox, oy + 12, H_END); paint(img, ox + 4, oy + 12, NUB)

# ---- sparks -------------------------------------------------------------
COL = {2: [(255, 255, 255), (255, 247, 170)], 3: [(255, 222, 70), (255, 170, 40)],
       4: [(255, 140, 32), (228, 88, 26)], 5: [(196, 66, 16), (160, 48, 14)]}
TRAIL = {3: (255, 150, 36), 4: (200, 70, 20)}

def spark_plane(rng, w=16, h=10):
    """vertical plane, strike point at bottom centre. returns {frame: {(x,y): rgb}}"""
    out = {f: {} for f in range(6)}
    for side in (-1, 1):
        for i in range(6):
            vx, vy, life = rng.uniform(0.9, 2.3), rng.uniform(1.6, 4.2), rng.choice([2, 3, 3, 4, 4])
            prev = None
            for t in range(1, life + 1):
                d, hh = 2.9 + vx * t, vy * t - 0.45 * t * t
                if hh < 0 or d >= w / 2 or hh >= h: break
                px = int(w / 2 + side * d) if side > 0 else int(w / 2 - d - 0.001)
                py = h - 1 - int(hh)
                f = t + 1
                if prev and f in TRAIL and prev != (px, py): out[f].setdefault(prev, TRAIL[f])
                out[f][(px, py)] = COL[f][i % 2]
                prev = (px, py)
    return out

def spark_floor(rng, n=16):
    """horizontal plane 16x16, centre = strike point; sparks skitter over the anvil top (r <= 5)"""
    out = {f: {} for f in range(6)}
    for i in range(n):
        a = 2 * math.pi * (i + rng.uniform(-0.3, 0.3)) / n
        v, life = rng.uniform(0.6, 1.3), rng.choice([1, 2, 2, 3, 4])
        for t in range(1, life + 1):
            r = 2.6 + v * t
            if r > 5.2: break
            x, z = 8 + r * math.cos(a), 8 + r * math.sin(a)
            if abs(x - 8) < 2.2 and abs(z - 8) < 2.2: continue      # under the hammer head
            out[t + 1][(int(x), int(z))] = COL[t + 1][i % 2]
    return out

def build_texture():
    rng = random.Random(7)
    img = Image.new('RGBA', (F, F * len(TIMES)), (0, 0, 0, 0))
    planes = [((0, 0), spark_plane(rng)), ((16, 0), spark_plane(rng)), ((32, 0), spark_floor(rng))]
    for f in range(len(TIMES)):
        for pose, frames in POSE_FRAMES.items():
            if f in frames:
                ox, oy = POSE_ORIGIN[pose]; pose_block(img, ox, oy + f * F)
        for (ox, oy), data in planes:
            for (x, y), rgb in data[f].items():
                img.putpixel((ox + x, oy + y + f * F), rgb + (255,))
    return img

# ---- model --------------------------------------------------------------
def uv(block, key, flip_u=False):
    x, y, w, h = R[key]; ox, oy = block
    u1, v1, u2, v2 = [(ox + x) * 16 / F, (oy + y) * 16 / F, (ox + x + w) * 16 / F, (oy + y + h) * 16 / F]
    return [u2, v1, u1, v2] if flip_u else [u1, v1, u2, v2]

def face(u): return {"uv": u, "texture": "#0"}

LIFT = 0.1   # keeps the head face off the anvil top (no z-fighting)
PIVOT = [8, 11 + LIFT, 19]

def hammer(pose):
    b = POSE_ORIGIN[pose]
    rot = {"angle": POSE_ANGLE[pose], "axis": "x", "origin": PIVOT}
    s = face(uv(b, 'side'))
    head = {"name": f"head_p{pose}", "from": [6, 8 + LIFT, 6], "to": [10, 14 + LIFT, 10], "rotation": rot,
            "faces": {"north": s, "south": s, "east": s, "west": s,
                      "up": face(uv(b, 'top')), "down": face(uv(b, 'bot'))}}
    handle = {"name": f"handle_p{pose}", "from": [7, 10 + LIFT, 10], "to": [9, 12 + LIFT, 20], "rotation": rot,
              "faces": {"east": face(uv(b, 'hside', True)), "west": face(uv(b, 'hside')),
                        "up": face(uv(b, 'hup')), "down": face(uv(b, 'hdn')), "south": face(uv(b, 'hend'))}}
    n = face(uv(b, 'nub'))
    nub = {"name": f"nub_p{pose}", "from": [7, 10 + LIFT, 5], "to": [9, 12 + LIFT, 6], "rotation": rot,
           "faces": {"north": n, "east": n, "west": n, "up": n, "down": n}}
    return [head, handle, nub]

def sparks():
    els = []
    for i, ang in enumerate((45, -45)):
        u1, u2 = i * 4, i * 4 + 4
        els.append({"name": f"sparks_{i}", "from": [0, 8.05, 8], "to": [16, 18.05, 8], "shade": False,
                    "light_emission": 15, "rotation": {"angle": ang, "axis": "y", "origin": [8, 8, 8]},
                    "faces": {"south": face([u1, 0, u2, 2.5]), "north": face([u2, 0, u1, 2.5])}})
    els.append({"name": "sparks_floor", "from": [0, 8.05, 0], "to": [16, 8.05, 16], "shade": False,
                "light_emission": 15, "faces": {"up": face([8, 0, 12, 4])}})
    return els

def build_model():
    els = []
    for p in (0, 1, 2): els += hammer(p)
    els += sparks()
    return {
        "credit": "Realms Beyond - anvil hammer (tools/anvil-hammer/gen_hammer.py)",
        "texture_size": [F, F],
        "textures": {"0": "realm:item/decorations/anvil_hammer", "particle": "realm:item/decorations/anvil_hammer"},
        "elements": els,
        "display": {
            # item frame: 1 model unit = 1/16 block, model y-up = world up, (8,8,8) = frame's backing surface
            "fixed": {"rotation": [-90, 180, 0], "translation": [0, 0, 0], "scale": [2, 2, 2]},
            "gui": {"rotation": [25, 135, 0], "translation": [1, -3, 0], "scale": [0.7, 0.7, 0.7]},
            "ground": {"translation": [0, -2, 0], "scale": [0.5, 0.5, 0.5]},
            "head": {"translation": [0, 6, 0]},
            "thirdperson_righthand": {"translation": [0, -2, -2], "scale": [0.5, 0.5, 0.5]},
            "firstperson_righthand": {"rotation": [0, 135, 0], "translation": [0, -2, 0], "scale": [0.5, 0.5, 0.5]},
        },
    }

# ---- hand-held hammer (static) --------------------------------------------
def _rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return {'x': [[1, 0, 0], [0, c, -s], [0, s, c]], 'y': [[c, 0, s], [0, 1, 0], [-s, 0, c]],
            'z': [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]
def _mul(a, b): return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def _apply(m, v): return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]
def _euler(m):
    """display rotation [x, y, z] such that Rx.Ry.Rz == m"""
    out = [math.degrees(math.atan2(-m[1][2], m[2][2])), math.degrees(math.asin(max(-1, min(1, m[0][2])))),
           math.degrees(math.atan2(-m[0][1], m[0][0]))]
    back = _mul(_mul(_rot('x', out[0]), _rot('y', out[1])), _rot('z', out[2]))
    assert all(abs(back[i][j] - m[i][j]) < 1e-6 for i in range(3) for j in range(3))
    return [round(v, 2) + 0.0 for v in out]

def hand_uv(key, flip_u=False):
    x, y, w, h = R[key]
    return [x + w, y, x, y + h] if flip_u else [x, y, x + w, y + h]

def build_hand_model():
    """Grip (middle of the wrap) at the model centre (8,8,8); handle along z, head at -z."""
    s = face(hand_uv('side')); n = face(hand_uv('nub'))
    els = [
        {"name": "head", "from": [6, 5, -4], "to": [10, 11, 0],
         "faces": {"north": s, "south": s, "east": s, "west": s, "up": face(hand_uv('top')), "down": face(hand_uv('bot'))}},
        {"name": "handle", "from": [7, 7, 0], "to": [9, 9, 10],
         "faces": {"east": face(hand_uv('hside', True)), "west": face(hand_uv('hside')), "up": face(hand_uv('hup')),
                   "down": face(hand_uv('hdn')), "south": face(hand_uv('hend'))}},
        {"name": "nub", "from": [7, 7, -5], "to": [9, 9, -4], "faces": {"north": n, "east": n, "west": n, "up": n, "down": n}},
    ]
    centre = [0, 0, 2.5 - 8]                 # middle of the hammer (z -5..10) relative to the model centre
    def flat(view, scale, extra=(0, 0, 0)):  # side-on, head up and to the right, centred
        m = _mul(view, _mul(_rot('z', 45), _rot('y', -90)))
        t = [-scale * c + e for c, e in zip(_apply(m, centre), extra)]
        return {"rotation": _euler(m), "translation": [round(v, 2) for v in t], "scale": [scale] * 3}
    eye = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    return {
        "credit": "Realms Beyond - blacksmith hammer (tools/anvil-hammer/gen_hammer.py)",
        "texture_size": [16, 16],
        "textures": {"0": "realm:item/decorations/blacksmith_hammer", "particle": "realm:item/decorations/blacksmith_hammer"},
        "elements": els,
        "display": {
            # in the hand: item +y points forward out of the fist, +z up the arm. Head forward, faces up/down.
            "thirdperson_righthand": {"rotation": [90, 0, 0], "translation": [0, -1.5, 1.25], "scale": [1, 1, 1]},
            "firstperson_righthand": {"rotation": [110, 0, 0], "translation": [1.13, -0.87, -0.35], "scale": [0.68, 0.68, 0.68]},
            "gui": flat(eye, 1.0),
            "fixed": flat(_rot('y', 180), 1.25, (0, 0, -0.75)),
            "ground": {"translation": [0, 2, 3], "scale": [0.75, 0.75, 0.75]},
        },
    }

def main(root):
    a = os.path.join(root, 'assets', 'realm')
    paths = {k: os.path.join(a, *v) for k, v in dict(
        item=('items', 'anvil_hammer.json'), model=('models', 'item', 'decorations', 'anvil_hammer.json'),
        tex=('textures', 'item', 'decorations', 'anvil_hammer.png'),
        item2=('items', 'blacksmith_hammer.json'), model2=('models', 'item', 'decorations', 'blacksmith_hammer.json'),
        tex2=('textures', 'item', 'decorations', 'blacksmith_hammer.png')).items()}
    for p in paths.values(): os.makedirs(os.path.dirname(p), exist_ok=True)
    build_texture().save(paths['tex'])
    json.dump({"animation": {"interpolate": False, "frames": [{"index": i, "time": t} for i, t in enumerate(TIMES)]}},
              open(paths['tex'] + '.mcmeta', 'w'), indent=2)
    json.dump(build_model(), open(paths['model'], 'w'), indent=1)
    json.dump({"model": {"type": "minecraft:model", "model": "realm:item/decorations/anvil_hammer"}},
              open(paths['item'], 'w'), indent=2)
    static = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); pose_block(static, 0, 0); static.save(paths['tex2'])
    json.dump(build_hand_model(), open(paths['model2'], 'w'), indent=1)
    json.dump({"model": {"type": "minecraft:model", "model": "realm:item/decorations/blacksmith_hammer"}},
              open(paths['item2'], 'w'), indent=2)
    print('wrote', *paths.values(), sep='\n ')

if __name__ == '__main__':
    main(sys.argv[1])
