# Realms Beyond

A custom resource pack for Minecraft Java 26.3.

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

`realm:balcony_flowers_corner` duplicates the current balcony flower geometry and display settings, with light blue flowers and a yellow ribbon. It has its own model and texture so placement can be edited independently in Blockbench.

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

### Incense pot

A gold bowl of sandalwood ash holding two incense sticks with glowing tips and two animated, translucent smoke plumes. Sits at a slight diagonal in its frame; place it on the floor in front of a shrine.

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:incense_pot"]
```
