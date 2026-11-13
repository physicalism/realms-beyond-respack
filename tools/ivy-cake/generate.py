"""Replace the Jellie cat topper with a small Ivy Labrador head."""
from pathlib import Path
import json, struct, zlib, copy
ROOT = Path(__file__).resolve().parents[2]


def write_png(path, w, h, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\0' + bytes(sum((list(p) for p in pixels[y*w:(y+1)*w]), [])) for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

PALETTE = [
    (34, 33, 32),  # coat, warm charcoal
    (43, 42, 40),  # skull top
    (26, 25, 24),  # hanging ears
    (48, 45, 41),  # broad muzzle
    (18, 17, 16),  # nose and mouth
    (7, 8, 8),    # black eyes
    (7, 8, 8),    # pupils
    (221, 212, 190), # tiny eye glint
    (24, 104, 72), # emerald collar
    (41, 132, 89), # collar top
    (198, 153, 62), # gold tag
    (67, 64, 58), # nose glint
]


def cuboid(name, lo, hi, colour, top=None):
    faces = {}
    for face in ('north', 'east', 'south', 'west', 'up', 'down'):
        c = top if face == 'up' and top is not None else colour
        faces[face] = {'uv': [(c+.1)/2,.05,(c+.9)/2,.45], 'texture': '#ivy'}
    return {'name':'ivy_'+name,'from':lo,'to':hi,'faces':faces}


def topper():
    # Original cookie-like proportions: one head, two floppy ears, one shallow muzzle.
    head = cuboid('head',[3,8.6,4],[9,12.6,6],0,1)
    head['faces']['north']['uv'] = [0,1,3,3]
    muzzle = cuboid('muzzle',[4.5,9,3.5],[7.5,10.5,4.02],3)
    muzzle['faces']['north']['uv'] = [4,1,6,2]
    parts = [head,
        cuboid('left_ear',[2,9,4],[3.1,12,6],2),
        cuboid('right_ear',[8.9,9,4],[10,12,6],2),muzzle]
    for part in parts:
        part['rotation']={'axis':'x','angle':22.5,'origin':[7,11.85,6]}
    return parts


def rotate_cake(element):
    e=copy.deepcopy(element)
    lo,hi=e['from'],e['to']
    e['from']=[16-hi[0],lo[1],16-hi[2]]
    e['to']=[16-lo[0],hi[1],16-lo[2]]
    swap={'north':'south','south':'north','east':'west','west':'east','up':'up','down':'down'}
    e['faces']={swap[f]:v for f,v in e['faces'].items()}
    for f in ('up','down'):
        if f in e['faces']:e['faces'][f]['rotation']=(e['faces'][f].get('rotation',0)+180)%360
    if 'rotation' in e:
        r=e['rotation'];o=r['origin'];r['origin']=[16-o[0],o[1],16-o[2]]
        if r['axis'] in ('x','z'):r['angle']=-r['angle']
    return e


def main():
    pixels=[(0,0,0,0)]*1024
    for x,c in enumerate(PALETTE):pixels[x]=(*c,255)
    # Painted features replace the former stacked eye and nose cuboids.
    for y in range(2,6):
        for x in range(6):pixels[y*32+x]=(*PALETTE[0],255)
    for x in (1,4):pixels[3*32+x]=(*PALETTE[5],255)
    for y in range(2,4):
        for x in range(8,12):pixels[y*32+x]=(*PALETTE[3],255)
    for x in (9,10):pixels[2*32+x]=(*PALETTE[4],255)
    write_png(ROOT/'assets/minecraft/textures/block/ivy_cake_dog.png',32,32,pixels)
    source=ROOT/'tools/ivy-cake/source'
    full=json.loads((source/'cake.json').read_text())
    # Rotate all fruit, flowers and Ivy together around the cake centre.
    decorations=[rotate_cake(e) for e in full['elements'][4:]]
    for path in (ROOT/'assets/minecraft/models/block').glob('*cake*.json'):
        data=json.loads((source/path.name).read_text())
        data['textures']={k:v if ':' in v else 'minecraft:'+v for k,v in data['textures'].items()}
        data['textures']['ivy']='minecraft:block/ivy_cake_dog'
        bites=int(path.stem[-1]) if path.stem.startswith('cake_slice') else 0
        cut=1+2*bites
        base=data['elements'][0]
        for f in ('up','down'):
            if f in base['faces']:base['faces'][f]['rotation']=180
        elements=[base]
        for source_part in decorations:
            part=copy.deepcopy(source_part)
            lo,hi=part['from'],part['to']
            # Keep scattered ground petals; eat the toppings from the vanilla cut side.
            if hi[1]>1:
                if (lo[0]+hi[0])/2 < cut:continue
                part['from'][0]=max(lo[0],cut)
            elements.append(part)
        for original in topper():
            part=rotate_cake(original)
            if bites>=5:
                # The topper now stands on the opposite side, so it falls later.
                part.pop('rotation',None)
                lo,hi=part['from'],part['to']
                part['from']=[lo[0]-6,(lo[2]-10)*.65+.05,15-hi[1]]
                part['to']=[hi[0]-6,(hi[2]-10)*.65+.05,15-lo[1]]
                swap={'south':'up','north':'down','up':'north','down':'south','east':'east','west':'west'}
                part['faces']={swap[f]:v for f,v in part['faces'].items()}
                part['name']=part['name'].replace('ivy_','ivy_fallen_',1)
            elements.append(part)
        if path.stem=='template_cake_with_candle':
            # Keep the vanilla candle socket centred; the cake decoration rotates around it.
            elements += [rotate_cake(e) for e in data['elements'] if any(f['texture']=='#candle' for f in e.get('faces',{}).values())]
        data['elements']=elements
        data['credit']='Cake by Hoffen @_InkGhoul; Ivy Labrador adaptation by Henry / Realms Beyond'
        path.write_text(json.dumps(data,indent=2)+'\n')

if __name__=='__main__':main()
