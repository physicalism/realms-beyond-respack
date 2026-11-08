import sys, os, numpy as np
import sim, scenes
from PIL import Image
root, out = sys.argv[1], sys.argv[2]
names = sys.argv[3].split(',') if len(sys.argv) > 3 else list(scenes.S)
sim.set_root(root); os.makedirs(out, exist_ok=True)
def shallow(w):
    ys = sorted({p[1] for p in w})
    return {p: b for p, b in w.items() if p[1] >= -2 or b[0].endswith('void')}
for n in names:
    w = scenes.S[n]
    w2 = sim.World({p: b for p, b in w.items() if p[1] >= -1})
    for p, b in w.items():
        if b[0].endswith('void'): w2[(p[0], -2, p[2])] = b
    faces = sim.collect(w2, list(w2.keys()))
    ims = []
    for yaw, pitch in [(0, 90), (25, 50), (205, 50)]:
        img = sim.render(faces, yaw, pitch, 5)[0][::-1]
        ims.append(img)
    H = max(i.shape[0] for i in ims); Wt = sum(i.shape[1] for i in ims) + 20*(len(ims)-1)
    canvas = np.full((H, Wt, 3), 30.)
    x = 0
    for i in ims:
        canvas[:i.shape[0], x:x+i.shape[1]] = i; x += i.shape[1] + 20
    Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).save(f'{out}/{n}.png')
print('ok')
