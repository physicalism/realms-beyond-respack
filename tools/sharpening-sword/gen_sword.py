#!/usr/bin/env python3
"""Sharpening sword + sparks for the side of a stonecutter (Realms Beyond). Usage: gen_sword.py <pack_root>
Writes assets/realm/{items,models/item/decorations,textures/item/decorations}/sharpening_sword*.
Model space: 1 unit = 1 block px. The fixed display puts model (8,8,8) at the centre of the block face an
INVISIBLE item frame hangs on, with model -z going into that block: the stonecutter is x 0..16, y 0..16,
z -8..8, its top at y 9 and its saw (1 px thick, see tools/stonecutter-saw) centred on z = 0, top at y 16;
put the frame on a side where the saw is seen flat-on."""
import json, os, random, sys
from PIL import Image

F = 64
NF, TICKS = 6, 3                       # 6 frames x 3 ticks = 0.9 s loop
SHIFT = 6                              # sword pulled back towards the hilt, so the saw works the tip end
POSE_DZ = {0: SHIFT - 2, 1: SHIFT, 2: SHIFT + 2}   # the sword slides along z across the saw
FRAME_POSE = [0, 0, 1, 2, 2, 1]
POSE_ORIGIN = {0: (0, 16), 1: (16, 16), 2: (32, 16)}
PLANE_ORIGIN = [(0, 0), (32, 0)]       # two 20x12 spark planes
PW, PH = 20, 12
CONTACT = (8, 16, 0)                   # top of the saw

PAL = {'H': (238, 241, 244), 'L': (203, 208, 214), 'M': (163, 170, 179), 'S': (126, 133, 143),
       'B': (222, 176, 66), 'b': (170, 124, 40), 'o': (122, 86, 28),
       'g': (104, 70, 42), 'k': (74, 49, 30)}
BLADE = ["LLLLLLLLLLLL", "MSSSSSSSSSSM", "HHHHHHHHHHHH"]   # 12x3: back, fuller, ground edge
BACK = ["L"] * 12                                          # 1x12
EDGE = ["H"] * 12
GUARD = ["BBbo", "BbBo", "BBbo", "booo"]                   # 4x4
GRIP = ["gkgk", "kgkk"]                                    # 4x2
POMMEL = ["Bb", "bo"]                                      # 2x2
R = dict(blade=(0, 0, 12, 3), back=(12, 0, 1, 12), edge=(13, 0, 1, 12), guard=(0, 4, 4, 4), grip=(4, 4, 4, 2),
         pommel=(8, 4, 2, 2), tip1=(0, 1, 2, 2), tip2=(0, 2, 1, 1), gstrip=(0, 4, 1, 4), gtop=(0, 4, 4, 1),
         gripcap=(4, 4, 1, 2), griptop=(4, 4, 4, 1), edge2=(13, 0, 1, 2), edge1=(13, 0, 1, 1))

def paint(img, ox, oy, rows):
    for y, row in enumerate(rows):
        for x, c in enumerate(row): img.putpixel((ox + x, oy + y), PAL[c] + (255,))

def pose_block(img, ox, oy):
    paint(img, ox, oy, BLADE); paint(img, ox + 12, oy, BACK); paint(img, ox + 13, oy, EDGE)
    paint(img, ox, oy + 4, GUARD); paint(img, ox + 4, oy + 4, GRIP); paint(img, ox + 8, oy + 4, POMMEL)

AGE_COL = [(255, 255, 255), (255, 244, 150), (255, 214, 64), (255, 160, 38), (232, 96, 28), (186, 60, 16)]

def spark_plane(rng, n=16):
    """plane px (x, y): x 0 = model x 4, y 0 = model y 21 (top). Seamless loop: each spark has a phase."""
    out = {f: {} for f in range(NF)}
    cx, cy = CONTACT[0] - 4, 21 - CONTACT[1]          # contact px = (4, 5)
    for i in range(n):
        phase, life = i % NF, rng.choice([3, 4, 4, 5, 6])
        vx, vy = rng.uniform(1.4, 3.4), rng.uniform(-0.6, 2.2)
        if i % 8 == 7: vx = -rng.uniform(0.6, 1.2)    # the odd one kicks back
        for f in range(NF):
            age = (f - phase) % NF
            if age >= life: continue
            t = age + 0.6
            x, y = cx + vx * t, cy - (vy * t - 0.28 * t * t)
            if not (0 <= x < PW and 0 <= y < PH): continue
            if 3 <= x < 5 and y < 5: continue         # inside the sword
            if age >= 2:                               # short trail back toward the wheel
                tx, ty = int(x - vx * 0.45), int(y + (vy - 0.56 * t) * 0.45)
                if 0 <= tx < PW and 0 <= ty < PH and not (3 <= tx < 5 and ty < 5):
                    out[f].setdefault((tx, ty), AGE_COL[min(age + 1, 5)])
            out[f][(int(x), int(y))] = AGE_COL[age]
    for f in range(NF):                                # glow either side of the blade, just above the saw's rim
        for dx in (-1, 0):
            out[f][(cx + dx, cy - 1)] = AGE_COL[(f + dx) % 2]
    return out

def build_texture():
    rng = random.Random(11)
    img = Image.new('RGBA', (F, F * NF), (0, 0, 0, 0))
    planes = [spark_plane(rng), spark_plane(rng)]
    for f in range(NF):
        ox, oy = POSE_ORIGIN[FRAME_POSE[f]]; pose_block(img, ox, oy + f * F)
        for (px, py), data in zip(PLANE_ORIGIN, planes):
            for (x, y), rgb in data[f].items(): img.putpixel((px + x, py + y + f * F), rgb + (255,))
    return img

def uv(block, key, flip_u=False):
    x, y, w, h = R[key]; ox, oy = block; k = 16 / F
    u1, v1, u2, v2 = (ox + x) * k, (oy + y) * k, (ox + x + w) * k, (oy + y + h) * k
    return [u2, v1, u1, v2] if flip_u else [u1, v1, u2, v2]
def face(u): return {"uv": u, "texture": "#0"}

Y0 = 16.1                               # ground edge rides just above the saw

def sword(pose):
    b, dz = POSE_ORIGIN[pose], POSE_DZ[pose]
    f = lambda key, flip=False: face(uv(b, key, flip))
    def el(name, lo, hi, faces):
        return {"name": f"{name}_p{pose}", "from": [lo[0], lo[1], lo[2] + dz], "to": [hi[0], hi[1], hi[2] + dz], "faces": faces}
    return [
        el("blade", (7.5, Y0, -8), (8.5, Y0 + 3, 4), {"east": f('blade'), "west": f('blade', True), "up": f('back'), "down": f('edge')}),
        el("tip1", (7.5, Y0 + .5, -10), (8.5, Y0 + 2.5, -8), {"east": f('tip1'), "west": f('tip1', True), "up": f('edge2'), "down": f('edge2'), "north": f('tip1')}),
        el("tip2", (7.5, Y0 + 1, -11), (8.5, Y0 + 2, -10), {k: f('tip2') for k in ("east", "west", "up", "down", "north")}),
        el("guard", (6, Y0 - .5, 4), (10, Y0 + 3.5, 5), {"north": f('guard'), "south": f('guard'), "east": f('gstrip'), "west": f('gstrip'), "up": f('gtop'), "down": f('gtop')}),
        el("grip", (7.5, Y0 + .5, 5), (8.5, Y0 + 2.5, 9), {"east": f('grip'), "west": f('grip', True), "up": f('griptop'), "down": f('griptop')}),
        el("pommel", (7, Y0 + .5, 9), (9, Y0 + 2.5, 10), {k: f('pommel') for k in ("north", "south", "east", "west", "up", "down")}),
    ]

def sparks():
    els = []
    for i, ang in enumerate((22.5, -22.5)):            # shallow X along the spray, clear of the saw's own plane
        ox, oy = PLANE_ORIGIN[i]; k = 16 / F
        u1, v1, u2, v2 = ox * k, oy * k, (ox + PW) * k, (oy + PH) * k
        els.append({"name": f"sparks_{i}", "from": [4, 9, 0], "to": [24, 21, 0], "shade": False, "light_emission": 15,
                    "rotation": {"angle": ang, "axis": "x", "origin": list(CONTACT)},
                    "faces": {"south": face([u1, v1, u2, v2]), "north": face([u2, v1, u1, v2])}})
    return els

def build_model():
    els = []
    for p in (0, 1, 2): els += sword(p)
    els += sparks()
    return {
        "credit": "Realms Beyond - sharpening sword (tools/sharpening-sword/gen_sword.py)",
        "texture_size": [F, F],
        "textures": {"0": "realm:item/decorations/sharpening_sword", "particle": "realm:item/decorations/sharpening_sword"},
        "elements": els,
        "display": {
            # wall frame: model units = block px, +x = viewer's right, -z = into the block behind the frame
            "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [2, 2, 2]},
            "gui": {"rotation": [20, 60, 0], "translation": [1, -9, 0], "scale": [0.75, 0.75, 0.75]},
            "ground": {"translation": [0, -6, 0], "scale": [0.5, 0.5, 0.5]},
            "thirdperson_righthand": {"translation": [0, -6, 0], "scale": [0.5, 0.5, 0.5]},
            "firstperson_righthand": {"rotation": [0, 60, 0], "translation": [0, -6, 0], "scale": [0.5, 0.5, 0.5]},
        },
    }

def main(root):
    a = os.path.join(root, 'assets', 'realm')
    item = os.path.join(a, 'items', 'sharpening_sword.json')
    model = os.path.join(a, 'models', 'item', 'decorations', 'sharpening_sword.json')
    tex = os.path.join(a, 'textures', 'item', 'decorations', 'sharpening_sword.png')
    for p in (item, model, tex): os.makedirs(os.path.dirname(p), exist_ok=True)
    build_texture().save(tex)
    json.dump({"animation": {"interpolate": False, "frametime": TICKS}}, open(tex + '.mcmeta', 'w'), indent=2)
    json.dump(build_model(), open(model, 'w'), indent=1)
    json.dump({"model": {"type": "minecraft:model", "model": "realm:item/decorations/sharpening_sword"}}, open(item, 'w'), indent=2)
    print('wrote', item, model, tex, sep='\n ')

if __name__ == '__main__':
    main(sys.argv[1])
