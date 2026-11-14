#!/usr/bin/env python3
"""Offline geometry contact sheet; not an in-game or shader preview. Needs Pillow/numpy."""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'builds/elphaba-backups/2026-11-13-refinement-preview.png'

def rot(axis,deg):
 c,s=math.cos(math.radians(deg)),math.sin(math.radians(deg))
 return np.array({'x':[[1,0,0],[0,c,-s],[0,s,c]],'y':[[c,0,s],[0,1,0],[-s,0,c]],'z':[[c,-s,0],[s,c,0],[0,0,1]]}[axis])

def render(model,kind,yaw,pitch,size=(340,470),context=None):
 tex=Image.open(ROOT/f'assets/realm/textures/item/elphaba_{kind}.png').convert('RGB')
 camera=rot('x',pitch)@rot('y',yaw)
 im=Image.new('RGB',size,'#252b34');draw=ImageDraw.Draw(im)
 quads=[]
 for e in model['elements']:
  a,b=e['from'],e['to'];x,y,z=a;X,Y,Z=b
  faces={'north':([(X,Y,z),(x,Y,z),(x,y,z),(X,y,z)],(0,0,-1)),
   'south':([(x,Y,Z),(X,Y,Z),(X,y,Z),(x,y,Z)],(0,0,1)),
   'west':([(x,Y,z),(x,Y,Z),(x,y,Z),(x,y,z)],(-1,0,0)),
   'east':([(X,Y,Z),(X,Y,z),(X,y,z),(X,y,Z)],(1,0,0)),
   'up':([(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],(0,1,0)),
   'down':([(x,y,Z),(X,y,Z),(X,y,z),(x,y,z)],(0,-1,0))}
  er=e.get('rotation',{});R=rot(er.get('axis','x'),er.get('angle',0));origin=np.array(er.get('origin',[8]*3))
  d=model['display'].get(context,{}) if context else {}
  dr=d.get('rotation',[0]*3);D=rot('x',dr[0])@rot('y',dr[1])@rot('z',dr[2])
  for face,f in e['faces'].items():
   points,n=faces[face];n=camera@D@R@np.array(n)
   if n[2] <= 0:continue
   pts=[]
   for p in points:
    q=R@(np.array(p)-origin)+origin-8
    q=D@(q*np.array(d.get('scale',[1]*3)))+np.array(d.get('translation',[0]*3))
    pts.append(camera@q)
   uv=f['uv'];u=int((uv[0]+uv[2])/32*tex.width);v=int((uv[1]+uv[3])/32*tex.height)
   col=tex.getpixel((min(u,tex.width-1),min(v,tex.height-1)))
   light=.65+.35*max(0,float(n@np.array([-.3,.65,.7])))
   col=tuple(min(255,int(c*light)) for c in col)
   quads.append((sum(p[2] for p in pts)/4,pts,col))
 scale=10 if not context else 15
 centre_y=3 if kind=='broom' else 13
 if context:centre_y=0
 for _,pts,col in sorted(quads,key=lambda q:q[0]):
  draw.polygon([(size[0]/2+p[0]*scale,size[1]/2-(p[1]-centre_y)*scale) for p in pts],fill=col)
 return im

sheet=Image.new('RGB',(1360,1040),'#161a21');draw=ImageDraw.Draw(sheet)
for row,kind in enumerate(['broom','hat']):
 model=json.loads((ROOT/f'assets/realm/models/item/elphaba_{kind}.json').read_text())
 for col,(yaw,pitch,label) in enumerate([(180,0,'Front'),(145,18,'Three-quarter'),(90,0,'Side'),(0,-12,'Back / underside')]):
  im=render(model,kind,yaw,pitch);sheet.paste(im,(col*340,row*520+30))
  draw.text((col*340+15,row*520+12),f'{kind.title()} — {label}',fill='white')
sheet.save(OUT);print(OUT)
# Display-context rotations/framing only, without claiming a simulated player camera.
sheet=Image.new('RGB',(1360,1040),'#161a21');draw=ImageDraw.Draw(sheet)
for row,kind in enumerate(['broom','hat']):
 model=json.loads((ROOT/f'assets/realm/models/item/elphaba_{kind}.json').read_text())
 for col,ctx in enumerate(['gui','firstperson_righthand','thirdperson_righthand','ground']):
  im=render(model,kind,0,0,context=ctx);sheet.paste(im,(col*340,row*520+30))
  draw.text((col*340+15,row*520+12),f'{kind.title()} — {ctx}',fill='white')
p=OUT.with_name('2026-11-13-context-preview.png');sheet.save(p);print(p)
