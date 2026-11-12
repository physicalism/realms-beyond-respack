"""Small RGBA PNG reader for previews; no external dependencies."""
import struct,zlib
from generate import write_png
class Image:
    def __init__(self,w,h,pixels): self.size=(w,h);self.pixels=pixels
    def load(self): return self
    def __getitem__(self,xy): return self.pixels[xy[1]*self.size[0]+xy[0]]
    def __setitem__(self,xy,v): self.pixels[xy[1]*self.size[0]+xy[0]]=v
    def save(self,path):
        from pathlib import Path
        write_png(Path(path),*self.size,self.pixels)
    @classmethod
    def new(cls,mode,size,colour): return cls(*size,[colour]*(size[0]*size[1]))
    @classmethod
    def open(cls,path):
        from pathlib import Path
        b=Path(path).read_bytes();pos=8;packed=b''
        while pos<len(b):
            n=struct.unpack('>I',b[pos:pos+4])[0];kind=b[pos+4:pos+8];data=b[pos+8:pos+8+n];pos+=n+12
            if kind==b'IHDR':w,h,depth,colour,_,_,_=struct.unpack('>IIBBBBB',data)
            elif kind==b'IDAT':packed+=data
        if (depth,colour)!=(8,6):raise ValueError('Preview requires RGBA8 PNG')
        raw=zlib.decompress(packed);stride=w*4;previous=[0]*stride;pixels=[]
        for y in range(h):
            f=raw[y*(stride+1)];row=list(raw[y*(stride+1)+1:(y+1)*(stride+1)])
            for x in range(stride):
                a=row[x-4] if x>=4 else 0;c=previous[x-4] if x>=4 else 0;u=previous[x]
                p=a+u-c;ds=[abs(p-a),abs(p-u),abs(p-c)];paeth=[a,u,c][ds.index(min(ds))]
                row[x]=(row[x]+[0,a,u,(a+u)//2,paeth][f])%256
            pixels += [tuple(row[x:x+4]) for x in range(0,stride,4)];previous=row
        return cls(w,h,pixels)
