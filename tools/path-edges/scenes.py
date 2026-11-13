from sim import World, B

def build(rows, heights=None, extra=None, base=0, depth=-4):
    """rows: list of strings (z = row, x = col). chars:
    G grass, P path, F farmland(+wheat), D dirt, C coarse dirt, R gravel, S stone,
    '.' no surface block (column lowered: top is dirt at level-1),
    n/e/s/w oak stairs facing that way (surface block replaced by stairs)
    heights: optional same-shape list of strings of digits = level offset added.
    extra: dict (x,y,z)->block for things above the surface (fences, torches)."""
    w = World()
    for z, row in enumerate(rows):
        for x, ch in enumerate(row):
            h = base + (int(heights[z][x]) if heights else 0)
            if ch == '.':
                top = h - 1
                w[(x, top, z)] = B('grass_block')
            else:
                top = h
                m = {'G': B('grass_block'), 'P': B('dirt_path'), 'F': B('farmland', moisture=7), 'f': B('farmland', moisture=0), 'D': B('dirt'),
                     'C': B('coarse_dirt'), 'r': B('rooted_dirt'), 'z': B('podzol'), 'R': B('gravel'), 'S': B('stone')}
                if ch in m: w[(x, top, z)] = m[ch]
                elif ch == 'l':
                    w[(x, top, z)] = B('oak_slab', type='bottom')
                elif ch in 'nesw':
                    w[(x, top, z)] = B('oak_stairs', facing={'n': 'north', 'e': 'east', 's': 'south', 'w': 'west'}[ch], half='bottom')
                if ch in 'Ff': w[(x, top+1, z)] = B('wheat')
            for y in range(depth, top):
                w[(x, y, z)] = B('dirt')
            w[(x, depth-1, z)] = B('void')
    for p, b in (extra or {}).items():
        w[p] = b
    return w

def positions(w):
    return list(w.keys())

S = {}
S['straight'] = build(["GGPGG", "GGPGG", "GGPGG", "GGPGG", "GGPGG"])
S['turn'] = build(["GGGGG", "GGGGG", "GGPPP", "GGPGG", "GGPGG"])
S['tee'] = build(["GGGGG", "GGGGG", "PPPPP", "GGPGG", "GGPGG"])
S['cross'] = build(["GGPGG", "GGPGG", "PPPPP", "GGPGG", "GGPGG"])
S['deadend'] = build(["GGGGG", "GGGGG", "GGPGG", "GGPGG", "GGPGG"])
S['single'] = build(["GGGGG", "GGGGG", "GGPGG", "GGGGG", "GGGGG"])
S['diagonal'] = build(["PGGGGG", "PPGGGG", "GPPGGG", "GGPPGG", "GGGPPG", "GGGGPP"])
S['wide'] = build(["GGGGGG", "GGPPGG", "GGPPGG", "GGPPPP", "GGPPPP", "GGGGGG"])
S['plaza'] = build(["GGGGGG", "GPPPPG", "GPPPPG", "GPPPPG", "GPPPPG", "GGGGGG"])
S['ledge'] = build(["GGPGG", "GGPGG", "GGPGG", ".....", "....."], heights=["11111", "11111", "11111", "11111", "11111"])
S['ledge_side'] = build(["GPPPG", "GPPPG", "GGGGG"], heights=["111", "111", "111"] and ["11111", "11111", "00000"])
S['landing'] = build(["GGPPPGG", "GGPPPGG", "GGGPGGG", "..nPn..", "PPPPPPP"],
                     heights=["2222222", "2222222", "2222222", "1111111", "1111111"])
S['fence'] = build(["GGGGG", "GGGGG", "PPPPP", "GGGGG", "GGGGG"],
                   extra={(x, 1, 1): B('oak_fence') for x in range(5)} | {(2, 1, 3): B('torch')})
S['crops'] = build(["GGPGG", "GGPGG", "FFPFF", "FFPFF", "GGPGG"], heights=["11111", "11111", "00100", "00100", "11111"])
S['crops_level'] = build(["GGPGG", "FFPFF", "FFPFF", "GGPGG"])
S['dirtedge'] = build(["GGPGG", "DDPCC", "GGPGG", "RRPGG"])

import random as _r
_rr = _r.Random(5)
def planted(w, frac=0.6):
    w = World(w)
    for (x, y, z), b in list(w.items()):
        if b[0] == 'minecraft:grass_block' and (x, y + 1, z) not in w and _rr.random() < frac:
            w[(x, y + 1, z)] = B(_rr.choice(['short_grass', 'tall_grass', 'poppy', 'short_grass']))
    return w
S['long_planted'] = planted(build(["GGGGGGGGGG", "PPPPPPPPPP", "PPPPPPPPPP", "GGGGGGGGGG", "GGGGGGGGGG"]))
S['long_bare'] = build(["GGGGGGGGGG", "PPPPPPPPPP", "PPPPPPPPPP", "GGGGGGGGGG"])

_rr2 = _r.Random(11)
def forest():
    rows = ["GGGGGGGGGGGG",
            "GGGGGPPPGGGG",
            "GGGGPPPPGGGG",
            "GGGGPPPGGGGG",
            "GGGPPPPGGGGG",
            "GGGPPPGGGGGG",
            "GGPPPPGGGGGG",
            "GGPPPGGGGGGG",
            "GGGPPPGGGGGG",
            "GGGGPPPGGGGG",
            "GGGGPPPPGGGG",
            "GGGGGPPPGGGG"]
    w = build(rows)
    for (x, y, z), b in list(w.items()):
        if b[0] == 'minecraft:grass_block' and y == 0 and _rr2.random() < 0.55:
            w[(x, 1, z)] = B(_rr2.choice(['short_grass', 'tall_grass', 'short_grass', 'poppy', 'fern']))
    return w
S['forest'] = forest()

# glitch repros from Henry's screenshots: path running past a wooden slab, and past a drop into a crop pit
S['slab_side'] = build(["GllGG", "GPPPG", "GPPPG", "GGGGG"])
S['crop_pit'] = build(["GG..GG", "GPPPPG", "GPPPPG", "GGGGGG"], heights=["110011", "111111", "111111", "111111"])
S['crop_pit2'] = build(["GFFFFG", "GPPPPG", "GGPPGG", "GGGGGG"], heights=["100001", "111111", "111111", "111111"])

# farmland merges with the lawn the same way as paths
S['farm_plot'] = build(["GGGGGG", "GFFFFG", "GFFFFG", "GFFFFG", "GGGGGG"])
S['farm_dry'] = build(["GGGGG", "GfffG", "GfFfG", "GGGGG"])
S['farm_path'] = build(["GGGGGG", "GFFPFf", "GFFPFf", "PPPPGG", "GGfGGG"])
S['farm_single'] = build(["GGGGG", "GGFGG", "GGGGf", "GGGGG"])
S['farm_ledge'] = build(["GFFG", "GFFG", "...."], heights=["1111", "1111", "1111"])
S['seam_strip'] = build(["FFFFFF", "PPPPPP", "ffFFff", "GGGGGG"])
S['seam_mix'] = build(["GGGGGG", "GFFPFG", "GFPPFG", "GPPFFG", "GFFPPG", "GGDGGG"])
S['seam_single'] = build(["FFFFF", "FFPFF", "FFFFF", "PPPPP", "PPFPP", "PPPPP"])

# every dirt variant merges with paths exactly like grass (2026-11-12)
S['dirt_path'] = build(["DDPDD", "DDPDD", "DDPPP", "DDPDD", "DDPDD"])
S['dirt_mix'] = build(["GGPDD", "GDPCC", "rrPPz", "zzPGG", "GGPFF"])
S['dirt_single'] = build(["CCCCC", "CCPCC", "CCCCC"])
S['dirt_planted'] = build(["DDDDD", "PPPPP", "DDDDD"], extra={(1, 1, 0): B('short_grass'), (3, 1, 2): B('poppy')})
