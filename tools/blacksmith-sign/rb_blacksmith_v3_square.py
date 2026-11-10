#!/usr/bin/env python3
"""Realms Beyond: Blacksmith sign lettering, v3 (square-cornered), with the anvil outlined.

Redraws the "Blacksmith" glyphs in blacksmith_sign.png and keeps everything
else in the atlas as it was:
  * bright glyphs on the full-bright overlay strip (atlas rows 144-195)
  * the dark outline on the wood board around the letters and the anvil (atlas rows 0-51)
The anvil, the wood grain, the frame, the bracket and the spike are not touched.

Usage: rb_blacksmith_v3.py <in.png> <out.png>
"""
import sys
from collections import Counter
from PIL import Image

BOARD_W, BOARD_H = 80, 52      # board face: uv 0..10 x 0..3.25 on 128x256
OVL_Y = 144                    # overlay strip: uv y 9..12.25
TEXT_TOP = 26                  # ascender top row (board space)
XH_TOP = 30                    # x-height top row
BASE = 39                      # baseline row (last row with ink)
GAP = 2                        # space between letters, in texels
FRAME = 4                      # frame width on each side
GLYPH = (255, 255, 249, 255)   # bright lettering
OUTLINE = (28, 21, 17, 255)    # dark letter outline on the wood
ANVIL = (239, 232, 211, 255)   # left as is

# 14 rows each: rows 0-3 ascender zone, rows 4-13 x-height. '#' = ink.
# Strokes are 2 texels thick and counters are 2 texels wide.
G = {
 'B': [
       "######",
       "######",
       "##..##",
       "##..##",
       "##..##",
       "##..##",
       "#####.",
       "#####.",
       "##..##",
       "##..##",
       "##..##",
       "##..##",
       "######",
       "######"],
 'l': [
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "##.",
       "###",
       "###"],
 'a': [
       "......",
       "......",
       "......",
       "......",
       "######",
       "######",
       "....##",
       "....##",
       "######",
       "######",
       "##..##",
       "##..##",
       "######",
       "######"],
 'c': [
       ".....",
       ".....",
       ".....",
       ".....",
       "#####",
       "#####",
       "##...",
       "##...",
       "##...",
       "##...",
       "##...",
       "##...",
       "#####",
       "#####"],
 'k': [
       "##...",
       "##...",
       "##...",
       "##...",
       "##.##",
       "##.##",
       "##.##",
       "####.",
       "###..",
       "####.",
       "##.##",
       "##.##",
       "##.##",
       "##.##"],
 's': [
       ".....",
       ".....",
       ".....",
       ".....",
       "#####",
       "#####",
       "##...",
       "##...",
       "#####",
       "#####",
       "...##",
       "...##",
       "#####",
       "#####"],
 'm': [
       "..........",
       "..........",
       "..........",
       "..........",
       "####..####",
       "##########",
       "##..##..##",
       "##..##..##",
       "##..##..##",
       "##..##..##",
       "##..##..##",
       "##..##..##",
       "##..##..##",
       "##..##..##"],
 'i': [
       "##",
       "##",
       "..",
       "..",
       "##",
       "##",
       "##",
       "##",
       "##",
       "##",
       "##",
       "##",
       "##",
       "##"],
 't': [
       "....",
       "....",
       ".##.",
       ".##.",
       "####",
       "####",
       ".##.",
       ".##.",
       ".##.",
       ".##.",
       ".##.",
       ".##.",
       ".###",
       ".###"],
 'h': [
       "##....",
       "##....",
       "##....",
       "##....",
       "######",
       "######",
       "##..##",
       "##..##",
       "##..##",
       "##..##",
       "##..##",
       "##..##",
       "##..##",
       "##..##"],
}
WORD = "Blacksmith"
# Per-pair spacing overrides (texels). Empty means a uniform GAP.
KERN = {}


def layout():
    for ch in WORD:
        rows = G[ch]
        assert len(rows) == BASE - TEXT_TOP + 1, ch
        assert len({len(r) for r in rows}) == 1, ch
    widths = [len(G[c][0]) for c in WORD]
    gaps = [KERN.get(WORD[i] + WORD[i + 1], GAP) for i in range(len(WORD) - 1)]
    total = sum(widths) + sum(gaps)
    inner = BOARD_W - 2 * FRAME
    x0 = FRAME + (inner - total) // 2
    ink = set()
    x = x0
    for i, ch in enumerate(WORD):
        for r, row in enumerate(G[ch]):
            for c, v in enumerate(row):
                if v == '#':
                    ink.add((x + c, TEXT_TOP + r))
        x += widths[i] + (gaps[i] if i < len(gaps) else 0)
    return ink, x0, total


def main(src, dst):
    im = Image.open(src).convert('RGBA')
    px = im.load()

    # Old text: overlay pixels in the glyph colour (the anvil is a different colour).
    old = {(x, y - OVL_Y) for y in range(OVL_Y, OVL_Y + BOARD_H) for x in range(BOARD_W)
           if px[x, y] == GLYPH}
    for (x, y) in old:
        px[x, y + OVL_Y] = (0, 0, 0, 0)

    # Wood is painted in 4x4 cells; rebuild each cell under the old outline from
    # the cell's other pixels, so no outline is left behind.
    for by in range(0, BOARD_H, 4):
        for bx in range(0, BOARD_W, 4):
            cell = [(bx + i, by + j) for j in range(4) for i in range(4)]
            if not any(px[p] == OUTLINE for p in cell):
                continue
            rest = Counter(px[p] for p in cell if px[p] != OUTLINE)
            if not rest:
                # Fully covered cell: use the cell to the right on the same row.
                rest = Counter(px[(bx + 4 + i) % BOARD_W, by + j] for j in range(4) for i in range(4))
            fill = rest.most_common(1)[0][0]
            for p in cell:
                if px[p] == OUTLINE:
                    px[p] = fill

    ink, x0, total = layout()
    for (x, y) in ink:
        px[x, y + OVL_Y] = GLYPH
    # Outline: 4-neighbour ring around the glyphs and the anvil emblem on the wood.
    anvil = {(x, y - OVL_Y) for y in range(OVL_Y, OVL_Y + BOARD_H) for x in range(BOARD_W)
             if px[x, y] == ANVIL}
    lit = ink | anvil
    ring = set()
    for (x, y) in lit:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in lit:
                ring.add(q)
    for q in ring:
        assert FRAME <= q[0] < BOARD_W - FRAME, f'outline hits the frame at {q}'
        px[q] = OUTLINE
    im.save(dst)
    print(f'text x {x0}..{x0 + total - 1} ({total} wide), rows {TEXT_TOP}..{BASE}; '
          f'{len(ink)} glyph px, {len(ring)} outline px')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
