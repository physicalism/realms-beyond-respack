"""Refresh style-guide reference images from current assets; not in-game screenshots.
Run with a Python containing Pillow and numpy. Existing animation renderers handle
model geometry/UVs; painting images are nearest-neighbour canvas texture studies.
"""
import json, shutil, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artstyle/images'
OUT.mkdir(parents=True,exist_ok=True)

def resource(kind,identifier):
 ns,name=identifier.split(':');return ROOT/'assets'/ns/kind/(name+('.png' if kind=='textures' else '.json'))

def resolved(identifier):
 d=json.loads(resource('models',identifier).read_text())
 if 'parent' in d and d['parent'].startswith('realm:'):
  parent=resolved(d['parent']);parent.update({k:v for k,v in d.items() if k!='textures'});parent['textures']={**parent.get('textures',{}),**d.get('textures',{})};return parent
 return d

rows=[]
for item in sorted((ROOT/'assets/realm/items').glob('painting_ivy*.json')):
 name=item.stem; identifier=json.loads(item.read_text())['model']['model'];d=resolved(identifier)
 canvas=resource('textures',d['textures']['canvas'])
 im=Image.open(canvas).convert('RGBA'); factor=max(1,min(200//im.width,340//im.height)); im=im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST)
 im.save(OUT/(name+'.png'));rows.append((name,im))
sheet=Image.new('RGB',(1200,880),'#272d33');draw=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(rows):
 x=(i%5)*240;y=(i//5)*440
 sheet.paste(im,(x+(240-im.width)//2,y+42),im)
 draw.text((x+10,y+12),name.replace('painting_ivy','Ivy'),fill='#eee0ca')
sheet.save(OUT/'ivy-paintings-current.png')
# Current static models, rendered by the existing software renderer.
for name,scale in [('blacksmith_sign',14),('blacksmith_hammer',26)]:
 model=ROOT/f'assets/realm/models/item/decorations/{name}.json'
 d=json.loads(model.read_text());texture=resource('textures',next(v for k,v in d['textures'].items() if k!='particle'))
 if name == 'blacksmith_hammer':
  bounds=[[(min(e['from'][axis] for e in d['elements'])),max(e['to'][axis] for e in d['elements'])] for axis in range(3)]
  centre=[sum(b)/2 for b in bounds]
  code=(ROOT/'tools/blacksmith-sign/render.py').read_text().replace('p[0] - 0, p[1] - 15, p[2] - 8',f'p[0] - {centre[0]}, p[1] - {centre[1]}, p[2] - {centre[2]}')
  args=sys.argv
  sys.argv=['render.py',str(model),str(texture),str(OUT/(name+'.png')),'-25','15','24']
  try: exec(compile(code,'reference-hammer-render','exec'),{'__name__':'__main__'})
  finally: sys.argv=args
 else:
  subprocess.run([sys.executable,str(ROOT/'tools/blacksmith-sign/render.py'),str(model),str(texture),str(OUT/(name+'.png')),'-25','15',str(scale)],check=True)
# Preserve existing reference boards inside the pack repository, with provenance
# in SOURCES.md. These are older offline boards, not fresh in-game screenshots.
for source,target in [('Origin-Realms-Blacksmith-Models.png','origin-realms-blacksmith.png'),('origin-realms-all-paintings.png','origin-realms-paintings.png'),('origin-realms-paintings-models.png','origin-realms-painting-models.png')]:
 shutil.copy2(ROOT.parent/'previews'/source,OUT/target)
print('Saved current painting studies, static blacksmith renders, and Origin Realms boards.')
