import sys, os, collections
import sim, scenes
root = sys.argv[1]; out = sys.argv[2]
sim.set_root(root); os.makedirs(out, exist_ok=True)
tot = collections.Counter()
for name, w in scenes.S.items():
    iss, det, imgs, faces = sim.audit(w, scenes.positions(w))
    tot.update(iss)
    print(f'{name:12s} faces={len(faces):5d}', iss)
    agg = collections.Counter((d[1], d[2], d[3], d[4], d[5]) for d in det)
    for k, v in sorted(agg.items())[:12]: print('     ', k, 'views:', v)
    for i, im in enumerate(imgs[:4] + imgs[8:9]):
        sim.save(im, f'{out}/{name}_{i}.png')
print('TOTAL', dict(tot))
