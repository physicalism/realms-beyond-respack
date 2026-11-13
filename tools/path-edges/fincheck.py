"""Find 'fins': 1px vertical faces at the lawn level (15..16) with nothing solid behind them."""
import sys, numpy as np, sim, scenes
def fins(root, w):
    sim.set_root(root)
    faces = sim.collect(w, list(w.keys()))
    def solid_behind(f):
        # point just behind the face (opposite to its normal), in the middle of the face, at y=15.5/16
        c = f.o + 0.5 * f.U + 0.5 * f.V - f.n * (0.5 / 16)
        bx, by, bz = int(np.floor(c[0])), int(np.floor(c[1])), int(np.floor(c[2]))
        blk = w.get((bx, by, bz))[0].split(':')[1]
        if blk in ('air', 'wheat', 'short_grass', 'tall_grass', 'poppy', 'fern'): return False
        if blk in ('grass_block', 'dirt', 'coarse_dirt', 'rooted_dirt', 'podzol', 'dirt_path', 'farmland'):
            # sample the surface height at that texel from the up faces of that block
            tx, tz = c[0] * 16, c[2] * 16
            top = -1
            for g in faces:
                if g.dir != 'up' or g.pos != (bx, by, bz): continue
                x0, z0 = g.o[0] * 16, g.o[2] * 16; x1, z1 = x0 + g.U[0] * 16, z0 + g.V[2] * 16
                if min(x0, x1) <= tx < max(x0, x1) and min(z0, z1) <= tz < max(z0, z1):
                    top = max(top, g.o[1] * 16 - by * 16)
            return top >= 15.99
        if blk.endswith('_slab'): return (c[1] - by) * 16 < 8
        if blk.endswith('_stairs'):
            ly = (c[1] - by) * 16; lx = (c[0] - bx) * 16; lz = (c[2] - bz) * 16
            if ly < 8: return True
            f = w.get((bx, by, bz))[1].get('facing', 'north')
            return {'north': lz < 8, 'south': lz >= 8, 'west': lx < 8, 'east': lx >= 8}[f]
        return True
    out = []
    for f in faces:
        if f.dir in ('up', 'down'): continue
        y0 = min(f.o[1], f.o[1] + f.V[1]); y1 = max(f.o[1], f.o[1] + f.V[1])
        if y1 - y0 > 1.5 / 16: continue
        if not solid_behind(f):
            out.append((f.pos, f.dir, f.tag.split('/')[-1]))
    return out
if __name__ == '__main__':
    tot = 0
    for n, w in scenes.S.items():
        r = fins(sys.argv[1], w); tot += len(r)
        if r: print(n, len(r), sorted(set(r))[:8])
    print('fins', tot)
