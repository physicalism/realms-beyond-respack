# Resource pack feature index

Navigation audited on 13 November 2026. Paths identify implementation candidates, not proof that every generator reproduces the currently approved artwork. Inspect source and existing output before regeneration; check command-line arguments in each script.

| Feature | Start with |
| --- | --- |
| Art direction and illustrated references | [ARTSTYLE.md](../ARTSTYLE.md), [complete reference catalogue](artstyle/CATALOGUE.md) |
| Build, validation, package contents | [build.py](../tools/build.py) |
| Release process | [release.py](../tools/release.py), [release notes](../tools/release-notes.md) |
| Item catalogue | [catalogue.json](../tools/catalogue.json); verify against current item definitions |
| War banners | [war-banner](../tools/war-banner/) |
| Hanging banners | [hanging-banner](../tools/hanging-banner/) |
| Connected paths and edges | [path-edges README](../tools/path-edges/README.md) |
| Sand shells | [generator and notes](../tools/sand-shells/README.md) |
| Grass decoration | [gen_decor.py](../tools/lawn-decor/gen_decor.py) |
| Lily-pad colour selection | [lily_pad_mix.py](../tools/lily_pad_mix.py) |
| Blacksmith, clocktower, and florist lettering | [rb_sign_caps.py](../tools/clocktower-sign/rb_sign_caps.py); older sign experiments also exist under `tools/blacksmith-sign/` |
| Brass tap | [gen_tap.py](../tools/brass-tap/gen_tap.py) |
| Kitchen props | [gen_kitchen.py](../tools/kitchen-props/gen_kitchen.py) |
| Ivy cake and icon | [generate.py](../tools/ivy-cake/generate.py), [icon.py](../tools/ivy-cake/icon.py) |
| Anvil and handheld hammers | [gen_hammer.py](../tools/anvil-hammer/gen_hammer.py) |
| Sharpening sword | [gen_sword.py](../tools/sharpening-sword/gen_sword.py) |
| Stonecutter saw | [gen_saw.py](../tools/stonecutter-saw/gen_saw.py) |
| Quenching horseshoe | [gen_horseshoe.py](../tools/quenching-horseshoe/gen_horseshoe.py) |

For features absent from this index, search `assets/realm/items/` by item ID, follow the model and texture references, and search `tools/` for the same ID. Vanilla overrides begin under `assets/minecraft/`. Companion cosmetic resources are under `assets/realms_beyond_cosmetics/`; mod logic lives in the sibling `realms-beyond-cosmetics/` project.

## Evidence and ongoing work

Keep accepted decisions, rejected approaches, and remaining visual checks beside the relevant generator, using its existing README where available. Record the date and exact paths. Add a short README only where a feature needs one; avoid duplicating its full history in this index.

Do not populate a task backlog from old chats without checking current source and the user's latest instructions. Describe unverified reports as unverified.
