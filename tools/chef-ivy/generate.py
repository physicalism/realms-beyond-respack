"""Restore the original Chef Ivy painting; experimental edits have been reverted."""
from pathlib import Path
import struct
import zlib
ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent / 'source'
def read(path):
    data = path.read_bytes(); pos = 8; packed = b''
    while pos < len(data):
        n = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]; part = data[pos+8:pos+8+n]; pos += n+12
        if kind == b'IHDR':
            w,h,depth,colour,_,_,interlace = struct.unpack('>IIBBBBB', part)
        elif kind == b'IDAT': packed += part
    assert depth == 8 and colour in (2,6) and interlace == 0
    channels = 3 if colour == 2 else 4
    raw = zlib.decompress(packed); stride = w*channels; previous = [0]*stride; pixels=[]
    for y in range(h):
        f=raw[y*(stride+1)]; row=list(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        for x in range(stride):
            a=row[x-channels] if x>=channels else 0
            b=previous[x]; c=previous[x-channels] if x>=channels else 0
            p=a+b-c; distances=[abs(p-a),abs(p-b),abs(p-c)]
            predictor=[a,b,c][distances.index(min(distances))]
            row[x]=(row[x]+[0,a,b,(a+b)//2,predictor][f])%256
        pixels += [tuple(row[x:x+3]) for x in range(0,stride,channels)]
        previous=row
    return w,h,pixels
def write(path,w,h,pixels):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+bytes(v for pixel in pixels[y*w:(y+1)*w] for v in pixel) for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
if __name__ == '__main__':
    import shutil
    # Henry reverted all Chef Ivy edits. Preserve the exact original texture.
    target=ROOT/'assets/realm/textures/item/painting/ivy_chef.png'
    shutil.copy2(SOURCE/'original.png',target)
    w,h,pixels=read(target)
    scale=16
    preview=[pixels[(y//scale)*w+x//scale] for y in range(h*scale) for x in range(w*scale)]
    write(ROOT/'builds/chef-ivy/kibble-preview.png',w*scale,h*scale,preview)
