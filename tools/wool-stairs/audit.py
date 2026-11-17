#!/usr/bin/env python3
"""Check exported surface coverage, texture slots, and Fusion neighbour gates."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('wool_generator',Path(__file__).with_name('generate.py'))
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def check(condition,message):
    if not condition:raise AssertionError(message)


def is_base(element):
    return all(float(v).is_integer() for v in element['from']+element['to'])


def planes(model):
    # Quarter-pixel raster of every face, ignoring normal sign: opposite-facing
    # coplanar faces also intersect and can flicker under shaders.
    result=Counter()
    for element in model['elements']:result.update(gen.face_cells(element))
    return result


def quads(model):
    result=Counter()
    for element in model['elements']:
        if not is_base(element):continue
        fr,to=element['from'],element['to']
        for direction,face in element['faces'].items():
            axis=next(i for i,v in enumerate(gen.DIRECTIONS[direction]) if v)
            plane=fr[axis] if gen.DIRECTIONS[direction][axis]<0 else to[axis]
            axes=[i for i in range(3) if i!=axis]
            for a in range(fr[axes[0]],to[axes[0]]):
                for b in range(fr[axes[1]],to[axes[1]]):
                    result[(direction,plane,a,b)]+=1
            uv=face.get('uv',[])
            if uv:check(uv[0]!=uv[2] and uv[1]!=uv[3],f'Degenerate UV: {uv}')
    return result


def expected(cells):
    result=Counter()
    for p in cells:
        for direction,delta in gen.DIRECTIONS.items():
            if tuple(a+b for a,b in zip(p,delta)) in cells:continue
            axis=next(i for i,v in enumerate(delta) if v)
            plane=p[axis]+(delta[axis]>0)
            axes=[i for i in range(3) if i!=axis]
            result[(direction,plane,p[axes[0]],p[axes[1]])]+=1
    return result


def predicate(value,world):
    if value['type']=='and':return all(predicate(p,world) for p in value['predicates'])
    check(value['type']=='match_state','Unexpected predicate')
    state=world.get(tuple(value['offset']),{'block':'minecraft:air'})
    return state['block'] in value['blocks'] and all(state.get(k) in v for k,v in value['properties'].items())


def main(jar):
    manifest=json.loads((ROOT/'tools/wool-stairs/generated.json').read_text())
    paths=manifest['paths']
    check(len(paths)==len(set(paths)),'Duplicate manifest paths')
    with zipfile.ZipFile(jar) as z:
        def read_model(identifier,seen=()):
            check(identifier not in seen,'Parent cycle')
            if ':' not in identifier:identifier='minecraft:'+identifier
            ns,name=identifier.split(':',1)
            filename=f'assets/{ns}/models/{name}.json'
            path=ROOT/filename
            raw=json.loads(path.read_text() if path.exists() else z.read(filename))
            parent=read_model(raw['parent'],seen+(identifier,)) if 'parent' in raw else {}
            return {**parent,**raw,'textures':{**parent.get('textures',{}),**raw.get('textures',{})}}
        vanilla_states=json.loads(z.read('assets/minecraft/blockstates/white_wool_stairs.json'))['variants']
        models=0
        for filename in paths:
            path=ROOT/filename; data=json.loads(path.read_text())
            if '/models/' not in filename:continue
            ns=filename.split('/')[1];identifier=ns+':'+filename.split('/models/')[1][:-5]
            resolved=read_model(identifier)
            slots=resolved['textures']
            for element in resolved['elements']:
                for face in element['faces'].values():
                    texture=face['texture'];seen=set()
                    while texture.startswith('#'):
                        key=texture[1:]
                        check(key in slots and key not in seen,f'Bad slot {identifier} {key}')
                        seen.add(key);texture=slots[key]
                    ns,name=texture.split(':',1)
                    file=f'assets/{ns}/textures/{name}.png'
                    check((ROOT/file).exists() or file in z.namelist(),f'Missing texture {texture}')
            if 'elements' in data:check(all(n==1 for n in planes(data).values()),f'Duplicate coplanar faces: {filename}')
            models+=1
        gates=0
        for colour in gen.COLOURS:
            modifier=json.loads((ROOT/f'assets/realm/fusion/model_modifiers/blocks/wool_spill_{colour}.json').read_text())
            check(len(modifier['append_models'])==40,'Missing stair orientations')
            check(len({e['model'] for e in modifier['append_models']})==24,'Spill geometry should be shared between equivalent stair states')
            for entry in modifier['append_models']:
                self_test,other_test=entry['conditions']['predicates']
                props={k:v[0] for k,v in self_test['properties'].items()}
                source={'block':f'minecraft:{colour}_wool_stairs',**props}
                other={'block':'minecraft:stone_brick_stairs',**props}
                offset=tuple(other_test['offset'])
                world={(0,0,0):source,offset:other}
                check(predicate(entry['conditions'],world),'Valid seam rejected')
                for key,value in [('block','minecraft:stone_bricks'),('block','minecraft:red_wool_stairs'),('half','top'),('waterlogged','true'),('facing',next(f for f in ('east','west','north','south') if f!=props['facing'])),('shape',next(s for s in ('straight','inner_left') if s!=props['shape']))]:
                    bad={**world,offset:{**other,key:value}}
                    check(not predicate(entry['conditions'],bad),f'Unsafe seam accepted {key}={value}')
                # Compare every exported spill texel against both existing
                # surfaces, ignoring normal sign: opposite-facing coplanar
                # faces are also an intersection and can flicker under shaders.
                suffix='_inner' if 'inner' in props['shape'] else '_outer' if 'outer' in props['shape'] else ''
                high=gen.SHAPES[suffix]
                key=','.join(f'{k}={props[k]}' for k in ('facing','half','shape'))
                turns=vanilla_states[key].get('y',0)//90
                side=next(s for s in (-1,1) if tuple(gen.rot_point((0,0,s),turns,True))==offset)
                host={(x,y,z) for x in range(16) for z in (range(-16,0) if side==-1 else range(16,32))
                      for y in range(gen.height(high,x,z+16 if side==-1 else z-16))}
                # Hosts extend beyond the block bounds in source coordinates;
                # UVs are irrelevant to this geometric intersection test.
                host_model={'elements':gen.rotate(gen.surface(host),turns)}
                source_model={'elements':[e for v in range(4) for e in gen.rotate(gen.stair_elements(suffix,v),turns)]}
                spill_model=json.loads((ROOT/('assets/realm/models/'+entry['model'].split(':',1)[1]+'.json')).read_text())
                def plane_keys(model):
                    return set(planes(model))
                existing=plane_keys(host_model)|plane_keys(source_model)
                check(not plane_keys(spill_model)&existing,f'Coplanar spill contact: {entry["model"]}')
                check(not predicate(entry['conditions'],{(0,0,0):source}),'Spill into air')
                check(not predicate(entry['conditions'],{**world,(0,0,0):{**source,'waterlogged':'true'}}),'Waterlogged source')
                gates+=1
    for suffix,high in gen.SHAPES.items():
        data=json.loads((ROOT/f'assets/realm/models/block/carpeted_wool_stairs{suffix}.json').read_text())
        check(quads(data)==expected(gen.volume(high)),f'Incomplete stair surface {suffix}')
        variants=[]
        for v in range(4):
            name=f'carpeted_wool_stairs{suffix}'+('' if v==0 else f'_v{v}')+'.json'
            m=json.loads((ROOT/'assets/realm/models/block'/name).read_text())
            check(quads(m)==quads(data),'Variant changed base geometry')
            variants.append(json.dumps(m['elements'],sort_keys=True))
            # Every tuft is anchored: most of its footprint sits on, or is
            # sunk into, the tread it decorates. Nothing hovers in the air.
            heights=gen.heightmap(high)
            tufts=[e for e in m['elements'] if not is_base(e)]
            check(len(tufts)>=3,f'Too little fluff: {name}')
            check(all(t['from'][1]==int(t['from'][1]) for t in tufts) or gen.EDGE_LUMPS,f'Edge lumps present: {name}')
            for t in tufts:
                cells=[(x,z) for x in range(int(t['from'][0]//1),int(-(-t['to'][0]//1)))
                       for z in range(int(t['from'][2]//1),int(-(-t['to'][2]//1)))]
                anchored=[c for c in cells if c in heights and t['from'][1]<=heights[c]<=t['to'][1]]
                check(len(anchored)*2>=len(cells),f'Floating tuft {t["from"]} in {name}')
                check(t['to'][1]-heights[anchored[0]]<=gen.LIFT,f'Tuft too tall in {name}')
                check('up' in t['faces'],f'Tuft without top in {name}')
                for other in tufts:
                    check(other is t or not gen.boxes_touch(t,other,1),f'Touching tufts in {name}')
    # Every fluff face samples one texel per model pixel (no stretched fibres).
    for filename in paths:
        if '/carpeted_wool_stairs' not in filename or '/realm/' not in filename:continue
        for e in json.loads((ROOT/filename).read_text())['elements']:
            if is_base(e):continue
            size=[b-a for a,b in zip(e['from'],e['to'])]
            for direction,face in e['faces'].items():
                axis=next(i for i,v in enumerate(gen.DIRECTIONS[direction]) if v)
                a,b=[i for i in range(3) if i!=axis]
                if direction in ('up','down'):want=(size[0],size[2])
                elif axis==0:want=(size[2],size[1])
                else:want=(size[0],size[1])
                uv=face['uv'];got=(abs(uv[2]-uv[0]),abs(uv[3]-uv[1]))
                if face.get('rotation',0)%180:got=got[::-1]
                check(got==want,f'Stretched fluff UV: {filename} {direction}')
    # Regression: every horizontal strip must sample one texel per model pixel,
    # including the world-rotated north/south strips and wrapped border texels.
    for filename in paths:
        if '/wool_spill/' not in filename and '/carpeted_wool_stairs' not in filename:continue
        data=json.loads((ROOT/filename).read_text())
        for e in data.get('elements',[]):
            for direction,face in e['faces'].items():
                if direction not in ('up','down'):continue
                uv=face['uv']
                u,v=abs(uv[2]-uv[0]),abs(uv[3]-uv[1])
                if face.get('rotation',0)%180:u,v=v,u
                check((u,v)==(e['to'][0]-e['from'][0],e['to'][2]-e['from'][2]),f'Stretched horizontal UV: {filename}')
    print(f'Checked {models} resolved models, {gates} Fusion seams, all surface faces, anchored non-touching fluff, four variants, and unsafe neighbour cases.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--client-jar',type=Path,default=Path.home()/'Library/Application Support/ModrinthApp/meta/versions/26.3-0.20.1/26.3-0.20.1.jar')
    main(parser.parse_args().client_jar)
