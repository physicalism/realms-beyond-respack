import sys, random, numpy as np, sim, scenes, gen, pixcheck, lipcheck, fincheck
from sim import World, B
root = sys.argv[1]; N = int(sys.argv[2]); seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
sim.set_root(root)
rnd = random.Random(seed)
bad_cons = bad_px = bad_wt = 0
for it in range(N):
    n = 6
    p = rnd.choice([0.3, 0.45, 0.6])
    rows = []
    for z in range(n):
        r = ''
        for x in range(n):
            u = rnd.random()
            r += rnd.choice('PPFFf') if u < p else ('G' if u < 0.93 else rnd.choice('FSn.'))
        rows.append(r)
    # S -> stone, n -> stairs facing north at same level, '.' -> drop
    w = scenes.build(rows, depth=-2)
    PL = {0: None, 1: 'short_grass', 2: 'tall_grass', 3: 'poppy'}
    klass = {}
    for (x, y, z), b in list(w.items()):
        if y == 0 and b[0] == 'minecraft:grass_block':
            k = rnd.choice([0, 0, 1, 2, 3]); klass[(x, z)] = k
            if PL[k]: w[(x, 1, z)] = B(PL[k])
    cells = {}
    for (x, y, z), b in w.items():
        if y != 0: continue
        nm = b[0]
        if nm in ('minecraft:dirt_path', 'minecraft:farmland'): cells[(x, z)] = 'P'
        elif nm == 'minecraft:grass_block': cells[(x, z)] = 'G'
        elif nm.endswith('_stairs'): cells[(x, z)] = 'S'
        else: cells[(x, z)] = 'N'
    for x in range(n):
        for z in range(n):
            if (x, z) not in cells:
                cells[(x, z)] = 'S' if w.get((x, -1, z))[0].endswith('_stairs') else 'N'
    # 1) consistency: assembled tiles vs global function (interior cells only)
    h, c = sim.topdown(w, list(w.keys()), 0, 0, n, n)
    mism = 0
    for (cx, cz), t in cells.items():
        if t not in 'GP' or not (1 <= cx < n-1 and 1 <= cz < n-1): continue
        for tz in range(16):
            for tx in range(16):
                want = gen.global_height(cells, cx*16+tx, cz*16+tz, klass)
                got = h[cz*16+tz, cx*16+tx]
                if abs(got - want/16.0) > 2e-3: mism += 1
    # 1b) farmland/path seam: paving seen from above vs the seam shape
    rc = {}
    for (x, y, z), b in w.items():
        if y == 0: rc[(x, z)] = {'minecraft:dirt_path': 'P', 'minecraft:farmland': 'F'}.get(b[0], 'N')
    for (cx, cz), t in rc.items():
        if t not in 'PF' or not (1 <= cx < n-1 and 1 <= cz < n-1): continue
        for tz in range(16):
            for tx in range(16):
                X, Z = cx*16+tx, cz*16+tz
                if h[Z, X] > 15.5/16: continue      # covered by raised lawn
                want = gen.seam_kind(rc, X, Z)
                got = 'P' if 'dirt_path' in c[Z, X] else ('F' if 'farmland' in c[Z, X] else '?')
                if got != want: mism += 1
    # 2) stray pixels (interior)
    cls = np.full(h.shape, -1)
    for z in range(h.shape[0]):
        for x in range(h.shape[1]):
            v = gen.global_height(cells, x, z, klass)
            if v is not None: cls[z, x] = 1 if v == 16 else 0
    cls[:16, :] = -1; cls[-16:, :] = -1; cls[:, :16] = -1; cls[:, -16:] = -1
    px = pixcheck.issues(cls)
    # 3) watertight from 8 views
    iss, det, imgs, faces = sim.audit(w, list(w.keys()), views=[(y, p) for p in (25, 55) for y in (20, 110, 200, 290)], scale=3)
    lips = [m for m in lipcheck.lipcheck(root, w) if 16 <= m[0] < (n-1)*16 and 16 <= m[1] < (n-1)*16]
    if lips: print(it, rows, 'missing lips', lips[:4])
    fn = fincheck.fins(root, w)
    if fn: print(it, rows, 'fins', fn[:4]); lips = lips or fn
    if mism: bad_cons += 1
    if px: bad_px += 1
    if iss['void'] or iss['zfight'] or lips: bad_wt += 1
    if mism or px or iss['void'] or iss['zfight']:
        print(it, rows, 'mismatch', mism, 'pixels', px[:4], iss)
print(f'{N} random layouts: consistency fails {bad_cons}, stray-pixel fails {bad_px}, watertight/zfight fails {bad_wt}')
