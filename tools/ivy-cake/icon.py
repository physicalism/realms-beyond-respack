"""Draw the flat 16x16 Ivy cake inventory sprite on a transparent background."""
from generate import ROOT, write_png
# Each character is one Minecraft texture pixel; no perspective rendering.
colours = {
 '.':(0,0,0,0),'k':(30,29,28,255),'h':(43,41,38,255),'e':(20,19,18,255),
 'b':(123,80,39,255),'n':(9,10,10,255),'m':(54,48,41,255),
 'g':(28,111,74,255),'t':(204,159,64,255),'r':(183,27,48,255),'R':(242,67,77,255),
 'l':(97,132,41,255),'f':(253,242,209,255),'w':(255,252,236,255),
 'c':(174,99,42,255),'d':(123,65,29,255),'p':(238,159,194,255),
}
rows = [
 '................',
 '................',
 '............l...',
 '....hhhhhhhhRr..',
 '...ekkkkkkkkeR..',
 '..lekkbkkbkke...',
 '.RRekkmmmmkke...',
 '.rRekkmnnmkke...',
 '..p..kkkkkk..p..',
 '.fwfffffffffwf..',
 '.wwwwwwwwwwwww..',
 '.ccwwccccwwccc..',
 '.ccccccccccccc..',
 '.fffffffffffff..',
 '.ccccccccccccc..',
 '..ddddddddddd...',
]
assert len(rows)==16 and all(len(r)==16 for r in rows)
write_png(ROOT/'assets/minecraft/textures/item/cake.png',16,16,[colours[c] for r in rows for c in r])
