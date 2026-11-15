"""Import and adapt This Rocks! art; never install or execute its mod code."""
from pathlib import Path
import argparse
import copy
import hashlib
import itertools
import json
import math
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SIZES = ['tiny', 'small', 'medium', 'large']
ROCKS = ['rock', 'andesite_rock', 'diorite_rock', 'granite_rock', 'gravel_rock',
         'sand_rock', 'red_sand_rock', 'ice_rock', 'end_stone_rock',
         'netherrack_rock', 'soul_soil_rock']
WOODS = ['oak','spruce','birch','jungle','acacia','dark_oak','mangrove',
         'cherry','pale_oak','poplar','bamboo','crimson','warped']
NAMES = [f'{r}_{s}' for r in ROCKS for s in SIZES]
NAMES += [f'{w}_stick_{s}' for w in WOODS for s in SIZES[1:]]
NAMES += ['pinecone'] + [f'seashell_{c}' for c in ['white','pink','yellow']]
NAMES += [f'starfish_{c}' for c in ['orange','pink','red']]
NAMES += ['geyser_off','geyser_on','nether_geyser_off','nether_geyser_on','snowy_geyser_off']

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')

def transformed(point, rotation):
    if not rotation or not rotation['angle']: return list(point)
    origin = rotation['origin']; axis = 'xyz'.index(rotation['axis'])
    a,b = [(1,2),(2,0),(0,1)][axis]
    p = [v-o for v,o in zip(point,origin)]
    c,s = math.cos(math.radians(rotation['angle'])), math.sin(math.radians(rotation['angle']))
    p[a],p[b] = c*p[a]-s*p[b], s*p[a]+c*p[b]
    if rotation.get('rescale'):
        p[a] /= c; p[b] /= c
    return [v+o for v,o in zip(p,origin)]

def adapt(data):
    data = copy.deepcopy(data)
    # Vanilla Java elements accept only these angles. The mod's starfish uses
    # additional angles; snap those arms to legal rotations, retaining its UVs.
    for el in data['elements']:
        rot = el.get('rotation')
        if rot:
            rot['angle'] = min([-45,-22.5,0,22.5,45], key=lambda v:abs(v-rot['angle']))
    points = [transformed(p,e.get('rotation')) for e in data['elements']
              for p in itertools.product(*zip(e['from'],e['to']))]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    scale = min(1, 14/max(hi[0]-lo[0],hi[2]-lo[2]), 12/(hi[1]-lo[1]))
    shift = [8-(lo[0]+hi[0])*scale/2, .02-lo[1]*scale,
             8-(lo[2]+hi[2])*scale/2]
    for el in data['elements']:
        for key in ['from','to']:
            el[key] = [round(v*scale+d,5) for v,d in zip(el[key],shift)]
        if 'rotation' in el:
            el['rotation']['origin'] = [round(v*scale+d,5) for v,d in zip(el['rotation']['origin'],shift)]
        for f in el['faces'].values(): f.pop('cullface',None)
    data['parent'] = 'minecraft:block/block'
    data['display'] = {
        'gui':{'rotation':[30,225,0],'translation':[0,3,0],'scale':[.9,.9,.9]},
        'ground':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1,1,1]},
        'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1,1,1]}}
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--jar',type=Path); args=ap.parse_args()
    source=HERE/'source'
    if args.jar:
        with zipfile.ZipFile(args.jar) as z:
            for name in z.namelist():
                if name.startswith('assets/rocks/models/block/') and name.endswith('.json'):
                    dest=source/'models'/Path(name).name; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(name))
                if name.startswith('assets/rocks/textures/block/') and name.endswith('.png'):
                    dest=source/'textures'/Path(name).name; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(name))
        (HERE/'source-sha256.txt').write_text(hashlib.sha256(args.jar.read_bytes()).hexdigest()+'\n')
    def resolve(name):
        d=json.loads((source/'models'/f'{name}.json').read_text())
        parent=d.get('parent','')
        inherited=resolve(parent.split('/')[-1]) if parent.startswith('rocks:') else {}
        return {**inherited,**d,'textures':{**inherited.get('textures',{}),**d.get('textures',{})}}
    def normalise(t):
        if t.startswith('#'):return t
        if t.startswith('rocks:'):return t.replace('rocks:block/','realm:block/this_rocks/')
        return t if ':' in t else 'minecraft:'+t
    models={}; entries=[]
    for name in NAMES:
        m=adapt(resolve(name)); m['textures']={k:normalise(v) for k,v in m['textures'].items()}
        models[name]=m
        write(ROOT/f'assets/realm/models/block/this_rocks/{name}.json',m)
        item=f'realm:this_rocks/{name}'
        write(ROOT/f'assets/realm/items/this_rocks/{name}.json',{'model':{'type':'minecraft:model','model':f'realm:block/this_rocks/{name}'}})
        entries.append({'name':name,'item_model':item,'model':f'realm:block/this_rocks/{name}'})
    for p in (source/'textures').glob('*.png'):
        d=ROOT/'assets/realm/textures/block/this_rocks'/p.name;d.parent.mkdir(parents=True,exist_ok=True); d.write_bytes(p.read_bytes())
    def combined(base,name):
        m=copy.deepcopy(models[name]); m.pop('display',None)
        for e in m['elements']:
            for k in ['from','to']:e[k][1]+=16
            if 'rotation'in e:e['rotation']['origin'][1]+=16
        # Give the substrate independent slots so imported #0 etc cannot collide.
        cube={'from':[0,0,0],'to':[16,16,16],'faces':{
            side:{'texture':'#substrate','uv':[0,0,16,16],'cullface':side}
            for side in ['up','down','north','south','east','west']}}
        tex='minecraft:block/'+base
        m['textures'].update({'substrate':tex,'particle':tex}); m['elements'].insert(0,cube)
        return m
    natural=[]
    # Preserve the approved rocks and reduced huge-rock probability. Extras
    # add only about 0.5% grass coverage; no automatic geysers or odd wood colours.
    grass_path=ROOT/'assets/minecraft/blockstates/grass_block.json'
    grass=json.loads(grass_path.read_text()); vs=grass['variants']['snowy=false']
    vs[:]=[v for v in vs if not v['model'].startswith('realm:block/this_rocks/')]
    for i,v in enumerate(vs):v['weight']=2425 if i<4 else (24 if i<14 else 6)
    extras=[(f'{w}_stick_{s}',weight) for w in ['oak','spruce','birch']
            for s,weight in [('small',9),('medium',4),('large',1)]]+[('pinecone',8)]
    # Reuse the existing grass cube/tint/overlay exactly.
    grass_base=json.loads((ROOT/'assets/realm/models/block/lawn_decor/rock/rock_00.json').read_text())
    for name,weight in extras:
        m=combined('grass_block',name)
        m['elements']=copy.deepcopy(grass_base['elements'][:2])+m['elements'][1:]
        for e in m['elements'][:2]:
            for f in e['faces'].values():f['texture']='#grass_'+f['texture'][1:]
        m['textures'].update({'grass_'+k:v for k,v in grass_base['textures'].items() if k!='rock'})
        m['textures']['particle']='minecraft:block/dirt'
        identifier=f'realm:block/this_rocks/natural/grass_{name}'
        write(ROOT/f'assets/realm/models/block/this_rocks/natural/grass_{name}.json',m)
        vs.append({'model':identifier,'weight':weight,'y':(len(vs)%4)*90}); natural.append(identifier)
    write(grass_path,grass)
    # New shell/starfish designs share the existing rates, keeping existing art.
    sand_path=ROOT/'assets/minecraft/blockstates/sand.json'
    sand=json.loads(sand_path.read_text()); vs=sand['variants']['']
    vs[:]=[v for v in vs if not v['model'].startswith('realm:block/this_rocks/')]
    # Double all old weights, then split shell/starfish shares across both designs.
    for i,v in enumerate(vs):v['weight']=7912 if i==0 else (2 if i==16 else (2 if 1<=i<=12 else 6))
    for name,weight in [(f'seashell_{c}',8) for c in ['white','pink','yellow']]+[(f'starfish_{c}',w) for c,w in [('orange',1),('pink',1),('red',0)]]:
        if not weight:continue
        identifier=f'realm:block/this_rocks/natural/sand_{name}'
        write(ROOT/f'assets/realm/models/block/this_rocks/natural/sand_{name}.json',combined('sand',name))
        vs.append({'model':identifier,'weight':weight,'y':(len(vs)%4)*90}); natural.append(identifier)
    write(sand_path,sand)
    # Red starfish is also included naturally; use weights 3 old : 1 per new
    # colour, total 6 / 12000 = the original 0.05%.
    for v in vs:v['weight']*=3
    vs[16]['weight']=6
    # Existing two new colours now weigh 3 each; add red and take three from old.
    vs[16]['weight']=3
    name='starfish_red'; identifier=f'realm:block/this_rocks/natural/sand_{name}'
    write(ROOT/f'assets/realm/models/block/this_rocks/natural/sand_{name}.json',combined('sand',name))
    vs.append({'model':identifier,'weight':3,'y':0});natural.append(identifier)
    write(sand_path,sand)
    manifest={'source':'This Rocks! 1.10.0 / Motschen and TeamMidnightDust',
              'items':entries,'natural_models':natural,'grass_extras':len(extras),
              'sand_total_weight':sum(v['weight']for v in vs)}
    write(HERE/'manifest.json',manifest)
    commands=['# Each line is a separate Minecraft chat command. Requires creative/operator permissions.',
              '# Item displays: decorations only; use ground context to preserve scale.',
              '# Remove only this preview: /kill @e[type=minecraft:item_display,tag=rb_nature_preview]']
    for i,e in enumerate(entries):
        name=e['name'];item=e['item_model'];x=i%10;z=i//10
        commands += [f'# {name}',f'/give @s minecraft:paper[minecraft:item_model="{item}"]',
                     f'/summon minecraft:item_display ~{x*1.5:g} ~ ~{z*1.5:g} {{Tags:["rb_nature_preview"],item:{{id:"minecraft:paper",count:1,components:{{"minecraft:item_model":"{item}"}}}},item_display:"ground"}}']
    (HERE/'COMMANDS.txt').write_text('\n'.join(commands)+'\n')
    print(f'Adapted {len(entries)} placeable models; grass extras {len(extras)}; sand total {manifest["sand_total_weight"]}.')

if __name__=='__main__':main()
