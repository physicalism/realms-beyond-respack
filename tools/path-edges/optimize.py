"""Reorder Fusion condition trees for speed without changing what they mean (2026-11-12).

Fusion evaluates and/or predicates left to right and stops early, for every targeted block on every chunk rebuild.
Most grass/dirt blocks are nowhere near a path, so each `and` should start with the child most likely to fail
(and cheapest), each `or` with the child most likely to succeed. Child order is chosen from statistics measured on
sample surroundings (mostly plain fields, some path/farmland layouts): `and` by cost/P(false), `or` by cost/P(true)
(optimal order for independent children). Pure reordering: the result of every condition is unchanged.
"""
import json, random
import sim, scenes
from sim import B, World

def contexts(seed=3, n_plain=240, n_near=60):
    rnd = random.Random(seed)
    kinds = ['grass_block', 'dirt', 'coarse_dirt', 'rooted_dirt', 'podzol']
    plants = [None, None, 'short_grass', 'tall_grass', 'poppy']
    out = []
    def field(rows):
        w = scenes.build(rows, depth=-1)
        for (x, y, z), b in list(w.items()):
            if y == 0 and b[0].split(':')[1] in kinds:
                p = rnd.choice(plants)
                if p: w[(x, 1, z)] = B(p)
        return w
    for i in range(n_plain):          # plain ground, no path or farmland nearby (most of a world)
        w = field([''.join(rnd.choice('GGGGGDCrz') for _ in range(3)) for _ in range(3)])
        out.append((w, (1, 0, 1)))
    for i in range(n_near):           # path / farmland blocks themselves
        rows = [''.join(rnd.choice('GGGDPPFfS') for _ in range(3)) for _ in range(3)]
        rows[1] = rows[1][0] + rnd.choice('PPFf') + rows[1][2]
        out.append((field(rows), (1, 0, 1)))
    for i in range(n_near):           # ground next to paths / farmland
        rows = [''.join(rnd.choice('GGGDPPFf') for _ in range(3)) for _ in range(3)]
        w = field(rows); out.append((w, (1, 0, 1)))
    return out

def flatten(c):
    """and(and(a,b),c) -> and(a,b,c); or likewise; single-child and/or -> the child. Same meaning, fewer nodes."""
    t = c['type']
    if t == 'not': return {'type': 'not', 'predicate': flatten(c['predicate'])}
    if t not in ('and', 'or'): return c
    kids = []
    for k in map(flatten, c['predicates']):
        if k['type'] == t: kids.extend(k['predicates'])
        else: kids.append(k)
    seen, uniq = set(), []
    for k in kids:
        key = json.dumps(k, sort_keys=True)
        if key not in seen: seen.add(key); uniq.append(k)
    return uniq[0] if len(uniq) == 1 else {'type': t, 'predicates': uniq}

# Fusion's match_block walks its block list one by one (seen in Henry's Spark profile: HashMap$KeyIterator under
# MatchBlockBlockStatePredicate.test), so a check costs about as much as its list is long. Common blocks are split
# into a tiny list of their own, checked first: or(match [air], match [rest]) means the same as match [air, rest].
HOT = ['minecraft:air', 'minecraft:grass_block', 'minecraft:dirt', 'minecraft:short_grass', 'minecraft:dirt_path',
       'minecraft:stone', 'minecraft:farmland', 'minecraft:tall_grass']
SPLIT_MIN = 5
def split_hot(c):
    t = c['type']
    if t in ('and', 'or'): return {'type': t, 'predicates': [split_hot(k) for k in c['predicates']]}
    if t == 'not': return {'type': 'not', 'predicate': split_hot(c['predicate'])}
    if t == 'match_block' and len(c['blocks']) >= SPLIT_MIN:
        hot = [b for b in c['blocks'] if b in HOT]
        if hot:
            rest = [b for b in c['blocks'] if b not in HOT]
            parts = [dict(c, blocks=[b]) for b in hot] + [dict(c, blocks=rest)]
            return {'type': 'or', 'predicates': parts}
    return c

def leaf_cost(c):
    """Fusion (MatchBlock/MatchStateBlockStatePredicate.test): blocks are a hashed Set (O(1)), but the offsets are a
    HashSet that is iterated on every test (16-slot table), plus one getBlockState per offset tried."""
    return 4 + len(c.get('offsets', [0]))

def merge_offsets(c):
    """or(match X at a, match X at b, ...) -> match X at offsets [a, b, ...] (one predicate, same meaning)."""
    t = c['type']
    if t == 'not': return {'type': 'not', 'predicate': merge_offsets(c['predicate'])}
    if t not in ('and', 'or'): return c
    kids = [merge_offsets(k) for k in c['predicates']]
    if t == 'or':
        groups, out = {}, []
        for k in kids:
            if k['type'] in ('match_block', 'match_state'):
                key = json.dumps({x: v for x, v in k.items() if x not in ('offset', 'offsets')}, sort_keys=True)
                if key in groups:
                    g = groups[key]
                    g.setdefault('offsets', [g.pop('offset')] if 'offset' in g else [])
                    for o in k.get('offsets', [k.get('offset')]):
                        if o not in g['offsets']: g['offsets'].append(o)
                    continue
                k = dict(k); groups[key] = k
            out.append(k)
        for g in groups.values():
            if 'offsets' in g and len(g['offsets']) == 1: g['offset'] = g.pop('offsets')[0]
        kids = out
    return kids[0] if len(kids) == 1 else {'type': t, 'predicates': kids}

def _stats(c, ctx, memo):
    """returns (mean cost, P(true)) of condition c over contexts, with children reordered in place."""
    t = c['type']
    if t in ('and', 'or'):
        kids = c['predicates']
        st = [_stats(k, ctx, memo) for k in kids]
        if t == 'and':
            key = lambda i: st[i][0] / max(1e-6, 1 - st[i][1])
        else:
            key = lambda i: st[i][0] / max(1e-6, st[i][1])
        order = sorted(range(len(kids)), key=key)
        c['predicates'] = [kids[i] for i in order]
    elif t == 'not':
        _stats(c['predicate'], ctx, memo)
    # measure the (reordered) node directly
    tot = 0; tr = 0
    for w, p in ctx:
        n = [0]
        r = _ev(c, w, p, n)
        tot += n[0]; tr += r
    return tot / len(ctx), tr / len(ctx)

def _ev(c, w, p, n):
    t = c['type']
    n[0] += leaf_cost(c) if t not in ('and', 'or', 'not') else 0.5
    if t == 'and':
        for k in c['predicates']:
            if not _ev(k, w, p, n): return False
        return True
    if t == 'or':
        for k in c['predicates']:
            if _ev(k, w, p, n): return True
        return False
    if t == 'not': return not _ev(c['predicate'], w, p, n)
    return sim.ev(c, w, p)

import re
LOW = ['minecraft:dirt_path', 'minecraft:farmland']
NEI8 = [[dx, 0, dz] for dx in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dz) != (0, 0)]
EMPTY = 'realm:block/path_edge_test/empty'
def gate_lists(m):
    """Lawn tiles of one corner are mutually exclusive, and so are the floors of one corner, and every one of them
    needs a path/farmland among the 8 neighbours. So each such group becomes one first-match list (Fusion submits
    only the first matching entry of a list) headed by an empty model shown when no neighbour is a path/farmland:
    a plain field block then costs one check per group instead of one per tile."""
    groups, rest = {}, []
    for a in m['append_models']:
        r = re.match(r'.*/(lawn|floor)_(nw|ne|sw|se)_\d+', a['model'])
        if r: groups.setdefault(r.group(1) + r.group(2), []).append(a)
        else: rest.append(a)
    gate = {'model': EMPTY, 'show_breaking_overlay': False,
            'conditions': {'type': 'not', 'predicate': {'type': 'match_block', 'offsets': NEI8, 'blocks': LOW,
                                                        'apply_model_rotation': False}}}
    m['append_models'] = [[gate] + g for g in groups.values()] + rest
    return m

def optimize_modifier(m, ctx):
    tg = m['targets']
    cx = [(w, p) for w, p in ctx if any(sim.target_ok(t, w.get(p)) for t in tg)] or ctx
    for key in ('default_model_overrides', 'append_models'):
        for a in [e for x in m.get(key, []) for e in (x if isinstance(x, list) else [x])]:
            if isinstance(a, dict) and 'conditions' in a:
                a['conditions'] = merge_offsets(flatten(a['conditions']))
                _stats(a['conditions'], cx, None)
    return m

def cost(m, ctx):
    tot = 0; k = 0
    for w, p in ctx:
        if not any(sim.target_ok(t, w.get(p)) for t in m['targets']): continue
        k += 1
        for a in m.get('default_model_overrides', []):
            n = [0]; _ev(a['conditions'], w, p, n); tot += n[0]
        for x in m.get('append_models', []):
            for a in (x if isinstance(x, list) else [x]):
                n = [0]; r = _ev(a['conditions'], w, p, n); tot += n[0]
                if r and isinstance(x, list): break
    return tot / max(1, k)
