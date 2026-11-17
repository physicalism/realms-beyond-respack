#!/usr/bin/env python3
"""Raised wool profiles with fixed fluff, UV variety, and conditional Fusion stair spills."""
import argparse
import random
import copy
import json
from collections import defaultdict
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
COLOURS = 'white orange magenta light_blue yellow lime pink gray light_gray cyan purple blue brown green red black'.split()
SHAPES = {'': {(1, 0), (1, 1)}, '_inner': {(1, 0), (1, 1), (0, 1)}, '_outer': {(1, 1)}}
DIRECTIONS = {'down':(0,-1,0), 'up':(0,1,0), 'north':(0,0,-1), 'south':(0,0,1), 'west':(-1,0,0), 'east':(1,0,0)}
WRITTEN = []


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, separators=(',', ':')) + '\n')
    WRITTEN.append(str(path.relative_to(ROOT)))


def height(high, x, z):
    return 16 if (x//8, z//8) in high else 8


def raised(high, x, z):
    # Dilate the upper tread into the recess by one pixel, making the front lip
    # part of the solid surface instead of laying faces on top of one another.
    return max(height(high, min(15,max(0,x+dx)), min(15,max(0,z+dz)))
               for dx,dz in ((0,0),(1,0),(-1,0),(0,1),(0,-1))) + 1


def volume(high):
    return {(x,y,z) for x in range(-1,16) for z in range(16)
            for y in range(9 if x == -1 else raised(high,x,z))}


def rectangles(points):
    points = set(points)
    while points:
        a,b = min(points)
        end = a+1
        while (end,b) in points: end += 1
        top = b+1
        while all((i,top) in points for i in range(a,end)): top += 1
        points.difference_update((i,j) for i in range(a,end) for j in range(b,top))
        yield a,b,end,top


def surface(cells, skip=None, blocked=frozenset()):
    planes = defaultdict(set)
    for x,y,z in cells:
        for direction,(dx,dy,dz) in DIRECTIONS.items():
            if direction == skip or (x+dx,y+dy,z+dz) in cells or (x+dx,y+dy,z+dz) in blocked: continue
            if dx: key=(direction,x+(dx>0)); point=(z,y)
            elif dy: key=(direction,y+(dy>0)); point=(x,z)
            else: key=(direction,z+(dz>0)); point=(x,y)
            planes[key].add(point)
    elements=[]
    for (direction,plane),points in sorted(planes.items()):
        # Never merge a wrapping edge texel with the main material face:
        # clamping that combined UV would stretch its border across the strip.
        groups=defaultdict(set)
        for a,b in points:
            first=-1 if a<0 else 1 if a>=16 else 0
            second=(-1 if b<0 else 1 if b>=16 else 0) if direction in ('up','down') else (0 if b<1 else 1)
            groups[(first,second)].add((a,b))
        patches=[rect for group in groups.values() for rect in rectangles(group)]
        for a,b,c,d in patches:
            if direction in ('east','west'):
                fr,to=[plane,b,a],[plane,d,c]
            elif direction in ('up','down'):
                fr,to=[a,plane,b],[c,plane,d]
            else: fr,to=[a,b,plane],[c,d,plane]
            # Clamp the extra edge texel to the wool's own border. All other
            # texels retain native scale; no new or recoloured image assets.
            if direction in ('up','down'):
                uv=[min(15,max(0,a)),min(15,max(0,b)),max(1,min(16,c)),max(1,min(16,d))]
                texture='#top' if direction == 'up' else '#bottom'
            else:
                uv=[min(15,max(0,a)),min(15,max(0,17-d)),max(1,min(16,c)),min(16,max(1,17-b))]
                texture='#side'
            face={'uv':uv,'texture':texture}
            if direction=='down' and plane==0: face['cullface']='down'
            elements.append({'from':fr,'to':to,'faces':{direction:face}})
    return elements


# --- Fluff -----------------------------------------------------------------
# Informed by Fluffy Carpets (bebebea_loste): small 2x2 wool patches lifted
# about 0.25 px from the surface, and soft carpet edges. Nothing is copied.
# Patches here are closed boxes rather than floating planes, placed by a seeded
# layout instead of a checkerboard, and each of the four fixed alternatives has
# its own layout. Positions are on the quarter-pixel grid and are rejected if
# any face would share a plane with another face.
LIFT=0.25        # tuft height above a tread
DROOP=0.5        # how far a riser-edge tuft hangs below its nose
LIP=0.5          # how far a riser-edge tuft leans out over the drop
Q=4              # quarter-pixel raster used for coplanarity checks


def heightmap(high):
    return {(x,z):(9 if x==-1 else raised(high,x,z)) for x in range(-1,16) for z in range(16)}


def box_faces(fr,to,omit=()):
    """Faces of a box with native-density UVs taken from the same wool region."""
    faces={}
    for direction in DIRECTIONS:
        if direction in omit:continue
        if direction in ('up','down'):u,v=(fr[0],to[0]),(fr[2],to[2]);texture='#top' if direction=='up' else '#bottom'
        else:
            u=(fr[0],to[0]) if direction in ('north','south') else (fr[2],to[2])
            v=(17-to[1],17-fr[1]);texture='#side'
        def fit(a,b):
            shift=max(0,-a)-max(0,b-16)
            return a+shift,b+shift
        (u0,u1),(v0,v1)=fit(*u),fit(*v)
        faces[direction]={'uv':[u0,v0,u1,v1],'texture':texture}
    return {'from':list(fr),'to':list(to),'faces':faces}


def face_cells(element):
    """Quarter-pixel cells covered by each face, keyed by axis and plane."""
    cells=set()
    fr,to=element['from'],element['to']
    for direction in element['faces']:
        delta=DIRECTIONS[direction];axis=next(i for i,v in enumerate(delta) if v)
        plane=round((to if delta[axis]>0 else fr)[axis]*Q)
        a,b=[i for i in range(3) if i!=axis]
        for i in range(round(fr[a]*Q),round(to[a]*Q)):
            for j in range(round(fr[b]*Q),round(to[b]*Q)):cells.add((axis,plane,i,j))
    return cells


def boxes_touch(e,f,gap=0):
    return all(e['from'][i]-gap<f['to'][i] and f['from'][i]-gap<e['to'][i] for i in range(3))


def fluff(suffix,variant):
    """Seeded tufts for one stair shape and alternative (deterministic)."""
    high=SHAPES[suffix];h=heightmap(high);rng=random.Random(f'wool-fluff{suffix}-{variant}')
    used=set().union(*(face_cells(e) for e in surface(volume(high))))
    tufts=[]
    def accept(element):
        cells=face_cells(element)
        if cells&used or any(boxes_touch(element,t,1) for t in tufts):return False
        used.update(cells);tufts.append(element);return True
    # Riser and front edges: a soft, slightly irregular nose. Interior risers
    # lean out over the drop; the front lip stays within the block profile.
    edges=defaultdict(list)
    for (x,z),top in h.items():
        for dx,dz in ((-1,0),(0,-1),(0,1)):
            n=(x+dx,z+dz)
            if n[0]==-2 or (n in h and h[n]<=top-4):edges[(dx,dz,top,x if dx else z)].append(z if dx else x)
    for (dx,dz,top,line),points in sorted(edges.items()):
        points=sorted(points);runs=[[points[0]]]
        for p in points[1:]:
            if p==runs[-1][-1]+1:runs[-1].append(p)
            else:runs.append([p])
        for run in runs:
            t=run[0]+1+rng.randrange(2)
            while t+2<=run[-1] and t+2<=14:
                length=min(rng.choice((2,2,3)),run[-1]-t,14-t)
                front=line==-1 and dx
                if dx:
                    near=line if dx<0 else line+1
                    out=0 if front else LIP
                    fr=[near-out if dx<0 else near-2,top-(0 if front else DROOP),t];to=[near+2 if dx<0 else near+out,top+LIFT,t+length]
                else:
                    near=line if dz<0 else line+1
                    fr=[t,top-DROOP,near-LIP if dz<0 else near-2];to=[t+length,top+LIFT,near+2 if dz<0 else near+LIP]
                accept(box_faces(fr,to,() if not front else ('down',)))
                t+=length+2+rng.randrange(3)
    # Tread tufts: a few 2x2, 2x1 and 1x2 patches, kept a pixel away from
    # block sides, risers, nose tufts and each other.
    flat=[(x,z) for (x,z),top in h.items() if 0<=x<=13 and 1<=z<=14
          and all(h.get((x+a,z+b),-1)==top for a,b in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)))]
    target=len(tufts)+max(3,len(flat)//22)
    for _ in range(400):
        if len(tufts)>=target:break
        x,z=rng.choice(flat);w,d=rng.choice(((2,2),(2,2),(2,1),(1,2)))
        if not all((x+i,z+j) in flat and h[(x+i,z+j)]==h[(x,z)] for i in range(w) for j in range(d)):continue
        accept(box_faces([x,h[(x,z)],z],[x+w,h[(x,z)]+LIFT,z+d],('down',)))
    return tufts


def stair_elements(suffix,variant):
    return with_variation(surface(volume(SHAPES[suffix]))+fluff(suffix,variant),variant)


def with_variation(elements, variant):
    elements=copy.deepcopy(elements)
    for e in elements:
        for direction,face in e['faces'].items():
            # Rotate UVs only on square full-material faces. Rotating a cropped
            # rectangular UV would stretch fibres along the staircase lips.
            uv=face['uv']
            if variant & 1: uv[0],uv[2]=uv[2],uv[0]
            if variant & 2: uv[1],uv[3]=uv[3],uv[1]
            if abs(uv[2]-uv[0]) == abs(uv[3]-uv[1]) and variant:
                face['rotation']=90 if variant in (1,2) else 180
    return elements


def rot_point(p, turns, vector=False):
    x,y,z=p
    for _ in range(turns): x,z=(-z,x) if vector else (16-z,x)
    return [x,y,z]


def rotate(elements, turns):
    result=copy.deepcopy(elements)
    for e in result:
        a,b=rot_point(e['from'],turns),rot_point(e['to'],turns)
        e['from']=[min(x,y) for x,y in zip(a,b)]
        e['to']=[max(x,y) for x,y in zip(a,b)]
        faces={}
        for direction,face in e['faces'].items():
            vector=rot_point(DIRECTIONS[direction],turns,True)
            name=next(k for k,v in DIRECTIONS.items() if list(v)==vector)
            if 'cullface' in face:face['cullface']=name
            # Baking a Y rotation into the bounds swaps top-face dimensions;
            # rotate its UV corners too, as vanilla's model baker would.
            if direction in ('up','down'):
                face['rotation']=(face.get('rotation',0)+(turns*90 if direction=='up' else -turns*90))%360
            faces[name]=face
        e['faces']=faces
    return result


def match(blocks, props, offset=(0,0,0)):
    return {'type':'match_state','blocks':blocks,'properties':{k:[v] for k,v in props.items()},
            'offset':list(offset),'apply_model_rotation':False}


def main(jar):
    WRITTEN.clear()
    with zipfile.ZipFile(jar) as z:
        stair_states=json.loads(z.read('assets/minecraft/blockstates/white_wool_stairs.json'))
        stair_blocks=sorted('minecraft:'+Path(n).stem for n in z.namelist()
                            if n.startswith('assets/minecraft/blockstates/') and n.endswith('_stairs.json') and '_wool_stairs' not in n)
        cubes={c:json.loads(z.read(f'assets/minecraft/models/block/{c}_wool.json')) for c in COLOURS}
        carpets={c:json.loads(z.read(f'assets/minecraft/models/block/{c}_carpet.json')) for c in COLOURS}
        cube_template=json.loads(z.read('assets/minecraft/models/block/cube.json'))
        carpet_template=json.loads(z.read('assets/minecraft/models/block/carpet.json'))
    default={'particle':'#side',**{k:'minecraft:block/white_wool' for k in ('top','side','bottom')}}
    for suffix,high in SHAPES.items():
        for variant in range(4):
            name='carpeted_wool_stairs'+suffix+('' if variant==0 else f'_v{variant}')
            write(f'assets/realm/models/block/{name}.json',{'parent':'minecraft:block/stairs','textures':default,'elements':stair_elements(suffix,variant)})
            for colour in COLOURS:
                texture='minecraft:block/'+colour+'_wool'
                model_name=colour+'_wool_stairs'+suffix+('' if variant==0 else f'_v{variant}')
                write(f'assets/minecraft/models/block/{model_name}.json',{'parent':'realm:block/'+name,'textures':{k:texture for k in ('top','side','bottom')}})
    for colour in COLOURS:
        # Vanilla weighted model alternatives are deterministic by block position.
        states=copy.deepcopy(stair_states)
        for key,entry in states['variants'].items():
            base=entry['model'].replace('white_wool',''+colour+'_wool')
            states['variants'][key]=[{**entry,'model':base+('' if v==0 else f'_v{v}'),'weight':1} for v in range(4)]
        write(f'assets/minecraft/blockstates/{colour}_wool_stairs.json',states)
        for kind,original,template in (('wool',cubes[colour],cube_template),('carpet',carpets[colour],carpet_template)):
            alternatives=[]
            for variant in range(4):
                # A full cube/carpet face always has square UVs; vary top and
                # side orientations independently without moving block geometry.
                data=copy.deepcopy(template)
                data.update(original)
                data['elements']=copy.deepcopy(template['elements'])
                texture='minecraft:block/'+colour+'_wool'
                data['textures']={**data.get('textures',{}), **({k:texture for k in (*DIRECTIONS,'particle')} if kind=='wool' else {'wool':texture,'particle':texture})}
                for e in data['elements']:
                    for direction,face in e['faces'].items():
                        if kind=='wool' or direction in ('up','down'):
                            face['rotation']=(variant*90+(90 if variant%2 and direction in ('east','west') else 0))%360
                        elif variant & 1:
                            uv=face['uv']; uv[0],uv[2]=uv[2],uv[0]
                identifier=f'realm:block/wool_variation/{colour}_{kind}_{variant}'
                write('assets/realm/models/block/wool_variation/'+f'{colour}_{kind}_{variant}.json',data)
                alternatives.append({'model':identifier,'weight':1})
            write(f'assets/minecraft/blockstates/{colour}_{kind}.json',{'variants':{'':alternatives}})
    # Each appended strip belongs to the wool block, reaches only 1px sideways,
    # and is gated on a dry neighbouring stair with exactly the same state.
    # Its join face is omitted, so no two visible faces share that join plane.
    spill_written=set()
    for colour in COLOURS:
        appends=[]
        for key,entry in stair_states['variants'].items():
            props=dict(p.split('=') for p in key.split(','))
            if props['half']!='bottom':continue
            props['waterlogged']='false'
            suffix='_inner' if 'inner' in props['shape'] else '_outer' if 'outer' in props['shape'] else ''
            high=SHAPES[suffix]
            turns=entry.get('y',0)//90
            for side in (-1,1):
                source_z=0 if side==-1 else 15
                host_z=15 if side==-1 else 0
                cells=set()
                for x in range(-1,16):
                    if x==-1:
                        low,top=0,9
                    elif height(high,x,source_z)!=height(high,x,host_z):continue
                    else:low,top=height(high,x,host_z),raised(high,x,source_z)
                    cells.update((x,y,-1 if side==-1 else 16) for y in range(low,top))
                # Remove every face buried against the supporting stair, not
                # just the side join. In particular, strip undersides must not
                # coincide with the stone treads or its vertical riser.
                host_range=range(-16,0) if side==-1 else range(16,32)
                host={(x,y,z) for x in range(16) for z in host_range
                      for y in range(height(high,x,z+16 if side==-1 else z-16))}
                offset=rot_point((0,0,side),turns,True)
                # Vanilla shares one model and rotation between pairs such as
                # east inner_left and north inner_right, so the spill geometry
                # is identical: write it once, keep the exact state condition.
                toward=next(k for k,v in DIRECTIONS.items() if list(v)==offset)
                name=f'{colour}_{(suffix[1:] or "straight")}_y{turns*90}_{toward}'
                identifier='realm:block/wool_spill/'+name
                if name not in spill_written:
                    els=rotate(surface(cells,blocked=host | volume(high)),turns)
                    texture='minecraft:block/'+colour+'_wool'
                    write(f'assets/realm/models/block/wool_spill/{name}.json',{'parent':'minecraft:block/block','textures':{k:texture for k in ('top','side','bottom','particle')},'elements':els})
                    spill_written.add(name)
                appends.append({'model':identifier,'show_breaking_overlay':True,'conditions':{'type':'and','predicates':[
                    match(['minecraft:'+colour+'_wool_stairs'],props),match(stair_blocks,props,offset)]}})
        write(f'assets/realm/fusion/model_modifiers/blocks/wool_spill_{colour}.json',
              {'targets':[{'block':'minecraft:'+colour+'_wool_stairs','properties':{'half':['bottom'],'waterlogged':['false']}}], 'append_models':appends})
    write('tools/wool-stairs/generated.json',{'source':'Minecraft 26.3 vanilla client assets','paths':sorted(WRITTEN),'spill_width':1,'variation':'Four fixed alternatives (UV orientation and seeded 0.25 px fluff layout), equal weights; original wool textures retained.'})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--client-jar',type=Path,default=Path.home()/'Library/Application Support/ModrinthApp/meta/versions/26.3-0.20.1/26.3-0.20.1.jar')
    main(parser.parse_args().client_jar)
