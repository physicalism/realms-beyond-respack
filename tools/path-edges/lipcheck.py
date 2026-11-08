import sys, numpy as np, sim, scenes
def lipcheck(root, w, lvl=0):
    sim.set_root(root)
    faces = sim.collect(w, list(w.keys()))
    xs=[p[0] for p in w]; zs=[p[2] for p in w]
    x0,x1,z0,z1=min(xs),max(xs)+1,min(zs),max(zs)+1
    h, c = sim.topdown(w, list(w.keys()), x0, z0, x1, z1)
    # vertical coverage sets: (axis, plane, cell index along, y)
    cov = set()
    for f in faces:
        if f.dir in ('up','down'): continue
        y0 = min(f.o[1], f.o[1]+f.V[1]); y1 = max(f.o[1], f.o[1]+f.V[1])
        if not (y0 <= lvl+15/16+1e-6 and y1 >= lvl+1-1e-6): continue
        if f.dir in ('north','south'):
            z = round(f.o[2]*16); a = f.o[0]*16; b = (f.o[0]+f.U[0])*16
            for t in range(int(round(min(a,b))), int(round(max(a,b)))): cov.add(('z', z, t, f.dir))
        else:
            x = round(f.o[0]*16); a = f.o[2]*16; b = (f.o[2]+f.U[2])*16
            for t in range(int(round(min(a,b))), int(round(max(a,b)))): cov.add(('x', x, t, f.dir))
    miss = []
    H, W = h.shape
    for z in range(H):
        for x in range(W):
            a = h[z,x]
            if abs(a-(lvl+1)) > 1e-6: continue   # lawn texel at 16
            for dx,dz,d in ((1,0,'east'),(-1,0,'west'),(0,1,'south'),(0,-1,'north')):
                nx,nz=x+dx,z+dz
                if not (0<=nx<W and 0<=nz<H): continue
                if abs(h[nz,nx]-(lvl+15/16))>1e-6: continue
                gx, gz = x + x0*16, z + z0*16
                if d=='east': key=('x', gx+1, gz, d)
                elif d=='west': key=('x', gx, gz, d)
                elif d=='south': key=('z', gz+1, gx, d)
                else: key=('z', gz, gx, d)
                if key not in cov: miss.append((gx,gz,d))
    return miss
if __name__=='__main__':
    root=sys.argv[1]
    tot=0
    for n,w in scenes.S.items():
        m=lipcheck(root,w); tot+=len(m)
        if m: print(n, len(m), m[:6])
    print('missing lips', tot)
