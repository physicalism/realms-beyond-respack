# Image sources and refresh instructions

Reference snapshot: 14 November 2026. [Art guide](../../ARTSTYLE.md) · [Complete catalogue](CATALOGUE.md).

## Evidence and provenance

| Files | Source | Evidence / limitations |
| --- | --- | --- |
| `ivy-paintings-current.png`, `painting_ivy*.png` | Current active painting canvas textures, resolved through their item model and parents | Nearest-neighbour enlargements; no new pixels, no frame render, no shader simulation |
| `blacksmith_sign.png`, `blacksmith_hammer.png` | Current model and texture, via `tools/blacksmith-sign/render.py` | Offline software render; approximate lighting, not an in-game screenshot |
| `anvil-hammer-frames.png` | `tools/anvil-hammer/render.py` and current model / texture | Offline frame sheet; stand-in anvil, not captured gameplay |
| `quenching-horseshoe-frames.png` | `tools/quenching-horseshoe/render.py` and current model / texture | Offline frame sheet; stand-in cauldron, not captured gameplay |
| `sharpening-sword-frames.png` | `tools/sharpening-sword/render.py` and current model / texture | Offline multi-view frame sheet; not captured gameplay |
| `kitchen_*_frames.png` | `tools/kitchen-props/render.py` and all three current models / textures | Offline animation sheets on stand-in surroundings; not captured gameplay |
| `origin-realms-blacksmith.png` | Existing workspace `previews/Origin-Realms-Blacksmith-Models.png` | Historical reference board; original capture method/date not established |
| `origin-realms-paintings.png` | Existing workspace `previews/origin-realms-all-paintings.png` | Historical reference board; not evidence of current installed assets |
| `origin-realms-painting-models.png` | Existing workspace `previews/origin-realms-paintings-models.png` | Historical reference board; original capture method/date not established |
| Remote Rokucraft Southern Air Temple image | `https://i.imgur.com/Uxch3uK.jpg`, linked by `https://rokucraft.com/` | Embedded external reference; downloading failed because local DNS could not resolve the host. No local attachment, image inspection, or model-level comparison claimed |

Origin Realms artwork belongs to its respective creators; existing pack attribution remains applicable. Reference inclusion is not evidence of a licence to redistribute a complete third-party pack. No full Origin Realms or Rokucraft source pack has been newly copied into this guide.

## Refresh from current source

Run from the resource-pack root with a Python installation containing Pillow and numpy. These scripts write documentation images only, not live assets:

```sh
python3 tools/artstyle/generate_gallery.py
python3 tools/kitchen-props/render.py . docs/artstyle/images
python3 tools/anvil-hammer/render.py . docs/artstyle/images/anvil-hammer-frames.png
python3 tools/quenching-horseshoe/render.py . docs/artstyle/images/quenching-horseshoe-frames.png
python3 tools/sharpening-sword/render.py . docs/artstyle/images/sharpening-sword-frames.png
```

The gallery script reads current paintings and static blacksmith props; its Origin Realms copy step expects the existing workspace `previews/` directory. Other render scripts use current active assets. After refreshing, inspect the sheets for cropping, overlap, missing textures, and blank frames. Update the catalogue if the item inventory changes.

## Actual screenshots

No fresh in-game screenshots were captured for this guide. Add screenshots from the current pack when available, with the item ID, date, camera/view, shader status, and relevant placement. Keep them distinct from offline renders. Do not rename a render “screenshot” to fill the gap.
