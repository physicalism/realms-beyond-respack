#!/usr/bin/env python3
"""Generate the compact forged keg spigot; north points away from wall z=16."""
import json, sys
from pathlib import Path
import struct, zlib
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[2]
# Five muted iron tones, plus restrained oak tones. All texels are opaque.
iron=['#131212','#201d1c','#2c2827','#393332','#49413e']
wood=['#553a1f', '#6b5332', '#805e36'] # Colours picked from the vanilla barrel_side PNG palette.
# Broad hand-placed clusters: bevel highlight, quiet forged patches, dark lower edge.
metal=[
 '3333433332333233',
 '2223322222222222',
 '2222222332221222',
 '2212222222221222',
 '2222222223322222',
 '1222122222222221',
 '1111111111111111',
 '0000000000000000',
]
oak=[
 '2222222222222222',
 '1111211111112111',
 '1111111011111111',
 '0111111011110111',
 '1111111111110111',
 '1110111111111111',
 '0000000000000000',
 '0000000000000000',
]
# Each face gets its own painted tile at two texels per model unit.
size=128
atlas=[[(32,29,28)]*size for _ in range(size)]
def chunk(t,d):
 return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
face_index=0
els=[]
def box(name,a,b,wood=False,omit=()):
 faces={}
 for f in ['north','south','east','west','up','down']:
  if f in omit:continue
  dx,dy,dz=[b[i]-a[i] for i in range(3)]
  w,h=(dx,dz) if f in ('up','down') else (dz,dy) if f in ('east','west') else (dx,dy)
  global face_index
  import math
  tw,th=max(1,math.ceil(w*2)),max(1,math.ceil(h*2))
  ox,oy=(face_index%10)*12,(face_index//10)*12
  face_index+=1
  for py in range(th):
   for px in range(tw):
    if wood:
     base=(107,79,46)
     grain=-16 if (py+px//4)%4==2 else 5 if py%3==0 else 0
     delta=grain+(13 if py==0 else -15 if py==th-1 else 0)
    else:
     base=(39,36,35)
     delta=(20 if py==0 else -12 if py==th-1 else 0)
     delta+=7 if px==0 else -5 if px==tw-1 else 0
     delta+=((px//2*7+py//2*3+face_index)%5-2)*2
     if (px+face_index*3)%11==0 and py==1:delta+=12
     if f=='down':delta-=10
    atlas[oy+py][ox+px]=tuple(max(8,min(255,c+delta)) for c in base)
  faces[f]={'uv':[ox/8,oy/8,(ox+tw)/8,(oy+th)/8],'texture':'#tap'}
 els.append({'name':name,'from':a,'to':b,'faces':faces})
box('mounting collar',[6,5,15],[10,9,16],omit=('south',))
box('horizontal body',[7,6,10],[9,8,15])
box('short downturned nozzle',[7,4,10],[9,6,12],omit=('up',))
# An inset dark outlet is represented by the bottom face, not a false open tube.
# Low raised valve housing and a slimmer stem give the handle a clear joint.
box('valve housing',[6.5,8,11.5],[9.5,9,13.5],omit=())
box('valve stem',[7.5,9,12],[8.5,10,13],omit=('down','up'))
# Split the grip at the band: adjacent faces are omitted to avoid overlapping surfaces.
box('oak left grip',[5,10,12],[7.5,11,13],wood=True,omit=('east',))
box('oak right grip',[8.5,10,12],[11,11,13],wood=True,omit=('west',))
box('handle iron band',[7.5,9.75,11.75],[8.5,11.25,13.25])
# Four narrow rim walls surround a recessed outlet; the nozzle underside closes it above.
box('nozzle rim front',[6.75,3.5,9.75],[9.25,4,10.25])
box('nozzle rim back',[6.75,3.5,11.75],[9.25,4,12.25])
box('nozzle rim left',[6.75,3.5,10.25],[7.25,4,11.75],omit=('north','south'))
box('nozzle rim right',[8.75,3.5,10.25],[9.25,4,11.75],omit=('north','south'))
pixels=bytearray()
for row in atlas:
 pixels.append(0)
 for rgb in row:pixels.extend(rgb)
p=root/'assets/realm/textures/block/brass_tap.png'
p.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
model={'credit':'Realms Beyond forged keg spigot','ambientocclusion':True,'textures':{'tap':'realm:block/brass_tap','particle':'realm:block/brass_tap'},'elements':els}
(root/'assets/realm/models/block/brass_tap.json').write_text(json.dumps(model,indent=2)+'\n')
# Attached tripwire returns to vanilla geometry, including powered movement.
variants={}
for attached in ('false','true'):
 for facing,rotation in [('north',0),('east',90),('south',180),('west',270)]:
  for powered in ('false','true'):
   model_id=('minecraft:block/tripwire_hook_attached'+('_on' if powered=='true' else '')) if attached=='true' else 'realm:block/brass_tap'
   variants[f'attached={attached},facing={facing},powered={powered}']={'model':model_id,'y':rotation}
(root/'assets/minecraft/blockstates/tripwire_hook.json').write_text(json.dumps({'variants':variants},indent=2)+'\n')
