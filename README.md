# Henry’s Realm Resource Pack

A small Java 26.3 resource pack containing one decorative banner: a gold lion on red cloth, with a softened lower crease. Current version: v0.4.0.

## Use

Enable the pack, then run with command permissions:

```mcfunction
/give @s minecraft:paper[minecraft:item_model="realm:royal_banner_red_lion"]
```

Place the item in an invisible wall-mounted item frame. Every viewer needs the resource pack enabled. No CIT mod or datapack is required. Existing red-lion items retain the same model ID; other experimental variants have been removed.

To get an invisible frame:

```mcfunction
/give @s minecraft:item_frame[minecraft:entity_data={id:"minecraft:item_frame",Invisible:1b}] 1
```

## Build

```sh
python3 scripts/build.py
```

The build script validates JSON and resource references, then writes ../builds/Realm-Resource-Pack-v0.4.0.zip containing only pack.mcmeta and assets/.

## Edit

- Texture: assets/realm/textures/item/royal_banner_red_lion.png
- Geometry and item-frame placement: assets/realm/models/item/royal_banner_red_lion.json
- Item definition and red overlay tint: assets/realm/items/royal_banner_red_lion.json

Reload resources in Minecraft after editing. The texture is 64 × 64 pixels and uses separate base and tinted overlay regions.

## Credits

The model and base texture originate from the user-supplied recovered Origin Realms pack. Changes for this project: namespace, frame display settings, fully red cloth, and a softer lower crease. Original model credit: Made with Blockbench. This project is not affiliated with Origin Realms. No licence or redistribution permission for the borrowed assets has been established; this repository does not grant one.
