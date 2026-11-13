"""Adapt the original Jellie 16×16 item sprite with Ivy's Labrador face.
Original cake artwork by Hoffen / @_InkGhoul; retain its icing and flowers.
"""
from generate import ROOT, write_png
from png_io import Image
im=Image.open(ROOT/'tools/ivy-cake/source/jellie-item.png')
# Preserve the original face position; replace pointed ears with floppy ears,
# dark fur, brown eyes and a broad Labrador muzzle.
colours={'k':(33,32,30,255),'h':(48,46,42,255),'e':(24,24,23,255),
         'b':(153,107,53,255),'B':(102,66,33,255),'m':(57,51,43,255),
         'n':(10,12,12,255)}
rows=['khhhhk','ekkkke','ebkkbe','ekmmke','kkmnkk','khmmhk']
for y,row in enumerate(rows,3):
 for x,c in enumerate(row,3):im[x,y]=colours[c]
im.save(ROOT/'assets/minecraft/textures/item/cake.png')
scale=24;bg=(56,57,62,255)
pixels=[im[x//scale,y//scale] if im[x//scale,y//scale][3] else bg for y in range(16*scale) for x in range(16*scale)]
write_png(ROOT/'tools/ivy-cake/icon-preview.png',16*scale,16*scale,pixels)
