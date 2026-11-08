import json, os, shutil, sys, glob
import gen
src, out = sys.argv[1], sys.argv[2]
if os.path.exists(out): shutil.rmtree(out)
shutil.copytree(src, out)
mdir = f'{out}/assets/realm/models/block/path_edge_test'
keep = {'earth_north','earth_east','earth_south','earth_west','gravel_north','gravel_east','gravel_south','gravel_west','grass_sided_dirt_path'}
removed = []
for f in glob.glob(mdir + '/*.json'):
    n = os.path.basename(f)[:-5]
    if n not in keep: os.remove(f); removed.append(n)
gm, pa, stats = gen.build(out)
mods = f'{out}/assets/realm/fusion/model_modifiers/blocks'
json.dump(gm, open(f'{mods}/grass_path_edge_test.json', 'w'))
pm = json.load(open(f'{mods}/path_edge_test.json'))
edge = [a for a in pm['append_models'] if ('earth' in a['model'] or 'gravel' in a['model'])]
for a in edge:
    c = a['conditions']; off = c['offset']
    # only speckle against exposed ground, not against a dirt wall (e.g. under a landing)
    a['conditions'] = {'type': 'and', 'predicates': [c, gen.mb((off[0], off[1] + 1, off[2]), gen.AIRISH)]}
pm['append_models'] = edge + pa
json.dump(pm, open(f'{mods}/path_edge_test.json', 'w'))
print('removed', len(removed), 'tiles/corner', stats, 'grass appends', len(gm['append_models']), 'path appends', len(pm['append_models']))
print('modifier sizes', os.path.getsize(f'{mods}/grass_path_edge_test.json'), os.path.getsize(f'{mods}/path_edge_test.json'))
