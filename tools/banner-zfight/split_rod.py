"""Stop neighbouring banner poles z-fighting.

Every pole element (anything above the cloth) is split at x=8. The left half
is inflated by D in y/z, the right half deflated by D. Adjacent banners overlap
left-end-over-right-end, so the faces are never coplanar. Idempotent: elements
already tagged 'rod_l'/'rod_r' are skipped.
usage: python3 split_rod.py path/to/base.json
"""
import json, sys
D, SPLIT = 0.1, 8.0
path = sys.argv[1]
m = json.load(open(path))

def grow(el, d):
    for ax in (1, 2):
        f, t = el['from'][ax], el['to'][ax]
        c = (f + t) / 2
        el['from'][ax] = round(f + (d if f > c else -d), 4)
        el['to'][ax] = round(t + (d if t > c else -d), 4)

def piece(el, x0, x1):
    # x0 replaces 'from' x role, x1 'to' role; interpolate u per face.
    fx, tx = el['from'][0], el['to'][0]
    n = json.loads(json.dumps(el))
    n['from'][0], n['to'][0] = x0, x1
    for side, face in n['faces'].items():
        u1, v1, u2, v2 = face['uv']
        # vanilla: north u runs from 'to' x to 'from' x; up/down/south from 'from' to 'to'
        a, b = (u2, u1) if side == 'north' else (u1, u2)   # u at from, u at to
        u_at = lambda x: round(a + (b - a) * (x - fx) / (tx - fx), 4)
        ua, ub = u_at(x0), u_at(x1)
        face['uv'] = [ub, v1, ua, v2] if side == 'north' else [ua, v1, ub, v2]
    return n

out = []
for el in m['elements']:
    if el.get('name', '').startswith('rod_') or el['to'][1] <= 22 and el['from'][1] <= 22:
        out.append(el); continue
    lo, hi = sorted((el['from'][0], el['to'][0]))
    if hi <= SPLIT or lo >= SPLIT:
        side = 'l' if hi <= SPLIT else 'r'
        n = json.loads(json.dumps(el)); grow(n, D if side == 'l' else -D)
        n['name'] = f"rod_{side} {el.get('name','')}".strip(); out.append(n); continue
    fx, tx = el['from'][0], el['to'][0]
    for x0, x1 in ((fx, SPLIT), (SPLIT, tx)):
        n = piece(el, x0, x1)
        side = 'l' if min(x0, x1) < SPLIT else 'r'
        grow(n, D if side == 'l' else -D)
        n['name'] = f"rod_{side} {el.get('name','')}".strip(); out.append(n)
m['elements'] = out
json.dump(m, open(path, 'w'), indent=2)
print(len(out), 'elements')
