#!/usr/bin/env python3
"""Generate raised wool stair surfaces without changing vanilla blockstates."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLOURS = 'white orange magenta light_blue yellow lime pink gray light_gray cyan purple blue brown green red black'.split()
SHAPES = {'': {(1, 0), (1, 1)}, '_inner': {(1, 0), (1, 1), (0, 1)}, '_outer': {(1, 1)}}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def model(high):
    # A one-pixel raised tread, retaining the original bottom and footprint.
    # Partition at each height so adjoining pieces have no internal faces.
    cells = {(x, y, z) for x in range(2) for z in range(2)
             for y in range(2) if y == 0 or (x, z) in high}
    ys = (0, 9, 17)
    elements = []
    for x, y, z in sorted(cells):
        x0, x1, y0, y1, z0, z1 = x*8, x*8+8, ys[y], ys[y+1], z*8, z*8+8
        faces = {}
        for name, delta in {'down': (0,-1,0), 'up': (0,1,0), 'north': (0,0,-1),
                            'south': (0,0,1), 'west': (-1,0,0), 'east': (1,0,0)}.items():
            if tuple(a+b for a,b in zip((x,y,z), delta)) in cells:
                continue
            if name in ('up', 'down'):
                uv = [x0,z0,x1,z1]
                texture = '#top' if name == 'up' else '#bottom'
            else:
                a,b = (x0,x1) if name in ('north','south') else (z0,z1)
                if name in ('north','east'):
                    a,b = 16-b,16-a
                # Keep the familiar wool pixel density on the raised sides.
                uv = [a,max(0,16-y1),b,16-y0]
                texture = '#side'
            face = {'uv': uv, 'texture': texture}
            # Raised upper faces must survive culling against adjacent blocks.
            if name == 'down':
                face['cullface'] = 'down'
            faces[name] = face
        elements.append({'from':[x0,y0,z0], 'to':[x1,y1,z1], 'faces':faces})
    return {'parent':'minecraft:block/stairs', 'textures':{'particle':'#side', **{key:'minecraft:block/white_wool' for key in ('top','side','bottom')}}, 'elements':elements}


def main():
    for suffix, high in SHAPES.items():
        name = 'carpeted_wool_stairs' + suffix
        write(ROOT / 'assets/realm/models/block' / (name + '.json'), model(high))
        for colour in COLOURS:
            texture = 'minecraft:block/' + colour + '_wool'
            write(ROOT / 'assets/minecraft/models/block' / (colour + '_wool_stairs' + suffix + '.json'),
                  {'parent':'realm:block/' + name,
                   'textures':{key:texture for key in ('bottom','side','top')}})


if __name__ == '__main__':
    main()
