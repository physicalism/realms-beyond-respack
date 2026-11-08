import sys, numpy as np, sim, scenes
def classify(root, name, lvl=None):
    sim.set_root(root)
    w = scenes.S[name]
    xs = [p[0] for p in w]; zs = [p[2] for p in w]
    x0, x1, z0, z1 = min(xs), max(xs)+1, min(zs), max(zs)+1
    h, c = sim.topdown(w, list(w.keys()), x0, z0, x1, z1)
    # class: 1 lawn-ish (top >= level+1 surface ~16), 0 path (15), -1 other
    cls = np.full(h.shape, -1)
    for z in range(h.shape[0]):
        for x in range(h.shape[1]):
            t = c[z, x]; frac = h[z, x] - np.floor(h[z, x] + 1e-6)
            if 'grass' in t: cls[z, x] = 1
            elif 'path_top' in t: cls[z, x] = 0
    return cls
def issues(cls):
    H, W = cls.shape; out = []
    for z in range(1, H-1):
        for x in range(1, W-1):
            v = cls[z, x]
            if v < 0: continue
            n = [cls[z-1, x], cls[z+1, x], cls[z, x-1], cls[z, x+1]]
            if any(k < 0 for k in n): continue
            diff = sum(k != v for k in n)
            if diff >= 3: out.append(('isolated' if diff == 4 else 'tip', x, z, 'lawn' if v else 'path'))
            elif (n[0] != v and n[1] != v) or (n[2] != v and n[3] != v): out.append(('thin', x, z, 'lawn' if v else 'path'))
    return out
if __name__ == '__main__':
    tot = {}
    for root in sys.argv[1:]:
        tot[root] = 0
        for name in scenes.S:
            iss = issues(classify(root, name))
            tot[root] += len(iss)
            print(f'{root:5s} {name:12s} {len(iss):3d}', iss[:6])
    print(tot)
