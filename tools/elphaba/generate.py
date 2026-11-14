#!/usr/bin/env python3
"""Refine the installed v2 designs; emit only the exterior of a quarter-pixel solid.
Standard library only. --check compares generated output without writing assets.
Reference models are immutable provenance, not live models.
"""
import argparse
import copy
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
Q = 4
DIRECTIONS = {'west': (0, -1), 'east': (0, 1), 'down': (1, -1),
              'up': (1, 1), 'north': (2, -1), 'south': (2, 1)}


def solid(kind):
    original = json.loads((HERE / f'{kind}-v2-reference.json').read_text())
    voxels = {}
    materials = []

    def box(lo, hi, faces):
        material = len(materials)
        materials.append(faces)
        a, b = [[round(x * Q) for x in v] for v in (lo, hi)]
        assert all(x < y for x, y in zip(a, b)), (lo, hi)
        for x in range(a[0], b[0]):
            for y in range(a[1], b[1]):
                for z in range(a[2], b[2]):
                    voxels[x, y, z] = material

    source = original['elements']
    if kind == 'broom':
        # Retain v2 shaft path and fork. Replace intersecting rotated boxes with
        # joined, deliberately chunky sections. Grain is face colour, not overlays.
        for e in source[:7]:
            a, b = e['from'], e['to']
            r = e.get('rotation', {})
            angle = math.radians(r.get('angle', 0))
            ox, oy, _ = r.get('origin', [8, 8, 8])
            steps = max(1, math.ceil((b[1] - a[1]) / 2.5))
            for i in range(steps):
                y0 = a[1] + (b[1]-a[1])*i/steps
                y1 = a[1] + (b[1]-a[1])*(i+1)/steps
                cx = (a[0]+b[0])/2
                x = ox + (cx-ox)*math.cos(angle) - ((y0+y1)/2-oy)*math.sin(angle)
                half = (b[0]-a[0])/2
                box([x-half,y0,a[2]], [x+half,y1,b[2]], e['faces'])
        # Connect the three fork roots and retain one integrated knot.
        box([7,23.75,7.25],[9.5,25,8.5], source[0]['faces'])
        box([6.75,10,7],[9,11,9], source[0]['faces'])
        # A solid, oval-ish natural bundle, with staggered ends in all directions.
        # Nine chunky tufts replace 32 crossing reeds and detached tips.
        for ix in range(3):
            for iz in range(3):
                x0, z0 = 5.25 + ix*2, 5.25 + iz*2
                end = -9 + ((ix*2+iz)%3)*0.5
                faces = source[12+(ix*3+iz)%7]['faces']
                inset = .5 if ix != 1 and iz != 1 else .25
                box([x0+inset,end,z0+inset], [x0+2-inset,-5,z0+2-inset], faces)
                box([x0,-5,z0],[x0+2,-1,z0+2],faces)
        box([6,-1,6],[10.5,1.5,10.5],source[15]['faces'])
        # Binding is part of the solid union, never a second surface over reeds.
        for y in (-.75,.5):
            box([5.75,y,5.75],[10.75,y+.5,10.75],source[38]['faces'])
        box([7.5,-.75,5.25],[8.5,.25,6],source[40]['faces'])
        original['credit'] = 'Realms Beyond | refined from installed Elphaba broom v2 | exterior-only solid'
        original['display'].update({
            'gui': {'rotation':[22,-35,40],'translation':[0,-.5,0],'scale':[.48]*3},
            'fixed': {'rotation':[0,-30,40],'translation':[0,0,0],'scale':[.46]*3},
            'ground': {'rotation':[0,0,90],'translation':[0,2.5,0],'scale':[.33]*3},
            'thirdperson_righthand': {'rotation':[12,-35,-8],'translation':[0,-1.5,.5],'scale':[.82]*3},
            'thirdperson_lefthand': {'rotation':[12,35,8],'translation':[0,-1.5,.5],'scale':[.82]*3},
            'firstperson_righthand': {'rotation':[0,-40,-15],'translation':[0,-1.5,0],'scale':[.64]*3},
            'firstperson_lefthand': {'rotation':[0,40,15],'translation':[0,-1.5,0],'scale':[.64]*3},
        })
    else:
        # Preserve the broad asymmetric brim and bent stepped crown. Remove
        # thin floating highlights, glints and layered band patches.
        keep = [e for e in source if e['name'].startswith('brim -') or e['name'] in
                ('crown lower','crown second','crown third','crown fourth','crown fifth',
                 'crown upper bend','crown next','crown tip','asymmetric tip')]
        for e in keep:
            box(e['from'],e['to'],e['faces'])
        # One continuous restrained dark band, fused into the crown.
        box([3,13,3.25],[13,14,13],source[25]['faces'])
        original['credit'] = 'Realms Beyond | refined original Elphaba hat silhouette | exterior-only solid'
        # Original GUI framing clipped the tall crown. Centre its occupied bounds.
        original['display']['gui'].update(translation=[0,-7,0],scale=[.59]*3)
        original['display']['fixed'].update(translation=[0,-7,0],scale=[.58]*3)
        original['display']['ground'].update(translation=[0,-1,0])
    return original, voxels, materials


def mesh(voxels, materials):
    # Surface cells are unique: an occupied voxel contributes a face iff its
    # neighbour is empty. Greedy merging never crosses a material boundary.
    groups = defaultdict(set)
    for p, m in voxels.items():
        for face,(axis,sign) in DIRECTIONS.items():
            neighbour = list(p); neighbour[axis] += sign
            if tuple(neighbour) in voxels:
                continue
            plane = p[axis] + (sign > 0)
            uv = tuple(materials[m][face]['uv'])
            tangents = [i for i in range(3) if i != axis]
            groups[face,plane,uv].add(tuple(p[i] for i in tangents))
    elements=[]
    for (face,plane,uv), cells in sorted(groups.items()):
        axis,sign=DIRECTIONS[face]
        u,v=[i for i in range(3) if i != axis]
        while cells:
            a,b=min(cells); w=1
            while (a+w,b) in cells: w+=1
            h=1
            while all((x,b+h) in cells for x in range(a,a+w)):h+=1
            cells.difference_update((x,y) for x in range(a,a+w) for y in range(b,b+h))
            lo=[0]*3; hi=[0]*3
            lo[axis]=plane-(sign>0); hi[axis]=plane+(sign<0)
            lo[u]=a; hi[u]=a+w;lo[v]=b;hi[v]=b+h
            elements.append({'from':[x/Q for x in lo],'to':[x/Q for x in hi],
                             'faces':{face:{'uv':list(uv),'texture':'#palette'}}})
    return elements


def validate(model, voxels):
    # Independent expansion of emitted rectangles checks duplicate/opposing
    # faces and exact agreement with the occupied solid, including every joint.
    seen=set()
    for e in model['elements']:
        assert 'rotation' not in e
        assert all(-16 <= a < b <= 32 for a,b in zip(e['from'],e['to']))
        for face, data in e['faces'].items():
            axis,sign=DIRECTIONS[face]; u,v=[i for i in range(3) if i != axis]
            lo=[round(x*Q) for x in e['from']];hi=[round(x*Q) for x in e['to']]
            plane=hi[axis] if sign>0 else lo[axis]
            assert all(0 <= x <= 16 for x in data['uv'])
            for x in range(lo[u],hi[u]):
                for y in range(lo[v],hi[v]):
                    key=(axis,plane,x,y)
                    assert key not in seen, ('Duplicate surface',key)
                    seen.add(key)
                    inner=[0]*3;inner[axis]=plane-(sign>0);inner[u]=x;inner[v]=y
                    outer=inner.copy();outer[axis]+=sign
                    assert tuple(inner) in voxels and tuple(outer) not in voxels
    expected=sum(tuple(p[i]+(s if i==a else 0) for i in range(3)) not in voxels
                 for p in voxels for a,s in DIRECTIONS.values())
    assert len(seen)==expected, 'Missing exterior faces'
    pending={next(iter(voxels))};visited=set()
    while pending:
        p=pending.pop();visited.add(p)
        for a,s in DIRECTIONS.values():
            n=tuple(p[i]+(s if i==a else 0) for i in range(3))
            if n in voxels and n not in visited:pending.add(n)
    assert len(visited)==len(voxels), 'Detached geometry'
    return len(seen)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=[]
    for kind in ('broom','hat'):
        model,voxels,materials=solid(kind)
        model['elements']=mesh(voxels,materials)
        count=validate(model,voxels)
        path=ROOT/f'assets/realm/models/item/elphaba_{kind}.json'
        content=json.dumps(model,indent=2)+'\n'
        if args.check: assert path.read_text()==content, f'Stale generated model: {path}'
        outputs.append((path,content))
        print(f'{kind}: {len(model["elements"])} exterior rectangles; {count} unique quarter-pixel faces; connected solid; no duplicate/internal faces')
    if not args.check:
        for path,content in outputs:
            temp=path.with_suffix('.json.tmp');temp.write_text(content);temp.replace(path)

if __name__=='__main__':main()
