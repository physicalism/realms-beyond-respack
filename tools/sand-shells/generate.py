"""Sparse clam shells, vanilla-textured pebbles, and very rare five-arm starfish."""
import json
from pathlib import Path
import struct
import zlib
ROOT = Path(__file__).resolve().parents[2]
# Shells 24/4000, pebble patches 18/4000, starfish 2/4000.
PLAIN_WEIGHT = 3956
PALETTES = [
    ['bca88c', 'dfc9a5', 'f3dfba', 'd2b996'],  # warm ivory
    ['b27c72', 'dca799', 'f2c6b1', 'c78e82'],  # coral pink
    ['a85b36', 'db8c4b', 'f4b76c', 'c3773d'],  # warm orange
    ['ad573b', 'd9814d', 'efa563', 'bd6c43'],  # terracotta starfish
]

def texture():
    # Four 8x8 painted tiles, one texel per model pixel. Broad shell ribs,
    # a restrained highlight and a darker lip; no noise or smooth gradient.
    rows = ['11121111','11221111','11211211','11211211',
            '11211211','11111111','33333333','00000000']
    pixels = []
    for y in range(16):
        row = bytearray(b'\0')
        for x in range(16):
            palette = PALETTES[(y//8)*2+x//8]
            # Shell tops have a stepped rim, warm bands, and broad mottled
            # clusters, painted at vanilla texel scale. Preserve starfish tile.
            shell_rows = ['00033300','03122330','31221133','32112330',
                          '31123330','03333330','00030300','00000000']
            pattern = rows if (y//8)*2+x//8 == 3 else shell_rows
            row.extend(bytes.fromhex(palette[int(pattern[y%8][x%8])]))
        pixels.append(bytes(row))
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
    path = ROOT/'assets/realm/textures/block/sand_shells.png'
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(pixels)))+chunk(b'IEND',b''))


    # Chalky shell-stone material: warm ivory, lighter than vanilla sand.
    # Hand-set two-pixel clusters retain the surrounding terrain's texel scale.
    ivory = ['f6eed7','eee5c9','e7ddbd','faf3e2']
    pattern = ['11001112','11001112','11331111','11331111',
               '22111100','22111100','11112211','11112211']
    raw = b''.join(b'\0'+b''.join(bytes.fromhex(ivory[int(pattern[(y//2)%8][(x//2)%8])]) for x in range(16)) for y in range(16))
    (ROOT/'assets/realm/textures/block/sand_pebble_ivory.png').write_bytes(
        b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,2,0,0,0))
        +chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def mesh(cells, palette, ox, oz):
    """Only exterior voxel faces: no coplanar overlaps or internal faces."""
    elements = []
    for x,y,z in sorted(cells):
        faces = {}
        for side, delta in [('up',(0,1,0)),('down',(0,-1,0)),('north',(0,0,-1)),('south',(0,0,1)),('west',(-1,0,0)),('east',(1,0,0))]:
            if tuple(a+b for a,b in zip((x,y,z),delta)) in cells:
                continue
            # Top paints the ribs across the entire shell, rather than flat
            # palette-colouring each cuboid. Sides pick the tile's darker lip.
            u,v = (x,z) if side == 'up' else (x,6)
            u += (palette%2)*8
            v += (palette//2)*8
            faces[side] = {'texture':'#shell', 'uv':[u,v,u+1,v+1]}
        if faces:
            elements.append({'from':[ox+x,16+y,oz+z], 'to':[ox+x+1,17+y,oz+z+1], 'faces':faces})
    return elements


def generate():
    texture()
    variants = [{'model':'minecraft:block/sand','weight':PLAIN_WEIGHT}]
    # Four different silhouettes. Depth follows a rim, convex back, or
    # tapered coil, rather than putting the same raised stripe on every shell.
    cup = {(x,0,z) for z in range(5) for x in range(5)
           if not (x in (0,4) and z in (0,4))}
    cup |= {(x,1,0) for x in range(1,4)} | {(0,1,1),(4,1,1)}
    closed = {(x,0,z) for z in range(4) for x in range(6)
              if not (x in (0,5) and z in (0,3))}
    closed |= {(x,1,z) for x in range(1,5) for z in range(1,3)}
    fan = {(x,0,z) for z,(start,end) in enumerate([(2,4),(1,5),(0,6),(0,6),(1,5)]) for x in range(start,end)}
    fan |= {(x,1,z) for z in (1,2) for x in (2,3)}
    spiral = {(x,0,z) for x in range(6) for z in range(4)
              if not (x in (0,5) and z in (0,3))} | {(6,0,1)}
    spiral |= {(x,1,z) for x in range(1,4) for z in (1,2)}
    shapes = [cup,closed,fan,spiral]
    star_rows = ['...#...','...#...','##.#.##','.#####.','..###..','.##.##.','.#...#.']
    star = {(x,0,z) for z,row in enumerate(star_rows) for x,c in enumerate(row) if c=='#'}
    for i in range(19):
        cube = {'from':[0,0,0], 'to':[16,16,16], 'faces':{
            side:{'texture':'#sand','uv':[0,0,16,16],'cullface':side}
            for side in ('up','down','north','south','east','west')}}
        textures = {'particle':'minecraft:block/sand','sand':'minecraft:block/sand'}
        if i < 12:
            palette = i%3
            cells = shapes[i//3]
            x,z = [(4,5),(7,8),(5,8),(6,4)][i//3]
            textures['shell'] = 'realm:block/sand_shells'
            decor = mesh(cells,palette,x,z)
            weight = 2
        elif i in (12,13,14,16,17,18):
            index = i-12 if i<15 else i-16
            materials = ['stone','andesite','cobblestone'] if i<15 else ['sandstone_top','sandstone_bottom','sandstone']
            textures['rock'] = ('minecraft:block/'+materials[index]) if i<15 else 'realm:block/sand_pebble_ivory'
            decor = []
            # Broad solitary stones; third variant has differently sized,
            # offset stones rather than the disliked matching pebble pair.
            plans = [[(5,7,4,3,1)], [(6,6,5,4,1)],
                     [(3,4,4,3,1),(10,10,3,2,1)]]
            for x,z,w,d,h in plans[index]:
                decor.append({'from':[x,16,z],'to':[x+w,16+h,z+d], 'faces':{
                    side:{'texture':'#rock','uv':[4,5,4+(d if side in ('east','west') else w),5+(d if side in ('up','down') else 1)]}
                    for side in ('up','north','south','east','west')}})
            weight = 3
        else:
            textures['shell'] = 'realm:block/sand_shells'
            decor = mesh(star,3,4,5)
            weight = 2
        model = {'parent':'minecraft:block/block','textures':textures,'elements':[cube]+decor}
        path = ROOT/f'assets/realm/models/block/sand_shells/shell_{i:02d}.json'
        path.write_text(json.dumps(model,indent=2)+'\n')
        variants.append({'model':f'realm:block/sand_shells/shell_{i:02d}', 'weight':weight,'y':(i%4)*90})
    (ROOT/'assets/minecraft/blockstates/sand.json').write_text(json.dumps({'variants':{'':variants}},indent=2)+'\n')

if __name__ == '__main__':
    generate()
