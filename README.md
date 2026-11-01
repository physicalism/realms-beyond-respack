# Realms Beyond

A custom resource pack for Minecraft Java 26.3.

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
