# Realms Beyond

A custom resource pack for Minecraft Java 26.3.

For all visible asset work, read the [illustrated art style guide](ARTSTYLE.md) and its [complete primary reference catalogue](docs/artstyle/CATALOGUE.md).

## Disc 13 music

Disc 13 plays 178 seconds of the Legend of Korra ending from https://www.youtube.com/watch?v=_zOmj9I2zzA. The item is named Korra Record, with The Legend of Korra - End Credits as its description and the original disc 13 texture. English (UK and US) translations are included. The music repeats for the full vanilla disc duration of 2 minutes 58 seconds and fades out over the final 1.5 seconds. Reload resources with F3 + T, then eject and reinsert the disc to hear the change.

Audio override: `assets/minecraft/sounds/records/13.ogg` (Ogg Vorbis). Music is from The Legend of Korra; inclusion does not grant redistribution rights.

96 decorative banners: lion, dragon, and stag, each in all 16 dye colours with gold or brown detailing. All banner textures are 64 × 64.

## Use

Enable the pack and place the custom items in invisible wall-mounted item frames. No CIT mod is required.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:banner_lion_red_gold"]
/give @s minecraft:paper[minecraft:item_model="realm:banner_dragon_yellow_brown"]
/give @s minecraft:paper[minecraft:item_model="realm:banner_stag_green_gold"]
```

Item IDs use `realm:banner_SYMBOL_COLOUR_TRIM`, where trim is `gold` or `brown`. Colours with two words use underscores, such as `light_blue`. Older item IDs remain supported for existing banners.

## Stag war banner

A long, animated deep-azure war banner with the town's original stag (at 2×, outlined), a crown and a fleur-de-lis: about 1.9 blocks wide and 5 tall, hanging from a spruce-coloured pole with gold finials. The cloth ripples and gently sways, and the fringed tails trail behind (32 frames, 3.2 s loop). Place it in an invisible item frame on the wall block directly under the beam you want it to hang from: the pole (stripped-spruce coloured) tucks in along the top of the frame's block, just under the beam and flat against the wall, and the banner lies flat on the wall below it.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:banner_stag_war_azure"]
```

Generator: `tools/war-banner/rb_war_banner.py <out_dir>` (stag sprite in `stag.txt`, preview in `preview.gif`).

### All 16 dye colours

The same banner in every Minecraft dye colour (the field is the plain dye colour, as on the royal banners): `realm:banner_stag_war_<dye>`, e.g. `banner_stag_war_blue`. Emblems stay gold, except on yellow and lime, where they use the royal banners' browns so they stay readable. The azure original is unchanged.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:banner_stag_war_blue"]
```

Generator: `tools/war-banner/rb_war_banner_dyes.py <pack_root> [preview_dir]` (reuses `rb_war_banner.py`).

## Hanging stag banner

A small animated stag banner (about 1 block wide, 2.2 tall) in all 16 dye colours: `realm:banner_stag_hanging_<dye>`. Its pole runs straight out from the end of a bottom-half trapdoor, flush with the trapdoor, and ends in a gold spike shaped like the Blacksmith sign's bracket; the banner hangs in the next block along, visible from both sides. Same stag, golds and sway as the war banner.

Stand on the trapdoor and run the command for the direction the pole should point (swap `orange` for any dye):

```mcfunction
# west
/execute align xyz run summon item_display ~-0.5 ~-0.75 ~0.5 {Tags:["rb_hanging_banner"],Rotation:[0f,0f],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:banner_stag_hanging_orange"}}}
# north
/execute align xyz run summon item_display ~0.5 ~-0.75 ~-0.5 {Tags:["rb_hanging_banner"],Rotation:[90f,0f],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:banner_stag_hanging_orange"}}}
# east
/execute align xyz run summon item_display ~1.5 ~-0.75 ~0.5 {Tags:["rb_hanging_banner"],Rotation:[180f,0f],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:banner_stag_hanging_orange"}}}
# south
/execute align xyz run summon item_display ~0.5 ~-0.75 ~1.5 {Tags:["rb_hanging_banner"],Rotation:[-90f,0f],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:banner_stag_hanging_orange"}}}
# remove the nearest one
/kill @e[type=item_display,tag=rb_hanging_banner,sort=nearest,limit=1,distance=..4]
```

Generator: `tools/hanging-banner/rb_hanging_banner.py <pack_root> [preview_dir]` (stag sprite from `tools/war-banner/stag.txt`).

## Build

```sh
python3 tools/build.py
```

Packages are written to `dist/`. Set the version in `tools/VERSION`. To preview a GitHub draft release, run `python3 tools/release.py --dry-run`; omit `--dry-run` after committing and pushing to create the draft. GitHub releases require the GitHub CLI.

## Credits

Banner model and base texture adapted from Origin Realms.

## Ivy paintings

Four paintings share the Origin Realms wooden frame, with the canvas fitted to its opening so edge pixels remain whole. Place in invisible wall-mounted item frames.

| Item model | Portrait | Canvas |
| --- | --- | --- |
| `realm:painting_ivy` | Original Ivy | 16 × 32 |
| `realm:painting_ivy_crown` | Crown headshot, default coarse style | 16 × 32 |
| `realm:painting_ivy_crown_detailed` | Detailed crown portrait | 32 × 64 |
| `realm:painting_ivy_doublet` | Tudor library portrait, coarse style | 16 × 32 |

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy"]
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_crown"]
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_crown_detailed"]
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_doublet"]
```

The former `_coarse` IDs have been retired; replace items using those IDs with the commands above. Previous painting assets are archived in `tools/painting-archive/pre-selection-v0.1.9.zip` and are excluded from installable builds.

Ivy artwork created from the supplied photographs; painting frame model and textures adapted from Origin Realms.

## Pack menu formatting

The description displays two large dark-purple square bullets, an aqua version, and a gold author line with only `(emotivist)` italicised. Building synchronises the description with `tools/VERSION`. The optional `dist/Realms Beyond.zip` copy uses a plain white menu title. Install either ZIP, not both. Live-linked folder titles come from the link name.

## Balcony flowers

Pink flowers with green trailing leaves, a wooden basket, and a yellow ribbon, adapted from Origin Realms. Uses Henry's corrected item-frame display settings: rotation `[-90, 0, 0]`, translation `[5, -12.25, -14]`, scale `[2, 2, 2]`.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:balcony_flowers"]
```

The old `realm:wall_flowers` item ID remains supported. This placement is tailored to the balcony corner; future centred variants can use their own display settings.

To adjust placement in Blockbench, open `assets/realm/models/item/balcony_flowers.json` and edit Display → Fixed. Its texture is `assets/realm/textures/item/decorations/balcony_flowers.png`.

### Corner variant

`realm:balcony_flowers_corner` duplicates the current balcony flower geometry and display settings, with orange flowers and a yellow ribbon. It has its own model and texture so placement can be edited independently in Blockbench.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:balcony_flowers_corner"]
```

## Lotus lily pads

Ordinary placed lily pads show six equally likely variants: plain leaf, pink, purple, white, pale tropical aqua, and yellow (1/6 each, approximately 16.7%). Aqua and yellow are recoloured from the white Origin Realms lotus. Each also has four equally likely rotations. The plain leaf uses the same lotus pad texture without the flower.

Place normal lily pads on water; no commands, frames, mods, or datapacks are needed. Existing pads also change appearance. Variants depend on block position, so breaking and replacing a pad at the same position does not reroll its appearance. These are probabilities, not a guaranteed equal count in each pond. Lily pad behaviour and collision remain vanilla. Pond models and textures adapted from Origin Realms.

To switch the two experimental colours off without affecting anything else:

```sh
python3 tools/lily_pad_mix.py four
python3 tools/build.py
```

Use `python3 tools/lily_pad_mix.py six` and rebuild to re-enable them. Four-colour mode restores the original 25% probabilities and exact model/rotation ordering. Reload resources after switching.

### First-person lanterns

All ten hanging lantern items use their matching block models in first person, inheriting geometry and textures from the active packs for parity with Not Enough Animations in F5. Both first- and third-person hand contexts use the 3D model because Punchy uses third-person contexts for its first-person hands. Inventory icons and non-hand contexts retain their original item models. First-person positioning is static; NEA swinging physics remain a third-person feature.

### Saint Ivy

A separate 16 × 32 devotional portrait with a gold halo, cream robe, crimson mantle, and sacred-heart motif. Shares the existing wooden painting frame.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_saint"]
```

## Decorative books

A magic book stack with blue and purple covers and parchment pages, plus the closed ancient spellbook. Both are decorative item models for floor-mounted invisible item frames.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:magic_book_stack"]
/give @s minecraft:paper[minecraft:item_model="realm:ancient_spellbook"]
```

Models and textures adapted from Origin Realms.

### Dreamcatcher

Multicoloured-feathered dreamcatcher for ceiling-mounted invisible item frames.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:dreamcatcher"]
```

### Blue Ivy

A front-facing 16 × 32 portrait with ice-blue eyes, a bright blue backdrop, and a sparkling cobalt high-neck outfit. Uses the shared wooden painting frame.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_blue"]
```

### Ivy meme portraits

Three square 2 × 2 paintings with 32 × 32 canvases and a shared solid wooden frame: music with wired earbuds, toy laptop, and Pepsi cup. Item IDs are unchanged from the earlier tall versions.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_music"]
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_laptop"]
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_pepsi"]
```

## Ivy shrines

A seated black Labrador statue of Ivy inside a gold-columned shrine: carved dark-stone plinth with a faceted amethyst set into each face, four gold columns with corbels, and a Japanese-style stepped stone roof with upturned gold eave tips and a gold spire. Ivy wears an emerald collar with a small gold tag and has brown eyes. A carved grey-stone version has emerald eyes and a plain stone collar. Her thick tail drapes over the back of the plinth.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:ivy_shrine"]
/give @s minecraft:paper[minecraft:item_model="realm:ivy_shrine_stone"]
```

Place in invisible floor-mounted item frames. Original models; Ivy is sculpted on a quarter-unit grid with simple flat shading, the shrine architecture at 1 texel per unit.

### Lucky Ivy

A lucky-cat figurine of Ivy, just under a block tall, sitting on a red velvet cushion with gold piping and gold corner tassels. She wears her emerald collar and gold tag, carries her head high on a long neck like the shrine's Ivy, smiles, and beckons with her left paw: it rests up for a second, swings smoothly down to her side and back up. Her eyes are square and black with a sparkle in the same corner of each, and her tail hangs over the back of the cushion, curving round to one side. Two finishes: a gold figurine, and coloured, with her black coat.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:lucky_ivy"]
/give @s minecraft:paper[minecraft:item_model="realm:lucky_ivy_coloured"]
```

Place in invisible floor-mounted item frames. Original model, sculpted on a quarter-unit grid in the shrine's flat shading and slimmer, taller proportions. The wave is a texture animation (`lucky_ivy_paw.png`, `lucky_ivy_coloured_paw.png`): each frame is opaque only on one of seven arm poses. Regenerate with `python3 builds/Lucky-Ivy/Source/lucky_ivy.py <outdir> gold` and `... <outdir> coloured`.

### Incense pot

A gold bowl of sandalwood ash holding two incense sticks with glowing tips and two animated, translucent smoke plumes. Sits at a slight diagonal in its frame; place it on the floor in front of a shrine.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:incense_pot"]
```

## Scarecrow

An Origin Realms scarecrow with a tilted pumpkin head, a straw hat, and a faded rust-red hat band. Place it in an invisible floor-mounted item frame.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:scarecrow",minecraft:item_name="Scarecrow"]
```

Model and textures adapted from Origin Realms.

## Stag fountain

A verdigris bronze stag on a two-tier mossy stone pedestal inside an octagonal stone basin, with four animated water spouts and splash foam. The pool itself is real water, so shaders such as Complementary render it natively. Built from six item display entities. The bronze stag uses the Origin Realms Reindeer Rocker body and Deer Mount antlers.

Build the pool first. Stand on the centre block:

```mcfunction
/fill ~-2 ~-2 ~-2 ~2 ~-2 ~2 minecraft:mossy_stone_bricks
/fill ~-2 ~-1 ~-1 ~2 ~-1 ~1 minecraft:water
/fill ~-1 ~-1 ~-2 ~1 ~-1 ~2 minecraft:water
/setblock ~ ~-1 ~ minecraft:stone_bricks
```

Then summon the pieces from the same block:

```mcfunction
/execute align xyz positioned ~.5 ~ ~.5 run summon item_display ~ ~ ~ {Tags:["rb_fountain"],item:{id:"paper",components:{"item_model":"realm:stag_fountain_pedestal"}}}
/execute align xyz positioned ~.5 ~ ~.5 run summon item_display ~ ~2.5 ~ {Tags:["rb_fountain","rb_fountain_stag"],billboard:"fixed",item_display:"none",Rotation:[-45f,0f],item:{id:"paper",components:{"item_model":"realm:stag_fountain_stag"}}}
/execute align xyz positioned ~.5 ~ ~.5 run summon item_display ~1.46875 ~ ~1.46875 {Tags:["rb_fountain"],item:{id:"paper",components:{"item_model":"realm:stag_fountain_basin_se"}}}
/execute align xyz positioned ~.5 ~ ~.5 run summon item_display ~-1.46875 ~ ~1.46875 {Tags:["rb_fountain"],item:{id:"paper",components:{"item_model":"realm:stag_fountain_basin_sw"}}}
/execute align xyz positioned ~.5 ~ ~.5 run summon item_display ~1.46875 ~ ~-1.46875 {Tags:["rb_fountain"],item:{id:"paper",components:{"item_model":"realm:stag_fountain_basin_ne"}}}
/execute align xyz positioned ~.5 ~ ~.5 run summon item_display ~-1.46875 ~ ~-1.46875 {Tags:["rb_fountain"],item:{id:"paper",components:{"item_model":"realm:stag_fountain_basin_nw"}}}
```

The stag command uses `Rotation:[-45f,0f]` to face south-west. Use a yaw of `180f` for east, `-90f` for south, `0f` for west, or `90f` for north. Stand directly on the centre block at ground level when summoning. If replacing an older stag, remove its display before running the updated command. Remove the whole fountain with `/kill @e[type=item_display,tag=rb_fountain,distance=..5]`. The spout colour is the `value` in `assets/realm/items/stag_fountain_pedestal.json` (default 8368864, #7FB2E0).

## Connected paths

Requires [Fusion](https://modrinth.com/mod/fusion-connected-textures); without it, paths and grass look vanilla. Dirt paths sit one pixel below the surrounding lawn with organic, rounded pixel-art edges, including under fences, gates and torches and at wooden step landings. Edge shapes vary with what grows on each grass block. Collision is unchanged. Generator and checks: `tools/path-edges/` (see its README).

## Grass stones

About 1 in 30 plain grass blocks shows a small stone (stone, andesite or cobblestone), chosen at random by vanilla blockstate variants, so no mod is needed. Grass next to paths has none. Regenerate or change the frequency with `tools/lawn-decor/gen_decor.py` (`GRASS_CHANCE`).

## Cosmetics

`assets/realms_beyond_cosmetics/` holds the petal chainsaw (four frames) and lightning bolt cosmetics. `wardrobe.properties` lists per-player toggles.

## Blacksmith sign

Summon the hanging Blacksmith sign at its wall anchor. Set its yaw for the wall orientation. The lettering is in capitals (`BLACKSMITH`) and full-bright; it sits 1/8 pixel in front of the board so it doesn't flicker at a distance.

```mcfunction
/summon item_display ~ ~ ~ {Tags:["rb_blacksmith_sign"],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:blacksmith_sign"}}}
```

## Clocktower sign

Same bracket, anchor and font as the Blacksmith sign, with a clock emblem and `CLOCKTOWER` in capitals. Summon it the same way. Both signs are generated by `tools/clocktower-sign/rb_sign_caps.py` (the lowercase generator `rb_clocktower_sign.py` and backups in `builds/sign-caps-backups/` are kept).

```mcfunction
/summon item_display ~ ~ ~ {Tags:["rb_clocktower_sign"],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:town_clocktower_sign"}}}
```

The back of the wall post is the entity's position. Keep the entity a hair (0.002 blocks) outside the wall: an item display takes its lighting from the block it stands in, so one placed exactly on the wall face is lit as solid stone and renders black. To snap it to a wall to its east, for example: `/execute as @e[type=item_display,tag=rb_clocktower_sign,limit=1,sort=nearest] at @s align xz positioned ~0.998 ~ ~0.5 run tp @s ~ ~ ~`.

## Florist sign

Same bracket, anchor and font as the other two signs, with a five-petal flower emblem and `FLORIST` in capitals, spaced 4px apart instead of 2, on a 20-unit board (the word is shorter). Place it like the Clocktower sign. Generated by `tools/clocktower-sign/rb_sign_caps.py ... FLORIST flower realm:item/decorations/florist_sign 20 4`.

```mcfunction
/summon item_display ~ ~ ~ {Tags:["rb_florist_sign"],item_display:"none",item:{id:"paper",count:1,components:{"item_model":"realm:florist_sign"}}}
```

## Anvil hammer

An animated blacksmith's hammer that strikes an anvil and throws glowing sparks, one hit every 0.85 seconds. Place an invisible item frame on top of a vanilla anvil and put the item in it; the hammer's face lands on the anvil top. The handle points south by default and each click on the frame turns it 45°.

```mcfunction
/give @s minecraft:item_frame[minecraft:entity_data={id:"minecraft:item_frame",Invisible:1b}]
/give @s minecraft:paper[minecraft:item_model="realm:anvil_hammer",minecraft:item_name="Anvil Hammer"]
```

The swing is a texture animation (`anvil_hammer.png`, six frames): each frame is opaque on only one of three hammer poses, and the sparks are full-bright planes. Regenerate with `python3 tools/anvil-hammer/gen_hammer.py .`; preview with `python3 tools/anvil-hammer/render.py . <out.png>`.

### Blacksmith hammer

The same hammer as a plain item (`realm:blacksmith_hammer`, no animation) to hold or to put in an NPC's hand. It is held by the grip with the head forward, and shows side-on in the inventory and in wall frames.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:blacksmith_hammer",minecraft:item_name="Blacksmith Hammer"]
/item replace entity @n[type=minecraft:mannequin] weapon.mainhand with minecraft:paper[minecraft:item_model="realm:blacksmith_hammer",minecraft:item_name="Blacksmith Hammer"]
```

Generated by the same script as the anvil hammer; the hand placement is the `thirdperson_righthand` display in `build_hand_model()`.

## Sharpening sword

A floating sword that slides back and forth across a stonecutter's saw, sharpening itself in a stream of glowing sparks. Place an invisible item frame on a side of the stonecutter where the saw is seen flat-on (as a half disc) and put the item in it; the sword hovers over the saw with its hilt towards you and the sparks fly to your right. Leave the frame unrotated.

```mcfunction
/give @s minecraft:item_frame[minecraft:entity_data={id:"minecraft:item_frame",Invisible:1b}]
/give @s minecraft:paper[minecraft:item_model="realm:sharpening_sword",minecraft:item_name="Sharpening Sword"]
```

The slide is a texture animation (`sharpening_sword.png`, six frames): each frame is opaque on only one of three sword positions, and the sparks loop seamlessly on two full-bright planes. Regenerate with `python3 tools/sharpening-sword/gen_sword.py .`; preview with `python3 tools/sharpening-sword/render.py . <out.png>`.

### 3D stonecutter saw

Every stonecutter's saw is one pixel thick (the sword's blade width) instead of a flat plane. It is the vanilla model with the vanilla saw texture and animation: the saw's face is extruded, so each tooth has a solid edge and the teeth still move as in vanilla. No textures are added, so a texture pack that changes the saw still works. Regenerate with `python3 tools/stonecutter-saw/gen_saw.py .` (the script's header explains the extrusion). To go back to the flat saw, delete `assets/minecraft/models/block/stonecutter.json` and remove the stonecutter lines from `tools/build.py`.

## Quenching horseshoe

A white-hot horseshoe floats down into a cauldron, hisses in a burst of steam, stays under for about two seconds while it cools to dark iron, lifts out dripping, reheats by itself in the air (red, orange, white) and goes in again, every 3.6 seconds. Place an invisible item frame on top of a full water cauldron and put the item in it. The shoe faces north and south by default; each click on the frame turns it 45°.

```mcfunction
/give @s minecraft:item_frame[minecraft:entity_data={id:"minecraft:item_frame",Invisible:1b}]
/give @s minecraft:paper[minecraft:item_model="realm:quenching_horseshoe",minecraft:item_name="Quenching Horseshoe"]
```

The steam starts at the surface of a full cauldron (`WATER_Y` in the generator; lower it by 3 per missing water level). The dunk is a texture animation (`quenching_horseshoe.png`, twelve frames) over three heights, each with a full-bright hot shoe and a plain cool one. Regenerate with `python3 tools/quenching-horseshoe/gen_horseshoe.py .`; preview with `python3 tools/quenching-horseshoe/render.py . <out.png>`.

## Ivy cake

The full cake decoration layout is rotated 180°: the Labrador topper, fruit, flowers, and icing design all turn together. Ivy is a simple cookie-like head matching the original Jellie topper proportions, with two hanging ears, a shallow muzzle, and painted brown eyes and nose. Four cuboids replace the previous detailed head.

All seven bite states preserve vanilla cake bounds. Toppings are removed from the cut side; Ivy falls into the eaten-away area after the fifth bite, because she now sits on the opposite side. The fallen topper is also a Labrador. Includes candle cakes and a flat 16 × 16 inventory icon.

Cake and original decorations by Hoffen (@_InkGhoul), adapted from the supplied `jellie_cake_26.1.zip`. Ivy adaptation by Henry / Realms Beyond. Integrated for Minecraft Java 26.3.

Generator: `python3 tools/ivy-cake/generate.py`; icon: `python3 tools/ivy-cake/icon.py`. The original model JSONs under `tools/ivy-cake/source/` are retained for repeatable generation and excluded from the installed pack.

## Chef Ivy painting

Chef Ivy is a tall portrait in the existing wooden Ivy painting frame, using a 16 × 32 pixel canvas adapted from the chosen kitchen concept. The other portraits remain available.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:painting_ivy_chef"]
/give @s minecraft:item_frame[minecraft:entity_data={id:"minecraft:item_frame",Invisible:1b,Fixed:1b}]
```

Place the invisible frame on the wall and insert the paper, leaving its rotation unchanged. It uses the same size and anchor as the original Ivy portrait (approximately 2.75 blocks wide and 4.75 blocks tall, extending upwards from the frame). Source concept and cropped canvas are preserved in `builds/chef-ivy/`.

## Sand shells

Small ivory, coral pink, and orange clams appear on approximately 1 in 167 ordinary sand blocks, alongside occasional vanilla-textured pebbles (1 in 222) and very rare starfish (1 in 2000). Uses vanilla weighted models, with no mod required. Applies to all ordinary sand, including deserts and underwater sand; red sand is unchanged. Collision and drops remain vanilla. Reload with F3 + T. Current artwork is awaiting visual approval.

Generator and limitations: `tools/sand-shells/README.md`.

To push and publish a prepared, committed release entirely from Terminal:

```sh
python3 tools/release.py --push --publish
```

Local untracked files under `builds/` are backups and do not block publication; pending source changes still do.
