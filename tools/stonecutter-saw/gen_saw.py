#!/usr/bin/env python3
"""3D stonecutter saw (Realms Beyond). Usage: gen_saw.py <pack_root>
Overrides minecraft:block/stonecutter. Everything is vanilla (base, textures, the saw's own animated texture)
except that the flat saw plane is extruded to 1 px thick (z 7.5..8.5, the sharpening sword's blade width).

How the extrusion keeps the animation: the vanilla saw face maps texel (u, v) of block/stonecutter_saw to
block x = 16 - u, y = 25 - v on both sides. Besides the two big faces, every texel row gets an up and a down
face and every texel column an east and a west face, each sampling exactly its own row or column of the same
texture. A side face is therefore visible only where its texel is opaque in the current animation frame, so
the teeth stay cut out and move exactly as in vanilla, with a solid rim wherever a texel borders empty space.
Faces that share a plane always point in opposite directions (single-sided quads), so nothing z-fights."""
import json, os, sys

Z1, Z2 = 7.5, 8.5
X1, X2, Y1, Y2 = 1, 15, 9, 16          # the vanilla saw plane

def build_model():
    v = "minecraft:block/stonecutter_"
    side = lambda cull: {"uv": [0, 7, 16, 16], "texture": "#side", "cullface": cull}
    saw = lambda uv: {"uv": uv, "texture": "#saw", "tintindex": 0}
    els = [{"from": [0, 0, 0], "to": [16, 9, 16], "faces": {
        "down": {"uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down"}, "up": {"uv": [0, 0, 16, 16], "texture": "#top"},
        "north": side("north"), "south": side("south"), "west": side("west"), "east": side("east")}}]
    # the two vanilla faces, moved half a pixel out each way
    els.append({"name": "saw_faces", "from": [X1, Y1, Z1], "to": [X2, Y2, Z2],
                "faces": {"north": saw([1, 9, 15, 16]), "south": saw([15, 9, 1, 16])}})
    for y in range(Y1, Y2):                # one texel row: v = 24 - y .. 25 - y, u runs against x
        uv = [16 - X1, 24 - y, 16 - X2, 25 - y]
        els.append({"name": f"saw_row_{y}", "from": [X1, y, Z1], "to": [X2, y + 1, Z2], "faces": {"up": saw(uv), "down": saw(uv)}})
    for x in range(X1, X2):                # one texel column: u = 15 - x .. 16 - x
        uv = [15 - x, 25 - Y2, 16 - x, 25 - Y1]
        els.append({"name": f"saw_col_{x}", "from": [x, Y1, Z1], "to": [x + 1, Y2, Z2], "faces": {"east": saw(uv), "west": saw(uv)}})
    return {"parent": "minecraft:block/block",
            "textures": {"particle": v + "bottom", "bottom": v + "bottom", "top": v + "top", "side": v + "side", "saw": v + "saw"},
            "elements": els}

def main(root):
    model = os.path.join(root, 'assets', 'minecraft', 'models', 'block', 'stonecutter.json')
    os.makedirs(os.path.dirname(model), exist_ok=True)
    json.dump(build_model(), open(model, 'w'), indent=1)
    print('wrote', model)

if __name__ == '__main__':
    main(sys.argv[1])
