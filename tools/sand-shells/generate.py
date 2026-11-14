"""Simple blocky shells on 1/80 sand blocks; vanilla weighted variants."""
import json
from pathlib import Path
import struct, zlib
ROOT = Path(__file__).resolve().parents[2]

def generate():
    texture = ROOT/'assets/realm/textures/block/sand_shells.png'
    texture.parent.mkdir(parents=True, exist_ok=True)
    palettes = [('f2dec3', 'ccb69e', 'fff1db', 'ddc7af'),
                ('e9beb4', 'ba8e88', 'ffe0cf', 'd5a69d'),
                ('d5cdbb', 'a69d8b', 'eee5d1', 'beb5a3'),
                ('bdabae', '92818c', 'dfcbd0', 'a995a1')]
    pixels = b''.join(b'\0' + b''.join(bytes.fromhex(palettes[y//4][x//4]) for x in range(16)) for y in range(16))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data))
    texture.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',16,16,8,2,0,0,0)) + chunk(b'IDAT',zlib.compress(pixels)) + chunk(b'IEND',b''))
    variants = [{'model': 'minecraft:block/sand', 'weight': 1264}]
    for i in range(16):
        palette = i % 4
        shape = i // 4
        x, z = [(4, 5), (8, 8), (5, 9), (9, 4)][shape]
        # Two or three broad cuboids per shell, with integer pixel dimensions.
        # Scallop, clam, tapered whelk, and a broken shell fragment.
        shapes = [
            [(0,0,1,4,1,2), (1,0,0,2,1,1), (1,1,1,2,1,1)],
            [(0,0,0,3,1,2), (1,1,0,1,1,2)],
            [(0,0,0,2,1,3), (0,1,1,2,1,1), (0,0,3,1,1,1)],
            [(0,0,0,3,1,1), (0,0,1,1,1,1)],
        ]
        elements = []
        for dx, dy, dz, w, h, d in shapes[shape]:
            faces = {}
            for side in ('up', 'down', 'north', 'south', 'east', 'west'):
                colour = (2 if dy else 0) if side == 'up' else 1
                faces[side] = {'texture': '#shell', 'uv': [colour*4, palette*4, colour*4+1, palette*4+1]}
            elements.append({'from': [x+dx, 16+dy, z+dz], 'to': [x+dx+w, 16+dy+h, z+dz+d], 'faces': faces})
        # Full vanilla cube, including cullfaces, so buried faces remain culled.
        cube = {'from': [0,0,0], 'to': [16,16,16], 'faces': {
            side: {'texture':'#sand', 'uv':[0,0,16,16], 'cullface':side}
            for side in ('up','down','north','south','east','west')}}
        model = {'parent':'minecraft:block/block', 'textures': {'particle':'minecraft:block/sand', 'sand':'minecraft:block/sand', 'shell':'realm:block/sand_shells'}, 'elements':[cube]+elements}
        path = ROOT/f'assets/realm/models/block/sand_shells/shell_{i:02d}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(model, indent=2)+'\n')
        variants.append({'model':f'realm:block/sand_shells/shell_{i:02d}', 'weight':1, 'y':((shape + palette)%4)*90})
    (ROOT/'assets/minecraft/blockstates/sand.json').write_text(json.dumps({'variants':{'':variants}}, indent=2)+'\n')

if __name__ == '__main__':
    generate()
