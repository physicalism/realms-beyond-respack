"""Original low, stepped rocks inspired by This Rocks!; exposed faces only."""

def rock_elements(x, y, z, w, h, d, texture, u=0, v=0):
    # Broad asymmetric base, smaller offset crown, and an occasional shoulder.
    cells = {(a, b, c) for a in range(w) for b in range(h) for c in range(d)}
    if w >= 5 and d >= 3:
        cells |= {(a, h, c) for a in range(1, w-2)
                  for c in range(1, d-1)}
    if w >= 7:
        cells |= {(a, 0, d) for a in range(2, w-2)}
    elements = []
    # Greedily merge coplanar exposed unit faces; no hidden faces or overlaps.
    for side, axis, sign, aa, bb in [
        ('up',1,1,0,2), ('north',2,-1,0,1), ('south',2,1,0,1),
        ('west',0,-1,2,1), ('east',0,1,2,1)]:
        planes = {}
        for cell in cells:
            neighbour = list(cell); neighbour[axis] += sign
            if tuple(neighbour) in cells:
                continue
            level = cell[axis] + (sign > 0)
            planes.setdefault(level, set()).add((cell[aa], cell[bb]))
        for level, faces in sorted(planes.items()):
            while faces:
                a, b = min(faces)
                width = 1
                while (a+width,b) in faces: width += 1
                height = 1
                while all((a+i,b+height) in faces for i in range(width)): height += 1
                faces.difference_update((a+i,b+j) for i in range(width) for j in range(height))
                lo = [x,y,z]; hi = [x,y,z]
                lo[axis] += level; hi[axis] += level
                lo[aa] += a; hi[aa] += a+width
                lo[bb] += b; hi[bb] += b+height
                elements.append({'from':lo, 'to':hi, 'faces':{side:{
                    'texture':texture, 'uv':[u+a,v+b,u+a+width,v+b+height]}}})
    return elements
