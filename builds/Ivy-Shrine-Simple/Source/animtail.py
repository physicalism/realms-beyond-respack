"""Turn the five tail-pose models into one model whose tail poses are switched by an animated texture.
Minecraft re-reads local_time only about once a second, so clock-swapped models can't wag quickly;
texture animation advances every game tick. Each frame of <name>_tail.png is opaque only on the faces
of one pose, so the other poses are discarded (alpha 0) and never z-fight."""
import json, sys, pathlib
from PIL import Image
src = pathlib.Path(sys.argv[1]); N = sys.argv[2]; POSES = 5; SEQ = [2, 3, 4, 3, 2, 1, 0, 1]
main = json.loads((src / f'{N}.json').read_text()); dog = Image.open(src / f'{N}_dog.png').convert('RGBA')
DW = dog.width
uniq = {}
for k in range(POSES):
    for e in json.loads((src / f'{N}_tail_{k}.json').read_text())['elements']:
        key = (tuple(e['from']), tuple(e['to']))
        if key not in uniq: uniq[key] = dict(el=e, poses=set())
        uniq[key]['poses'].add(k)
rects = []                                                     # (box, face, x0,y0,x1,y1 in dog px, flipx, flipy)
for key, u in uniq.items():
    for f, fc in u['el']['faces'].items():
        x0, y0, x1, y1 = [round(v * DW / 16) for v in fc['uv']]
        rects.append([u, f, min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), x0 > x1, y0 > y1])
S = 32
while True:                                                     # shelf-pack with a 1px gutter into an S x S frame
    x = y = shelf = 0; ok = True
    for r in sorted(rects, key=lambda r: -(r[5] - r[3])):
        w, h = r[4] - r[2] + 2, r[5] - r[3] + 2
        if x + w > S: x = 0; y += shelf; shelf = 0
        if y + h > S: ok = False; break
        r.append((x + 1, y + 1)); x += w; shelf = max(shelf, h)
    if ok: break
    for r in rects: del r[8:]
    S *= 2
strip = Image.new('RGBA', (S, S * POSES), (0, 0, 0, 0))
for u, f, x0, y0, x1, y1, fx, fy, (px, py) in rects:
    tile = dog.crop((x0, y0, x1, y1)); w, h = tile.size
    bled = Image.new('RGBA', (w + 2, h + 2)); bled.paste(tile.resize((w + 2, h + 2), Image.NEAREST)); bled.paste(tile, (1, 1))
    for k in u['poses']: strip.paste(bled, (px - 1, py - 1 + k * S))
    a, b, c, d = [v * 16 / S for v in (px, py, px + w, py + h)]
    u['el']['faces'][f] = {'uv': [c if fx else a, d if fy else b, a if fx else c, b if fy else d], 'texture': '#tail'}
els = []
for i, u in enumerate(uniq.values()):
    e = dict(u['el']); e['name'] = 'Ivy tail ' + ''.join(e['name'].split()[2:3]) + ' ' + ''.join(map(str, sorted(u['poses'])))
    els.append(e)
main['textures']['tail'] = f'realm:item/decorations/{N}_tail'
main['elements'] += els
out = src / 'anim'; out.mkdir(exist_ok=True)
(out / f'{N}.json').write_text(json.dumps(main, indent=2) + '\n')
strip.save(out / f'{N}_tail.png', optimize=True)
(out / f'{N}_tail.png.mcmeta').write_text(json.dumps({'animation': {'frametime': 1, 'interpolate': False, 'frames': SEQ}}, indent=2) + '\n')
(out / f'{N}_item.json').write_text(json.dumps({'model': {'type': 'minecraft:model', 'model': f'realm:item/decorations/{N}'}}, indent=2) + '\n')
print(N, 'unique tail boxes', len(els), 'frame', S, 'faces', len(rects))
